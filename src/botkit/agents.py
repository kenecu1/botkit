"""Run the builder and reviewer CLIs as subprocesses and turn their output into records."""

import json
import os
import signal
import subprocess
import time

from botkit.shapes import AgentResult, Finding, Review

SECRET_VARS = ("SSH_AUTH_SOCK", "GH_TOKEN", "GITHUB_TOKEN", "GIT_ASKPASS", "ANTHROPIC_API_KEY")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEMA_PATH = os.path.join(REPO_ROOT, "schemas", "review.json")
FINDING_TYPES = {
    "file": str,
    "line_start": int,
    "line_end": int,
    "severity": str,
    "claim": str,
    "evidence": str,
}


class UsageLimitError(Exception):
    """Raised when a CLI reports that the plan's usage limit was reached."""


def default_runner(args: list[str], *, stdin: str, cwd: str | None,
                   env: dict[str, str] | None, timeout: float) -> tuple[int, str]:
    """Run args in a new process group, send stdin, and return (exit_code, stdout)."""
    proc = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        cwd=cwd, env=env, start_new_session=True,
    )
    try:
        stdout, _ = proc.communicate(stdin, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        partial, _ = proc.communicate()
        raise subprocess.TimeoutExpired(args, timeout, output=partial)
    return proc.returncode, stdout


def _write_text(path, text):
    """Write text to path as UTF-8."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _as_int(value):
    """Return value if it is an int (not a bool), otherwise None."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _as_dict(value):
    """Return value if it is a dict, otherwise an empty dict."""
    if isinstance(value, dict):
        return value
    return {}


def _parse_json_object(text):
    """Return text parsed as a JSON object, or an empty dict if it is not one."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return _as_dict(data)


def _has_usage_limit(text):
    """Return True if text mentions a usage limit in any case."""
    return "usage limit" in text.lower()


def _builder_env():
    """Return a copy of os.environ without the secret variables."""
    env = dict(os.environ)
    for name in SECRET_VARS:
        env.pop(name, None)
    return env


def _total_input_tokens(usage):
    """Return plain plus cache-write plus cache-read input tokens, or None if any is missing."""
    parts = [
        _as_int(usage.get("input_tokens")),
        _as_int(usage.get("cache_creation_input_tokens")),
        _as_int(usage.get("cache_read_input_tokens")),
    ]
    if None in parts:
        return None
    return sum(parts)


def _build_model(data, model):
    """Return the one model named in modelUsage, otherwise the given model."""
    model_usage = _as_dict(data.get("modelUsage"))
    if len(model_usage) == 1:
        return list(model_usage)[0]
    return model


def build(clone_path: str, prompt: str, model: str, timeout: float,
          rules_path: str, test_cmd: str, out_path: str,
          runner=default_runner) -> AgentResult:
    """Run the Claude builder in the clone and return its AgentResult."""
    os.makedirs(out_path, exist_ok=True)
    args = [
        "claude", "-p", "--model", model,
        "--permission-mode", "acceptEdits", "--permission-prompts", "none",
        "--allowedTools", f"Bash({test_cmd} *)",
        "--disallowedTools", "Bash(git commit *)", "Bash(git push *)",
        "--append-system-prompt-file", rules_path,
        "--output-format", "json", "--max-turns", "60", "--no-session-persistence",
    ]
    start = time.monotonic()
    try:
        exit_code, stdout = runner(
            args, stdin=prompt, cwd=clone_path, env=_builder_env(), timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise TimeoutError(f"build timed out after {timeout}s in {clone_path}") from error
    seconds = float(time.monotonic() - start)

    raw_path = os.path.join(out_path, "build_raw.json")
    _write_text(raw_path, stdout)

    data = _parse_json_object(stdout)
    failed = exit_code != 0 or data.get("is_error") is True
    if failed and _has_usage_limit(stdout):
        raise UsageLimitError(f"build hit a usage limit (output saved to {raw_path})")

    usage = _as_dict(data.get("usage"))
    final_text = data.get("result")
    if not isinstance(final_text, str):
        final_text = None
    return AgentResult(
        role="build",
        model=_build_model(data, model),
        final_text=final_text,
        input_tokens=_total_input_tokens(usage),
        cached_input_tokens=_as_int(usage.get("cache_read_input_tokens")),
        output_tokens=_as_int(usage.get("output_tokens")),
        turns=_as_int(data.get("num_turns")),
        seconds=seconds,
        exit_code=exit_code,
        raw_path=raw_path,
    )


def _stream_events(text):
    """Return the JSON objects from a JSON-lines stream, skipping lines that are not."""
    events = []
    for line in text.splitlines():
        event = _parse_json_object(line)
        if event:
            events.append(event)
    return events


def _last_agent_message(events):
    """Return the text of the last completed agent_message item, or None."""
    text = None
    for event in events:
        item = _as_dict(event.get("item"))
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            text = item.get("text")
    if isinstance(text, str):
        return text
    return None


def _last_turn_usage(events):
    """Return the usage of the last turn.completed event, or an empty dict."""
    usage = {}
    for event in events:
        if event.get("type") == "turn.completed":
            usage = _as_dict(event.get("usage"))
    return usage


def _severity_enum():
    """Return the allowed finding severities from schemas/review.json."""
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    return schema["properties"]["findings"]["items"]["properties"]["severity"]["enum"]


def _parse_finding(raw, severities):
    """Return a Finding from raw, or None if a field is missing, mistyped or has an unknown severity."""
    if not isinstance(raw, dict):
        return None
    for name, kind in FINDING_TYPES.items():
        value = raw.get(name)
        if not isinstance(value, kind) or isinstance(value, bool):
            return None
    if raw["severity"] not in severities:
        return None
    return Finding(**{name: raw[name] for name in FINDING_TYPES})


def _read_review(path):
    """Return the Review stored at path, or None if it is missing or malformed."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    summary = data.get("summary")
    raw_findings = data.get("findings")
    if not isinstance(summary, str) or not isinstance(raw_findings, list):
        return None
    severities = _severity_enum()
    findings = []
    for raw in raw_findings:
        finding = _parse_finding(raw, severities)
        if finding is None:
            return None
        findings.append(finding)
    bug_count = len([f for f in findings if f.severity == "bug"])
    return Review(summary=summary, findings=tuple(findings), bug_count=bug_count)


def review(prompt: str, model: str, timeout: float, out_path: str, cwd: str,
           runner=default_runner) -> tuple[AgentResult, Review] | None:
    """Run the Codex reviewer and return its AgentResult and Review, or None if unavailable."""
    os.makedirs(out_path, exist_ok=True)
    review_path = os.path.join(out_path, "review.json")
    raw_path = os.path.join(out_path, "review_raw.jsonl")
    args = [
        "codex", "exec", "-m", model, "-s", "read-only", "--ephemeral",
        "--ignore-user-config", "--ignore-rules",
        "--output-schema", SCHEMA_PATH,
        "-o", review_path,
        "--json", "-",
    ]
    start = time.monotonic()
    try:
        exit_code, stdout = runner(args, stdin=prompt, cwd=cwd, env=None, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        _write_text(raw_path, error.output or "")
        return None
    seconds = float(time.monotonic() - start)

    _write_text(raw_path, stdout)
    if exit_code != 0 and _has_usage_limit(stdout):
        raise UsageLimitError(f"review hit a usage limit (output saved to {raw_path})")
    if exit_code != 0:
        return None

    parsed_review = _read_review(review_path)
    if parsed_review is None:
        return None

    events = _stream_events(stdout)
    usage = _last_turn_usage(events)
    result = AgentResult(
        role="review",
        model=model,
        final_text=_last_agent_message(events),
        input_tokens=_as_int(usage.get("input_tokens")),
        cached_input_tokens=_as_int(usage.get("cached_input_tokens")),
        output_tokens=_as_int(usage.get("output_tokens")),
        turns=None,
        seconds=seconds,
        exit_code=exit_code,
        raw_path=raw_path,
    )
    return result, parsed_review
