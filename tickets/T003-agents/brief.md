# Brief: agents.py

## Goal
Runs a CLI as a subprocess and turns the output into a record.

## Inputs
- build: `clone_path`, `prompt`, `model`, `timeout`, `rules_path`, `runner` (fake runner gets passed in via a parameter, like subprocess.run or something). Builder runs in clone so it needs clone path.
- review: `prompt`, `model`, `timeout`, `out_path`, `runner`. Brief, spec and patch are in prompt. `out_path` is pipeline's path.
- Agent never reads ticket folder itself, that's for a different part.

## Outputs
- build calls claude through the cli and returns an AgentResult record.
- review calls codex through the cli and returns a tuple of AgentResult and Review records, or None.
- Raise if it can't continue, return None when it can continue without it.
- Build timeout: kill the group because it will have to start all over, raise `TimeoutError` listing the problem and where it occurred.
- Usage limit (build or review): raise `TimeoutError`, because it literally cannot continue no matter what.
- Review crash or timeout: save raw output to pipeline's path, return None without raising, since review comes after the test run.
- Removing `SSH_AUTH_SOCK`, git token variables and `ANTHROPIC_API_KEY` from the builder's environment is agents' job, since it's the code that starts the process.

## Examples
1. Normal (build): returns an AgentResult record. Set fake numbers so made-up gets caught.
2. Normal (review): returns a tuple of AgentResult and Review records, or None. Set fake numbers so made-up gets caught.
3. Unusual: zero findings, and crash returning None (review timeout also returns None without raising).
4. Env: `SSH_AUTH_SOCK`, git token variables and `ANTHROPIC_API_KEY` are left out of the builder's environment. Test it for sure that it's left out.
5. Broken: build timeout raises `TimeoutError` with the problem and where it happened.

## Out of scope
- No committing.
- Just building via given instructions in the subprocess and then filling in AgentResult to output.
- Don't change any other files.
- No retries on timeout or crash.
- Never reads the ticket folder.

## Touches
- src/botkit/agents.py (new file; no existing files change)
