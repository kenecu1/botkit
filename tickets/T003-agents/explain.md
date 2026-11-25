# T003 agents explain

Tier: B (bootstrap ticket, interface level explain)

## src/botkit/agents.py
- Contains builder and reviewer, builder recieves a spec, ticket, tests and builds given task in a clone then outputs a record. The Reviewer accepts patch without any builder summary to review in the most unbias way. Builder uses a subprocess to run claude to build then stores that build info into AgentResult record. UsageLimitError would occur when claude or codex runs out of usage. If build timeout it raises TimeoutError and run ends. Review timeout outputs None and move on to verdict. Before the build, it removes SSH_AUTH_SOCK, GH_TOKEN, GITHUB_TOKEN and GIT_ASKPASS so the bot has no way to push or log in to GitHub, and ANTHROPIC_API_KEY so it uses your plan login instead of billing a key.

## Compared with the bot's summary
- I thought timeouts restart the run. A build timeout kills the process group and ends the run as ERROR; a review timeout returns None and the tests still decide.
- I mixed up the env scrub with the clone setup. Removing the remote happens in the clone; agents.py removes 5 variables so the bot cannot push or bill a key.
- I said it outputs a patch. agents.py only returns an AgentResult; the patch export belongs to sandbox (T002).
- Untested: the process group kill in default_runner. Worth a test in a later ticket.
