"""Append one line per step to status.jsonl. Sum up metrics.

Ticket: BK-8 basic, Phase 4 full   Tier: C
Design: docs/design.md
"""

def log_event(event, path="status.jsonl"):
    raise NotImplementedError


def metrics(store):
    """Tickets by status, average attempts, tokens and cost per ticket."""
    raise NotImplementedError

# Phase 3: NtfyNotifier (phone). Phase 4: status page that reads status.jsonl.
