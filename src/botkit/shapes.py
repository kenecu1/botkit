"""Records shared by every Botkit module"""

from dataclasses import dataclass


@dataclass(frozen = True)
class Snapshot:
    """Snapshot of each original and copy repo at one moment for comparison start and finish"""
    
    repo: str
    head: str
    refs: dict[str, str]
    reflog_len: int
    config_hash: str


