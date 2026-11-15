"""Snapshot git state and report what changed."""


def compare(before, after):
    if before.repo != after.repo:
        raise ValueError(f"Before {before.repo} doesn't match with after {after.repo}")

    problems = []

    if before.head != after.head:
        problems.append(f"HEAD changed from {before.head} to {after.head}")
    if before.reflog_len != after.reflog_len:
        problems.append(f"reflog_len changed from {before.reflog_len} to {after.reflog_len}")

    return problems


