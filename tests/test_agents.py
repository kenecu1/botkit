import json
import os
import subprocess
from pathlib import Path

import pytest

from botkit.agents import UsageLimitError, build, review
from botkit.shapes import AgentResult, Finding, Review

FIXTURES = Path(__file__).parent / "fixtures"
SECRET_VARS = ["SSH_AUTH_SOCK", "GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS", "ANTHROPIC_API_KEY"]


class FakeRunner:
    """Stands in for the real runner. Never starts a process."""

    def __init__(self, exit_code=0, stdout="", raises=None, review_json=None):
        self.exit_code = exit_code
        self.stdout = stdout
        self.raises = raises
        self.review_json = review_json
        self.calls = []

    def __call__(self, args, *, stdin, cwd, env, timeout):
        self.calls.append(
            {"args": list(args), "stdin": stdin, "cwd": cwd, "env": env, "timeout": timeout}
        )
        if self.review_json is not None:
            # codex writes the final answer to the -o path itself
            out_file = args[args.index("-o") + 1]
            Path(out_file).write_text(json.dumps(self.review_json), encoding="utf-8")
        if self.raises is not None:
            raise self.raises
        return self.exit_code, self.stdout


def claude_stdout():
    """The real probe output, with numbers no real run would give."""
    data = json.loads((FIXTURES / "claude_ok.json").read_text())
    data["result"] = "Built the parser."
    data["num_turns"] = 17
    data["usage"]["input_tokens"] = 111
    data["usage"]["cache_creation_input_tokens"] = 2222
    data["usage"]["cache_read_input_tokens"] = 33333
    data["usage"]["output_tokens"] = 4444
    data["modelUsage"] = {"claude-opus-5-5-20261101": data["modelUsage"]["claude-opus-5-5"]}
    return json.dumps(data)


def codex_stdout():
    """The real probe stream, with numbers no real run would give."""
    events = [json.loads(line) for line in (FIXTURES / "codex_stream.jsonl").read_text().splitlines()]
    last_message = [e for e in events if e["type"] == "item.completed" and e["item"]["type"] == "agent_message"][-1]
    last_message["item"]["text"] = "Review finished."
    turn = [e for e in events if e["type"] == "turn.completed"][-1]
    turn["usage"]["input_tokens"] = 50505
    turn["usage"]["cached_input_tokens"] = 30303
    turn["usage"]["output_tokens"] = 707
    return "".join(json.dumps(e) + "\n" for e in events)


BUG_A = {
    "file": "src/botkit/a.py", "line_start": 3, "line_end": 4, "severity": "bug",
    "claim": "Empty input crashes.", "evidence": "a('') raises IndexError at line 3.",
}
BUG_B = {
    "file": "src/botkit/b.py", "line_start": 9, "line_end": 9, "severity": "bug",
    "claim": "Off by one.", "evidence": "b(18) returns False, spec says True.",
}
RISK_C = {
    "file": "src/botkit/a.py", "line_start": 20, "line_end": 22, "severity": "risk",
    "claim": "Unclosed file.", "evidence": "open() at line 20 is never closed.",
}
REVIEW_TWO_BUGS = {"summary": "Adds a and b. Two bugs found.", "findings": [BUG_A, BUG_B, RISK_C]}


