# Spec: agents.py

## Goal
Runs a CLI as a subprocess and turns the output into a record.

## Signatures
File: `src/botkit/agents.py` (new)

```python
from botkit.shapes import AgentResult, Review

class UsageLimitError(Exception): ...

def default_runner(args: list[str], *, stdin: str, cwd: str | None,
                   env: dict[str, str] | None, timeout: float) -> tuple[int, str]: ...

def build(clone_path: str, prompt: str, model: str, timeout: float,
          rules_path: str, test_cmd: str, out_path: str,
          runner=default_runner) -> AgentResult: ...

def review(prompt: str, model: str, timeout: float, out_path: str, cwd: str,
           runner=default_runner) -> tuple[AgentResult, Review] | None: ...
```

## Inputs and outputs

### UsageLimitError
Its own error class, a direct subclass of `Exception`. It is **not** a `TimeoutError`.

### runner
`runner(args, *, stdin, cwd, env, timeout) -> (exit_code, stdout)`
- `args`: the command as a list of strings. Never a shell string.
- `stdin`: the prompt text, sent on standard input.
- `cwd`: the folder to run in.
- `env`: the full environment for the process, or `None` to inherit.
- `timeout`: wall clock seconds.
- Returns `(exit_code: int, stdout: str)`.
- On timeout it raises `subprocess.TimeoutExpired`, with any partial stdout in `.output`.

`default_runner` is the real one. It starts the process with `subprocess.Popen(args, stdin=PIPE, stdout=PIPE, text=True, cwd=cwd, env=env, start_new_session=True)` and calls `communicate(stdin, timeout=timeout)`. On timeout it kills the whole process group with `os.killpg(proc.pid, signal.SIGKILL)`, collects any partial output, and raises `subprocess.TimeoutExpired(args, timeout, output=partial)`. stderr is not captured. Never `shell=True`.

### build
- Makes `out_path` (the run folder, given by the pipeline) with `os.makedirs(out_path, exist_ok=True)`.
- Calls `runner` once:
  - `args`:
    ```
    ["claude", "-p", "--model", model,
     "--permission-mode", "acceptEdits", "--permission-prompts", "none",
     "--allowedTools", f"Bash({test_cmd} *)",
     "--disallowedTools", "Bash(git commit *)", "Bash(git push *)",
     "--append-system-prompt-file", rules_path,
     "--output-format", "json", "--max-turns", "60", "--no-session-persistence"]
    ```
  - `stdin=prompt`, `cwd=clone_path`, `timeout=timeout`
  - `env`: a copy of `os.environ` with exactly these keys removed: `SSH_AUTH_SOCK`, `GH_TOKEN`, `GITHUB_TOKEN`, `GIT_ASKPASS`, `ANTHROPIC_API_KEY`. `os.environ` itself is not changed.
- If `runner` raises `subprocess.TimeoutExpired`, `build` raises `TimeoutError`. The message names the problem and where it happened, e.g. `"build timed out after 1200s in /path/to/clone"`. It must contain `build`, `timed out` and `clone_path`. No retry.
- Otherwise it writes stdout exactly as returned to `<out_path>/build_raw.json` (UTF-8), then:
  - **Usage limit:** if the run failed (`exit_code != 0`, or stdout is a JSON object with `is_error` true) and stdout contains `usage limit` in any case, it raises `UsageLimitError`. The message contains `build` and `usage limit`.
  - Otherwise it returns `AgentResult`:

| Field | Value |
|---|---|
| `role` | `"build"` |
| `model` | the one key of `modelUsage` if there is exactly one, otherwise the `model` argument |
| `final_text` | `result` if it is a string, otherwise `None` |
| `input_tokens` | `usage.input_tokens + usage.cache_creation_input_tokens + usage.cache_read_input_tokens` |
| `cached_input_tokens` | `usage.cache_read_input_tokens` |
| `output_tokens` | `usage.output_tokens` |
| `turns` | `num_turns` |
| `seconds` | wall clock seconds around the `runner` call (`time.monotonic`), a `float` >= 0 |
| `exit_code` | the runner's exit code |
| `raw_path` | `os.path.join(out_path, "build_raw.json")` |

A value that is missing, or not an `int`, becomes `None`. If stdout is not a JSON object, every parsed field is `None`.

### review
- Makes `out_path` with `os.makedirs(out_path, exist_ok=True)`.
- Calls `runner` once:
  - `args`:
    ```
    ["codex", "exec", "-m", model, "-s", "read-only", "--ephemeral",
     "--ignore-user-config", "--ignore-rules",
     "--output-schema", <abs path of schemas/review.json>,
     "-o", os.path.join(out_path, "review.json"),
     "--json", "-"]
    ```
  - `stdin=prompt`, `cwd=cwd`, `env=None` (inherits), `timeout=timeout`
- `prompt` is passed exactly as given. `review` never builds, reads or changes the prompt.
- The schema path is found from the package location: `<repo>/schemas/review.json`, two folders above `src/botkit/`.
- Raw output file: `<out_path>/review_raw.jsonl`, UTF-8.

What happens:
1. **Timeout** (`runner` raises `subprocess.TimeoutExpired`): writes `.output` to the raw file, or `""` if it is `None`. Returns `None`. Doesn't raise, doesn't retry.
2. Otherwise writes stdout exactly as returned to the raw file.
3. **Usage limit:** if `exit_code != 0` and stdout contains `usage limit` in any case, raises `UsageLimitError`. The message contains `review` and `usage limit`.
4. **Crash:** if `exit_code != 0`, returns `None`.
5. Reads `<out_path>/review.json`. Returns `None` if it is missing, isn't valid JSON, lacks `summary` (str) or `findings` (list), or any finding lacks a required field or has the wrong type. Also returns `None` if a finding's `severity` is not in the `severity` enum of `schemas/review.json` (today `bug`, `risk`).
6. Otherwise returns `(AgentResult, Review)`:

