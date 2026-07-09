"""Manual, opt-in end-to-end check: the REAL `claude` CLI (costs a small
amount of real usage, takes real time) talking to a REAL running server
(local dev server by default, or pass --api-base-url for the live Vercel
deployment).

Not part of `pytest`/CI - this is for a human to run deliberately when they
want to sanity-check the whole real chain at once, not something that should
run on every commit. The offline, deterministic equivalent that *does* run
in CI is local_agent/tests/test_agent_integration.py (real API logic, fake
Claude CLI).

Usage:
    uvicorn app.main:app --reload          # in one terminal
    python -m local_agent.smoke_test        # in another

    python -m local_agent.smoke_test --api-base-url https://nanda-municipal-laws.vercel.app
"""

import argparse
import sys

from .agent import Agent
from .api_client import ApiClient
from .claude_cli import ClaudeCliError
from .config import settings

_CASES = [
    ("Keep backyard chickens", "chickens are allowed with a rooster caveat"),
    ("keep a rooster in my apartment", "roosters are explicitly prohibited"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api-base-url", default=settings.api_base_url)
    parser.add_argument("--model", default=settings.claude_model)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    print(f"Live smoke test against {args.api_base_url} using the real claude CLI.")
    print("This makes real Claude Code calls and costs a small amount of real usage.\n")

    agent = Agent(api_client=ApiClient(base_url=args.api_base_url), model=args.model)
    failures = 0
    try:
        for prompt, expectation in _CASES:
            print(f"> {prompt}")
            print(f"  (expect: {expectation})")
            try:
                answer = agent.ask(prompt)
            except ClaudeCliError as exc:
                print(f"  FAILED - claude CLI error: {exc}\n")
                failures += 1
                continue
            except Exception as exc:  # noqa: BLE001
                print(f"  FAILED - {exc}\n")
                failures += 1
                continue

            print(f"  answer: {answer.answer}")
            print(f"  sources: {[s.section for s in answer.sources]}")
            print(f"  reasoning: {answer.reasoning}\n")
    finally:
        agent.api_client.close()

    if failures:
        print(f"{failures}/{len(_CASES)} case(s) failed.")
        return 1

    print("All cases completed without error. Read the printed answers yourself - "
          "this script checks the pipeline runs end to end, it does not assert on "
          "the model's exact wording.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
