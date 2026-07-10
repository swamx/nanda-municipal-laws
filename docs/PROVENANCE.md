# Signed provenance

`POST /api/v1/is_action_allowed` and `POST /api/v1/search` responses each carry a `provenance` object: an Ed25519 signature over every other field in the response. It exists so a downstream agent — or another NANDA Town skill composing with this one — can prove *offline* that this service (not a relay, a cache, or a man-in-the-middle) produced a given set of citations, without re-calling the API.

```json
"provenance": {
  "signature": "3a5f...c9",
  "public_key": "b1e0...7d",
  "signed_at": "2026-07-10T15:00:00Z",
  "algorithm": "ed25519"
}
```

## What's signed

The canonical payload is the response body with the `provenance` field itself removed, serialized as compact, sorted-key JSON:

```python
json.dumps(response_without_provenance, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
```

`app/signing.py::canonicalize()` is the reference implementation — reproduce that exact recipe (sorted keys, no whitespace, `default=str` for any non-JSON-native value) or the signature won't verify, since Ed25519 signs the literal bytes, not an abstract notion of "the same data."

## Verifying a response

1. Fetch the current public key: `GET /api/v1/pubkey` → `{"public_key": "<hex>", "algorithm": "ed25519"}`.
2. Take the response you want to verify, drop its `provenance` field, canonicalize the rest per the recipe above.
3. Verify the signature against that canonical byte string with the public key.

```python
import json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

def verify(response_body: dict, public_key_hex: str) -> bool:
    provenance = response_body["provenance"]
    signable = {k: v for k, v in response_body.items() if k != "provenance"}
    canonical = json.dumps(signable, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
    try:
        public_key.verify(bytes.fromhex(provenance["signature"]), canonical)
        return True
    except Exception:
        return False
```

`tests/test_provenance.py` exercises this exact recipe end-to-end, including a tamper-detection case (mutating one field after the fact breaks verification).

## Key stability

The signing key is loaded from `SIGNING_PRIVATE_KEY_SEED_HEX` (32 random bytes, hex-encoded) if set; otherwise a fresh Ed25519 key is generated per process, and a warning is logged. On Vercel's serverless model, an unset seed means the public key can change across cold starts — set the env var (see [DEPLOYMENT.md](./DEPLOYMENT.md)) before relying on a stable key for cross-session verification, e.g.:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
vercel env add SIGNING_PRIVATE_KEY_SEED_HEX production
```

## What this does *not* claim

A valid signature proves *this service, with this key, produced this exact response body* — it does not (and cannot) prove the underlying legal citation is current, complete, or correctly interpreted. It's a provenance/integrity guarantee, not a correctness one; the determinism and citation guarantees described in [SKILL.md](../SKILL.md) are what carry the correctness story.
