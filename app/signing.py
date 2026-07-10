import json
import logging
import os
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.models import Provenance

logger = logging.getLogger("municipal_bylaws_api.signing")

_SEED_ENV_VAR = "SIGNING_PRIVATE_KEY_SEED_HEX"


def _load_or_generate_private_key() -> Ed25519PrivateKey:
    seed_hex = os.environ.get(_SEED_ENV_VAR)
    if seed_hex:
        return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex))
    logger.warning(
        "%s not set - generating an ephemeral Ed25519 signing key for this process. "
        "Signatures will not verify across restarts or serverless cold starts. Set "
        "the env var (32 random bytes, hex-encoded) for a stable public key.",
        _SEED_ENV_VAR,
    )
    return Ed25519PrivateKey.generate()


_PRIVATE_KEY = _load_or_generate_private_key()
_PUBLIC_KEY_HEX = _PRIVATE_KEY.public_key().public_bytes_raw().hex()


def public_key_hex() -> str:
    """The Ed25519 public key (hex, raw 32 bytes) that verifies every signature
    this process produces - also served at GET /api/v1/pubkey."""
    return _PUBLIC_KEY_HEX


def canonicalize(payload: dict) -> bytes:
    """The exact byte string that gets signed/verified: compact, sorted-key JSON.
    Any third party can reproduce this from a response's own fields (everything
    except `provenance` itself) plus this same recipe - see docs/PROVENANCE.md.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sign_payload(payload: dict) -> Provenance:
    signature = _PRIVATE_KEY.sign(canonicalize(payload))
    return Provenance(
        signature=signature.hex(),
        public_key=_PUBLIC_KEY_HEX,
        signed_at=datetime.now(timezone.utc),
        algorithm="ed25519",
    )


def sign_response(response_model, exclude: set[str] = frozenset({"provenance"})) -> Provenance:
    """Signs every field of `response_model` except `provenance` itself (which
    doesn't exist yet at signing time). Callers attach the result via
    `response_model.model_copy(update={"provenance": provenance})`.
    """
    payload = response_model.model_dump(mode="json", exclude=exclude)
    return sign_payload(payload)
