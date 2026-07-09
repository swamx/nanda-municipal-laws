import builtins

from local_agent import cli
from local_agent.models import AgentAnswer, SourceCitation


def test_parse_args_defaults_to_settings(monkeypatch):
    args = cli._parse_args([])

    assert args.api_base_url == cli.settings.api_base_url
    assert args.model == cli.settings.claude_model


def test_parse_args_overrides():
    args = cli._parse_args(["--api-base-url", "http://example.test", "--model", "opus"])

    assert args.api_base_url == "http://example.test"
    assert args.model == "opus"


class _FakeApiClient:
    def close(self):
        self.closed = True


class _FakeAgent:
    """Stands in for local_agent.agent.Agent - avoids any real Claude CLI or
    HTTP call in this REPL-wiring test.
    """

    def __init__(self, *args, **kwargs):
        self.api_client = _FakeApiClient()

    def ask(self, prompt: str) -> AgentAnswer:
        return AgentAnswer(
            answer=f"echo: {prompt}",
            sources=[SourceCitation(section="161.19", url="https://example.com", score=1.0)],
            reasoning="fake reasoning",
        )


def test_main_prints_answer_and_exits_cleanly(monkeypatch, capsys):
    monkeypatch.setattr(cli, "Agent", _FakeAgent)

    scripted_inputs = iter(["Can I keep chickens?", "exit"])
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(scripted_inputs))

    exit_code = cli.main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "echo: Can I keep chickens?" in captured.out
    assert "161.19" in captured.out


def test_main_handles_eof_as_exit(monkeypatch, capsys):
    monkeypatch.setattr(cli, "Agent", _FakeAgent)

    def _raise_eof(prompt=""):
        raise EOFError

    monkeypatch.setattr(builtins, "input", _raise_eof)

    exit_code = cli.main([])

    assert exit_code == 0
