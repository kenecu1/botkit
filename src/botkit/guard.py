"""Snapshot git state and report what changed."""

import subprocess
import hashlib

from botkit.shapes import Snapshot


def _git(repo, args):
    """takes repo path and list of command words, runs git with them in that folder and returns output text"""

    result = subprocess.run(
        ["git"] + args,
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,

    )
    return result.stdout


def take_snapshot(repo):
    """Record the git state of one repo at this momement"""

    head = _git(repo, ["rev-parse", "HEAD"]).strip()

    refs = {}
    for line in _git(repo, ["show-ref"]).splitlines():
        commit_id, name = line.split()
        refs[name] = commit_id

    reflog_len = len(_git(repo, ["reflog"]).splitlines())

    with open(f"{repo}/.git/config", "rb") as f:
        config_hash = hashlib.sha256(f.read()).hexdigest()

    return Snapshot(repo=repo, head=head, refs=refs, reflog_len=reflog_len, config_hash=config_hash)


def compare(before, after):
    """takes two snapshots of same repo, returns a list of messages (one per change)
    an empty list if nothing changed, different repos raise ValueError"""

    if before.repo != after.repo:
        raise ValueError(f"Before {before.repo} doesn't match with after {after.repo}")

    problems = []

    if before.head != after.head:
        problems.append(f"HEAD changed from {before.head} to {after.head}")
    if before.reflog_len != after.reflog_len:
        problems.append(f"reflog_len changed from {before.reflog_len} to {after.reflog_len}")
    if before.refs != after.refs:
        problems.append(f"refs changed from {before.refs} to {after.refs}")
    if before.config_hash != after.config_hash:
        problems.append(f"config_hash changed from {before.config_hash} to {after.config_hash}")

    return problems


