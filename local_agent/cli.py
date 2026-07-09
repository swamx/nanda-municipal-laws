import argparse
import sys

from .agent import Agent
from .api_client import ApiClient
from .claude_cli import ClaudeCliError
from .config import settings

BANNER = """\
Municipal Law Skill - local agent simulator
Base URL: {base_url}
Type a question in plain English (e.g. "Can I keep backyard chickens in Queens?").
Type 'exit' or 'quit' to leave.
"""


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local chat loop that simulates an autonomous agent using SKILL.md.")
    parser.add_argument(
        "--api-base-url",
        default=settings.api_base_url,
        help=f"Municipal Law Skill base URL (default: {settings.api_base_url})",
    )
    parser.add_argument(
        "--model",
        default=settings.claude_model,
        help="Claude model alias/name to use (default: your Claude Code session's current default)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    print(BANNER.format(base_url=args.api_base_url))

    agent = Agent(api_client=ApiClient(base_url=args.api_base_url), model=args.model)
    try:
        while True:
            try:
                user_prompt = input("you> ").strip()
            except EOFError:
                print()
                break

            if not user_prompt:
                continue
            if user_prompt.lower() in {"exit", "quit"}:
                break

            try:
                answer = agent.ask(user_prompt)
            except ClaudeCliError as exc:
                print(f"\n[claude cli error] {exc}\n")
                continue
            except Exception as exc:  # noqa: BLE001 - a demo REPL should never crash on one bad turn
                print(f"\n[error] {exc}\n")
                continue

            print(f"\nagent> {answer.answer}\n")
            if answer.sources:
                print("sources:")
                for source in answer.sources:
                    score_suffix = f" (score {source.score})" if source.score is not None else ""
                    print(f"  - {source.section}: {source.url}{score_suffix}")
            else:
                print("sources: (none)")
            print(f"\nreasoning: {answer.reasoning}\n")
    finally:
        agent.api_client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
