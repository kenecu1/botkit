#!/usr/bin/env bash
# Throwaway stand-in for pipeline. Delete once `botkit run` works.
# Usage: ~/.botkit/manual_build.sh T005-record
set -euo pipefail

T="$1"
REPO="$HOME/dev/botkit"
cd "$REPO"

if [ -n "$(git status --porcelain)" ]; then
  echo "Stop: the real repo has uncommitted changes. Commit or restore them first."
  exit 1
fi

BASE="$(git rev-parse HEAD)"

read -r PROMPT_FILES TOUCHES ACCEPT <<<"$(python - "$T" <<'EOF'
import sys
from botkit.ticket import read_ticket
t = read_ticket(f"tickets/{sys.argv[1]}")
if t.by_hand:
    sys.exit("Stop: this ticket is by_hand, so it is not built by a bot.")
files = ",".join([f"tickets/{t.ticket_name}/spec.md", f"tickets/{t.ticket_name}/brief.md", "src/botkit/shapes.py", *t.acceptance])
print(files, ",".join(t.touches), " ".join(t.acceptance))
EOF
)"

RUN="$HOME/.botkit/runs/botkit/$T/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUN"
echo "$BASE" > "$RUN/base.txt"
echo "$RUN" > "$HOME/.botkit/current_run"
echo "Run folder: $RUN"

git clone -q "$REPO" "$RUN/clone"
cd "$RUN/clone"
git checkout -q --detach "$BASE"
git remote remove origin
export PYTHONPATH="$RUN/clone/src"

python - "$RUN" "$REPO" <<'EOF'
import json, sys, dataclasses
from botkit.guard import take_snapshot
run, repo = sys.argv[1], sys.argv[2]
snaps = [take_snapshot(f"{run}/clone"), take_snapshot(repo)]
with open(f"{run}/guard_before.json", "w") as f:
    json.dump([dataclasses.asdict(s) for s in snaps], f, indent=2)
EOF

cat > "$RUN/prompt.txt" <<EOF
Build ticket $T. Read ${PROMPT_FILES//,/, }.
Change only ${TOUCHES//,/, }.
Test command: pytest
EOF

echo "Building. Do not switch branches, commit or push in $REPO until this finishes."
env -u SSH_AUTH_SOCK -u ANTHROPIC_API_KEY -u GH_TOKEN -u GITHUB_TOKEN \
  timeout 30m claude -p --model claude-opus-5-5 \
  --permission-mode acceptEdits --permission-prompts none \
  --allowedTools "Bash(pytest *)" \
  --disallowedTools "Bash(git commit *)" "Bash(git push *)" \
  --append-system-prompt-file "$REPO/prompts/builder_rules.md" \
  --output-format json --max-turns 60 --no-session-persistence \
  < "$RUN/prompt.txt" > "$RUN/build.json" || echo "Builder exited with an error. Check build.json."

echo "== Guard =="
python - "$RUN" <<'EOF'
import json, sys
from botkit.shapes import Snapshot
from botkit.guard import take_snapshot, compare
problems = []
for d in json.load(open(f"{sys.argv[1]}/guard_before.json")):
    before = Snapshot(**d)
    found = compare(before, take_snapshot(before.repo))
    print(before.repo, found)
    problems += found
print("VIOLATION, do not apply the patch" if problems else "Guard clean")
EOF

echo "== Build =="
python - "$RUN" <<'EOF'
import json, sys
d = json.load(open(f"{sys.argv[1]}/build.json"))
print("is_error:", d["is_error"], "| turns:", d["num_turns"], "| minutes:", d["duration_ms"] // 60000)
print("denials:", [x["tool_input"].get("command", x["tool_name"])[:80] for x in d["permission_denials"]])
EOF

git add -A
echo "== Test files the bot changed (should be empty) =="
git diff --cached --stat "$BASE" -- tests/
git diff --cached "$BASE" > "$RUN/change.patch"
echo "== Files in the patch (should match touches: $TOUCHES) =="
git diff --cached --stat "$BASE"
echo "== Added lines with # (comments) =="
grep -c "^+.*#" "$RUN/change.patch" || true

echo "== Restoring tests and pytest config from base =="
git diff --cached --name-only --diff-filter=A "$BASE" -- tests/ | while IFS= read -r f; do
  echo "Removing test file the bot added: $f"
  git rm -q -f -- "$f"
done
git checkout -q "$BASE" -- tests/
git clean -q -f -d -x -- tests/
for f in pytest.ini pyproject.toml; do
  if git cat-file -e "$BASE:$f" 2>/dev/null; then
    git checkout -q "$BASE" -- "$f"
  elif [ -e "$f" ]; then
    echo "Removing $f, which the bot added"
    git rm -q -f -- "$f"
  fi
done

COLLECTED="$(pytest --collect-only -q $ACCEPT 2>&1 | tail -n 1 || true)"
echo "Acceptance tests collected: $COLLECTED"

echo "== Tests =="
pytest $ACCEPT && pytest | tee "$RUN/tests.txt" || echo "Tests FAILED"

echo
echo "Done. Next: explain.md in $RUN, change by hand, re-export the patch, then apply on the branch."
echo "New terminal? Run: RUN=\$(cat ~/.botkit/current_run)"
