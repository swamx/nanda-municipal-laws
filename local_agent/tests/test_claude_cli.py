import json
import subprocess

import pytest

from local_agent import claude_cli
from local_agent.claude_cli import ClaudeCliError, ask_structured


class _FakeCompletedProcess:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch_which(monkeypatch, found=True):
    monkeypatch.setattr(claude_cli.shutil, "which", lambda name: "/usr/bin/claude" if found else None)


def test_ask_structured_returns_structured_output_on_success(monkeypatch):
    _patch_which(monkeypatch)
    envelope = {"is_error": False, "structured_output": {"endpoint": "search", "query_or_action": "noise", "reasoning": "x"}}
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _FakeCompletedProcess(0, stdout=json.dumps(envelope))
    )

    result = ask_structured("hello", system_prompt="sys", json_schema={"type": "object"})

    assert result == envelope["structured_output"]


def test_ask_structured_raises_when_claude_binary_missing(monkeypatch):
    _patch_which(monkeypatch, found=False)

    with pytest.raises(ClaudeCliError, match="not found on PATH"):
        ask_structured("hello", system_prompt="sys", json_schema={"type": "object"})


def test_ask_structured_raises_on_nonzero_exit(monkeypatch):
    _patch_which(monkeypatch)
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: _FakeCompletedProcess(1, stdout="", stderr="boom")
    )

    with pytest.raises(ClaudeCliError, match="exited 1"):
        ask_structured("hello", system_prompt="sys", json_schema={"type": "object"})


def test_ask_structured_raises_on_malformed_json(monkeypatch):
    _patch_which(monkeypatch)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeCompletedProcess(0, stdout="not json"))

    with pytest.raises(ClaudeCliError, match="non-JSON output"):
        ask_structured("hello", system_prompt="sys", json_schema={"type": "object"})


def test_ask_structured_raises_when_envelope_reports_error(monkeypatch):
    _patch_which(monkeypatch)
    envelope = {"is_error": True, "result": "something went wrong"}
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeCompletedProcess(0, stdout=json.dumps(envelope)))

    with pytest.raises(ClaudeCliError, match="reported an error"):
        ask_structured("hello", system_prompt="sys", json_schema={"type": "object"})


def test_ask_structured_raises_when_structured_output_missing(monkeypatch):
    _patch_which(monkeypatch)
    envelope = {"is_error": False, "result": "free text, no structured_output"}
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _FakeCompletedProcess(0, stdout=json.dumps(envelope)))

    with pytest.raises(ClaudeCliError, match="did not return structured_output"):
        ask_structured("hello", system_prompt="sys", json_schema={"type": "object"})


def test_ask_structured_raises_on_timeout(monkeypatch):
    _patch_which(monkeypatch)

    def _raise_timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr(subprocess, "run", _raise_timeout)

    with pytest.raises(ClaudeCliError, match="timed out"):
        ask_structured("hello", system_prompt="sys", json_schema={"type": "object"}, timeout=1)


def test_ask_structured_passes_model_flag_when_given(monkeypatch):
    _patch_which(monkeypatch)
    captured_args = {}

    def _fake_run(args, **kwargs):
        captured_args["args"] = args
        return _FakeCompletedProcess(0, stdout=json.dumps({"is_error": False, "structured_output": {}}))

    monkeypatch.setattr(subprocess, "run", _fake_run)

    ask_structured("hello", system_prompt="sys", json_schema={"type": "object"}, model="opus")

    assert "--model" in captured_args["args"]
    assert "opus" in captured_args["args"]


def test_ask_structured_pipes_the_prompt_over_stdin_not_as_a_cli_arg(monkeypatch):
    # Pins a real bug: a long prompt (e.g. agent.py's needs_full_text
    # follow-up embedding a full statute section's text) passed as a CLI
    # argument hit Windows' ~32K command-line length limit
    # ("[WinError 206] The filename or extension is too long"). The prompt
    # must go over stdin instead, regardless of its length.
    _patch_which(monkeypatch)
    captured = {}

    def _fake_run(args, *, input=None, **kwargs):
        captured["args"] = args
        captured["input"] = input
        return _FakeCompletedProcess(0, stdout=json.dumps({"is_error": False, "structured_output": {}}))

    monkeypatch.setattr(subprocess, "run", _fake_run)

    long_prompt = "x" * 100_000
    ask_structured(long_prompt, system_prompt="sys", json_schema={"type": "object"})

    assert captured["input"] == long_prompt
    assert long_prompt not in captured["args"]
