"""Snapshot git state and report what changed."""


"""takes two snapshots of same repo, returns a list of messages (one per change)
   an empty list if nothing changed, different repos raise ValueError"""
def compare(before, after):
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