# Example 1
def test_build_normal_run_returns_agent_result_with_parsed_numbers(tmp_path):
    clone = tmp_path / "clone"
    clone.mkdir()
    out = tmp_path / "run"
    stdout = claude_stdout()
    runner = FakeRunner(exit_code=0, stdout=stdout)

    result = build(
        clone_path=str(clone), prompt="the build prompt", model="claude-opus-5-5",
        timeout=1200, rules_path="/abs/prompts/builder_rules.md", test_cmd="pytest -q",
        out_path=str(out), runner=runner,
    )

    raw_path = os.path.join(str(out), "build_raw.json")
    assert isinstance(result, AgentResult)
    assert result.role == "build"
    assert result.model == "claude-opus-5-5-20261101"
    assert result.final_text == "Built the parser."
    assert result.input_tokens == 111 + 2222 + 33333
    assert result.cached_input_tokens == 33333
    assert result.output_tokens == 4444
    assert result.turns == 17
    assert isinstance(result.seconds, float) and result.seconds >= 0
    assert result.exit_code == 0
    assert result.raw_path == raw_path
    assert Path(raw_path).read_text(encoding="utf-8") == stdout

    assert len(runner.calls) == 1
    call = runner.calls[0]
    assert call["args"][0] == "claude"
    assert call["args"][call["args"].index("--model") + 1] == "claude-opus-5-5"
    assert call["args"][call["args"].index("--append-system-prompt-file") + 1] == "/abs/prompts/builder_rules.md"
    assert call["args"][call["args"].index("--allowedTools") + 1] == "Bash(pytest -q *)"
    assert call["stdin"] == "the build prompt"
    assert call["cwd"] == str(clone)
    assert call["timeout"] == 1200


# Example 2
def test_review_normal_run_returns_agent_result_and_review(tmp_path):
    out = tmp_path / "run"
    stdout = codex_stdout()
    runner = FakeRunner(exit_code=0, stdout=stdout, review_json=REVIEW_TWO_BUGS)

    returned = review(
        prompt="spec, diff and test output", model="gpt-6-luna", timeout=600,
        out_path=str(out), cwd=str(tmp_path), runner=runner,
    )

    assert returned is not None
    result, rev = returned
    raw_path = os.path.join(str(out), "review_raw.jsonl")
    assert isinstance(result, AgentResult)
    assert result.role == "review"
    assert result.model == "gpt-6-luna"
    assert result.final_text == "Review finished."
    assert result.input_tokens == 50505
    assert result.cached_input_tokens == 30303
    assert result.output_tokens == 707
    assert result.turns is None
    assert isinstance(result.seconds, float) and result.seconds >= 0
    assert result.exit_code == 0
    assert result.raw_path == raw_path
    assert Path(raw_path).read_text(encoding="utf-8") == stdout

    assert rev == Review(
        summary="Adds a and b. Two bugs found.",
        findings=(Finding(**BUG_A), Finding(**BUG_B), Finding(**RISK_C)),
        bug_count=2,
    )

    assert len(runner.calls) == 1
    call = runner.calls[0]
    assert call["args"][:2] == ["codex", "exec"]
    assert call["args"][call["args"].index("-m") + 1] == "gpt-6-luna"
    assert call["args"][call["args"].index("-o") + 1] == os.path.join(str(out), "review.json")
    assert call["stdin"] == "spec, diff and test output"
    assert call["cwd"] == str(tmp_path)
    assert call["timeout"] == 600


# Example 3
def test_review_zero_findings_returns_review_with_empty_findings(tmp_path):
    out = tmp_path / "run"
    runner = FakeRunner(
        exit_code=0, stdout=codex_stdout(),
        review_json={"summary": "Small change, nothing wrong.", "findings": []},
    )

    returned = review(
        prompt="p", model="gpt-6-luna", timeout=600,
        out_path=str(out), cwd=str(tmp_path), runner=runner,
    )

    assert returned is not None
    _, rev = returned
    assert rev == Review(summary="Small change, nothing wrong.", findings=(), bug_count=0)


# Example 3
def test_review_crash_returns_none_and_saves_raw_output(tmp_path):
    out = tmp_path / "run"
    stdout = '{"type":"turn.failed","error":{"message":"stream disconnected"}}\n'
    runner = FakeRunner(exit_code=1, stdout=stdout)

    returned = review(
        prompt="p", model="gpt-6-luna", timeout=600,
        out_path=str(out), cwd=str(tmp_path), runner=runner,
    )

    assert returned is None
    assert (out / "review_raw.jsonl").read_text(encoding="utf-8") == stdout


