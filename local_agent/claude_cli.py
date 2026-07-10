import json
import shutil
import subprocess
from typing import Any


class ClaudeCliError(RuntimeError):
    """Raised for any failure talking to the local `claude` CLI - missing binary,
    non-zero exit, malformed output, or a response that doesn't match the
    requested schema.
    """


def _find_claude_binary() -> str:
    path = shutil.which("claude")
    if not path:
        raise ClaudeCliError(
            "claude CLI not found on PATH. This agent shells out to your existing "
            "Claude Code login instead of requiring a separate ANTHROPIC_API_KEY - "
            "install/log in to Claude Code first (https://claude.com/claude-code)."
        )
    return path


def ask_structured(
    prompt: str,
    *,
    system_prompt: str,
    json_schema: dict[str, Any],
    timeout: float = 90.0,
    model: str | None = None,
) -> dict[str, Any]:
    """Runs one non-interactive Claude Code turn and returns its schema-validated
    structured output as a dict.

    This rides on the caller's existing Claude Code session (`claude -p ...`) -
    no separate ANTHROPIC_API_KEY needed. That's the whole point: this module is
    only ever imported by the local_agent package, which is excluded from the
    Vercel deployment (see .vercelignore) - a deployed server must never shell
    out to a CLI tool like this.
    """
    binary = _find_claude_binary()
    # The prompt is piped over stdin, not passed as a CLI argument: it can
    # embed a full statute section's text (thousands of characters, e.g. via
    # agent.py's needs_full_text follow-up), and Windows' CreateProcess has a
    # hard ~32K total command-line length limit - a real failure observed
    # while building this ("[WinError 206] The filename or extension is too
    # long") once a long section's full text was folded into the prompt.
    # `-p` with no value after it means "read the prompt from stdin".
    args = [
        binary,
        "-p",
        "--output-format",
        "json",
        "--tools",
        "",
        "--system-prompt",
        system_prompt,
        "--json-schema",
        json.dumps(json_schema),
    ]
    if model:
        args += ["--model", model]

    try:
        proc = subprocess.run(
            args,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
    except subprocess.TimeoutExpired as exc:
        raise ClaudeCliError(f"claude CLI timed out after {timeout}s") from exc
    except OSError as exc:
        raise ClaudeCliError(f"failed to launch claude CLI: {exc}") from exc

    if proc.returncode != 0:
        raise ClaudeCliError(f"claude CLI exited {proc.returncode}: {proc.stderr.strip()}")

    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ClaudeCliError(f"claude CLI returned non-JSON output: {proc.stdout[:500]!r}") from exc

    if envelope.get("is_error"):
        raise ClaudeCliError(f"claude CLI reported an error: {envelope.get('result')!r}")

    structured = envelope.get("structured_output")
    if structured is None:
        raise ClaudeCliError(
            "claude CLI did not return structured_output matching the requested schema "
            f"(raw result: {envelope.get('result', '')[:300]!r})"
        )
    return structured
