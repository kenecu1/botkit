"""Load stories (story.json, spec.md, seeded.diff, clean.diff, bug.json, hidden_tests/) and run the sanity check.

Ticket: BK-10   Tier: A
Design: docs/design.md
"""

def load_dataset(folder):
    raise NotImplementedError


def check_dataset(stories):
    """Visible tests pass on both diffs; hidden tests fail on seeded and pass on clean."""
    raise NotImplementedError