`AgentResult`:

| Field | Value |
|---|---|
| `role` | `"review"` |
| `model` | the `model` argument (the Codex stream does not report one) |
| `final_text` | `item.text` of the last `item.completed` event whose `item.type` is `agent_message`, else `None` |
| `input_tokens` | `usage.input_tokens` of the last `turn.completed` event |
| `cached_input_tokens` | `usage.cached_input_tokens` of that event |
| `output_tokens` | `usage.output_tokens` of that event |
| `turns` | `None` |
| `seconds` | wall clock seconds around the `runner` call, a `float` >= 0 |
| `exit_code` | the runner's exit code |
| `raw_path` | `os.path.join(out_path, "review_raw.jsonl")` |

Lines in the stream that aren't valid JSON are skipped. A missing number is `None`.

`Review`:
- `summary`: from `review.json`
- `findings`: a tuple of `Finding`, in file order
- `bug_count`: the number of findings with `severity == "bug"`

## Examples
1. Normal (build): returns an AgentResult record. Set fake numbers so made-up gets caught.
2. Normal (review): returns a tuple of AgentResult and Review records, or None. Set fake numbers so made-up gets caught.
3. Unusual: zero findings, and crash returning None (review timeout also returns None without raising).
4. Env: `SSH_AUTH_SOCK`, git token variables and `ANTHROPIC_API_KEY` are left out of the builder's environment. Test it for sure that it's left out.
5. Broken: build timeout raises `TimeoutError` with the problem and where it happened.

## Edge cases
| Case | Result |
|---|---|
| Review has zero findings | `(AgentResult, Review(summary, (), 0))`, not `None` |
| Review crashes (`exit_code != 0`, no usage limit) | raw output saved, returns `None` |
| Review times out | process group killed, partial output saved, returns `None` |
| Review exits 0 but `review.json` is missing, unreadable, malformed or has an unknown severity | returns `None` |
| Successful review stream mentions "usage limit" in its text (exit 0) | not a usage limit, parsed normally |
| Build times out | process group killed, `TimeoutError` naming `build`, `timed out` and `clone_path` |
| Build crashes (`exit_code != 0` or `is_error`, no usage limit) | raw output saved, returns `AgentResult` with the real `exit_code` and `None` for anything missing |
| Build stdout isn't JSON | `AgentResult` with every parsed field `None` |
| Usage limit in build or review | raw output saved, `UsageLimitError` |
| One of the five secret env vars isn't set | no error, still absent |
| `runner` raises anything else (e.g. `FileNotFoundError` when the CLI isn't installed) | propagates unchanged |

## Out of scope
- No committing.
- Just building via given instructions in the subprocess and then filling in AgentResult to output.
- Don't change any other files.
- No retries on timeout or crash.
- Never reads the ticket folder.

## Proposed
Not covered by the acceptance tests.

**Needs a decision**
1. **`test_cmd` for build (settled).** Added to the brief and to `build()`. It is passed as one argument, `--allowedTools`, `Bash(<test_cmd> *)`, exactly as written, per design runner rule 2.
2. **Reviewer prompt contents (settled).** The prompt holds the spec, the diff (the builder's patch) and the test output, never the builder's summary. `review()` passes the prompt through untouched, so whoever builds the prompt enforces this. The brief's Inputs line ("Brief, spec and patch") should be updated to match.

**Assumptions**
3. **Usage-limit detection.** It uses the phrase `usage limit`, in any case, and only on a failed run. Installed Claude 2.1.332 contains "Usage limit reached" and "you have reached your weekly usage limit". I found no exact Codex message, only a `usage_limited` status. Confirm both with a day-1 probe and save the outputs as fixtures. The fakes in the tests are placeholders.
4. **Input tokens for Claude** are the total input (plain + cache write + cache read) and `cached_input_tokens` is the cache read. That matches Codex, where `input_tokens` already includes the cached ones.
5. **`turns` is `None` for review.** The Codex stream has no turn count.
6. **`model` for build** is the one key in `modelUsage` (design runner rule 3: record the model the run reports). For review it's the argument.
7. **`--max-turns 60`** is hard-coded from design section 4. `botkit.toml` also has `max_turns = 60`, but the brief doesn't pass it in.
8. **The schema path** is found from the package location, because the brief doesn't pass it in.
9. **The reviewer's environment** is inherited unchanged. Only the builder's is stripped, per the brief.
10. **stderr** isn't captured, and passes through to the terminal.
11. **A partial build output on timeout** isn't saved. Only the review saves partial output.

**Extra tests to consider**
12. `default_runner` kills the group: run `["sh", "-c", "sleep 30 & sleep 30"]` with `timeout=0.5`, check that `subprocess.TimeoutExpired` is raised within a few seconds and that the background `sleep` is gone. This uses a real process but no model or network.
13. A build crash (exit 1, stdout `"not json"`) returns `AgentResult(exit_code=1, final_text=None, input_tokens=None, ...)`.
14. A review that exits 0 with `review.json` missing, invalid JSON, or `severity: "nit"` returns `None`.
15. The exact `args` lists for build and review (only the key flags are checked now).
