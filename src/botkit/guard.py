"""Snapshot git state and report what changed."""

def compare(before, after):
    problems = []

    if before.head != after.head:
        problems.append(f"HEAD changed from {before.head} to {after.head}")
    if before.reflog_len != after.reflog_len:
        problems.append(f"reflog_len changed form {before.reflog_len} to {after.reflog_len}")

    return problems


