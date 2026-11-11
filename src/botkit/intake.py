"""Read spec.md and check every required field is there.

Ticket: BK-3   Tier: B
Design: docs/design.md
"""

REQUIRED = ["Tier", "Inputs", "Outputs", "Edge cases", "Visible tests"]


class MarkdownIntake:
    def load(self, spec_path, project_path):
        """Return a Ticket, or raise INVALID_SPEC listing missing fields. Tier A is refused."""
        raise NotImplementedError


def split_headings(text):
    """Split a Markdown file on '## ' headings -> {heading: body}. Used for spec.md and project_rules.md."""
    raise NotImplementedError


def load_project_rules(project_path):
    """Read project_rules.md -> test, build, lint commands (first non empty line under each heading)."""
    raise NotImplementedError