# Example 3
def test_review_timeout_returns_none_without_raising_and_saves_partial_output(tmp_path):
    out = tmp_path / "run"
    runner = FakeRunner(
        raises=subprocess.TimeoutExpired(cmd=["codex"], timeout=600, output='{"type":"turn.started"}\n'),
    )

    returned = review(
        prompt="p", model="gpt-6-luna", timeout=600,
        out_path=str(out), cwd=str(tmp_path), runner=runner,
    )

    assert returned is None
    assert (out / "review_raw.jsonl").read_text(encoding="utf-8") == '{"type":"turn.started"}\n'


# Example 4
def test_build_env_leaves_out_ssh_git_tokens_and_anthropic_key(tmp_path, monkeypatch):
    for name in SECRET_VARS:
        monkeypatch.setenv(name, "secret-" + name)
    monkeypatch.setenv("BOTKIT_KEEP_ME", "kept")
    clone = tmp_path / "clone"
    clone.mkdir()
    runner = FakeRunner(exit_code=0, stdout=claude_stdout())

    build(
        clone_path=str(clone), prompt="p", model="claude-opus-5-5", timeout=1200,
        rules_path="/abs/rules.md", test_cmd="pytest",
        out_path=str(tmp_path / "run"), runner=runner,
    )

    env = runner.calls[0]["env"]
    assert env is not None
    for name in SECRET_VARS:
        assert name not in env
    assert not any(value.startswith("secret-") for value in env.values())
    assert env["BOTKIT_KEEP_ME"] == "kept"
    for name in SECRET_VARS:
        assert os.environ[name] == "secret-" + name


# Example 5
def test_build_timeout_raises_timeout_error_naming_build_and_clone(tmp_path):
    clone = tmp_path / "clone"
    clone.mkdir()
    runner = FakeRunner(raises=subprocess.TimeoutExpired(cmd=["claude"], timeout=1200))

    with pytest.raises(TimeoutError) as caught:
        build(
            clone_path=str(clone), prompt="p", model="claude-opus-5-5", timeout=1200,
            rules_path="/abs/rules.md", test_cmd="pytest",
            out_path=str(tmp_path / "run"), runner=runner,
        )

    message = str(caught.value)
    assert "timed out" in message
    assert "build" in message
    assert str(clone) in message
    assert len(runner.calls) == 1


# Error case from the spec: usage limit during build
def test_build_usage_limit_raises_usage_limit_error(tmp_path):
    clone = tmp_path / "clone"
    clone.mkdir()
    stdout = json.dumps({
        "type": "result", "subtype": "error", "is_error": True,
        "result": "Claude AI usage limit reached", "num_turns": 0,
    })
    runner = FakeRunner(exit_code=1, stdout=stdout)

    with pytest.raises(UsageLimitError) as caught:
        build(
            clone_path=str(clone), prompt="p", model="claude-opus-5-5", timeout=1200,
            rules_path="/abs/rules.md", test_cmd="pytest",
            out_path=str(tmp_path / "run"), runner=runner,
        )

    assert not isinstance(caught.value, TimeoutError)
    message = str(caught.value).lower()
    assert "usage limit" in message
    assert "build" in message
    assert len(runner.calls) == 1


# Error case from the spec: usage limit during review
def test_review_usage_limit_raises_usage_limit_error(tmp_path):
    stdout = '{"type":"error","message":"You\'ve hit your usage limit. Try again later."}\n'
    runner = FakeRunner(exit_code=1, stdout=stdout)

    with pytest.raises(UsageLimitError) as caught:
        review(
            prompt="p", model="gpt-6-luna", timeout=600,
            out_path=str(tmp_path / "run"), cwd=str(tmp_path), runner=runner,
        )

    assert not isinstance(caught.value, TimeoutError)
    message = str(caught.value).lower()
    assert "usage limit" in message
    assert "review" in message
    assert len(runner.calls) == 1
