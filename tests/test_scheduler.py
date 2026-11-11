"""Tests for scheduler. Use fake runners only.

Cases to write: happy path; tests fail then pass; retry cap reached with failing tests -> FAILED; cap reached with passing tests -> AWAITING_HUMAN; new commit -> SAFETY_VIOLATION; identical retry stops early; touched test file sets tests_changed; review only mode skips BUILDING and never retries
"""
