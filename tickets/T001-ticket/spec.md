# Spec: ticket.py

## Goal
Read a ticket folder and output a filled-in Ticket record.

## Signatures
File: `src/botkit/ticket.py`

```python
from botkit.shapes import Ticket

def read_ticket(ticket_folder_path: str) -> Ticket: ...
```

## Inputs and outputs

Input:
- `ticket_folder_path` (`str`): path to one ticket folder, absolute or relative. A trailing slash does not change the result.

The folder holds:
- `brief.md`: any text.
- `spec.md`: any text.
- `ticket.toml`: TOML with these keys and types:

| Key | Type |
|---|---|
| `base` | string |
| `test_cmd` | string |
| `acceptance` | list of strings |
| `touches` | list of strings |
| `by_hand` | boolean |

Output: a `Ticket` from `botkit.shapes`, filled as follows.

| Field | Value |
|---|---|
| `repo_path` | Absolute path of the folder two levels above the ticket folder, as `str`. Made absolute without following symlinks (like `os.path.abspath`) |
| `ticket_name` | Name of the ticket folder, for example `"T001-ticket"` |
| `brief` | Full text of `brief.md` |
| `spec` | Full text of `spec.md` |
| `base` | `base` from `ticket.toml` |
| `test_cmd` | `test_cmd` from `ticket.toml` |
| `acceptance` | `acceptance` from `ticket.toml`, as a `tuple[str, ...]` |
| `touches` | `touches` from `ticket.toml`, as a `tuple[str, ...]` |
| `by_hand` | `by_hand` from `ticket.toml` |

Errors:
- `ticket.toml` missing, or the folder does not exist: raise `FileNotFoundError` whose message names `ticket.toml`.
- A key missing from `ticket.toml`: raise `KeyError` whose message names the missing key.
- A key in `ticket.toml` with the wrong type, or an item in `acceptance` or `touches` that is not a string: raise `TypeError` whose message names the key.
- Broken TOML: the `tomllib.TOMLDecodeError` from the standard library is raised unchanged.

## Examples
1. Normal: a folder with brief.md, spec.md and a full ticket.toml gives a Ticket with every value copied over. `acceptance` and `touches` come back as tuples, even though ticket.toml writes them as lists.
2. Worked out: for `/home/kenecu/dev/botkit/tickets/T001-ticket`, `ticket_name` is `"T001-ticket"` and `repo_path` is `"/home/kenecu/dev/botkit"` (two folders up).
3. Unusual but allowed: `by_hand = true` and `touches` with three files. Both are read normally into the Ticket.
4. Broken: the folder has no ticket.toml. Raise `FileNotFoundError` with a message that names `ticket.toml`.

## Edge cases
- `by_hand = true`: read normally. Refusing it is not this module's job.
- `touches` with several files: every file is kept, in the order written.
- Relative input path: `repo_path` is still absolute.
- Trailing slash on the input path: same Ticket as without it.
- Symlinks in the path: kept as written, not resolved.
- No `ticket.toml`, or the folder does not exist: `FileNotFoundError` naming `ticket.toml`.
- A key missing from `ticket.toml`: `KeyError` naming the key.
- A key with the wrong type, such as `by_hand = "yes"` or `acceptance = "tests/x.py"`: `TypeError` naming the key.
- A non-string item in a list, such as `acceptance = ["tests/a.py", 5]`: `TypeError` naming the key.
- Broken TOML: `tomllib.TOMLDecodeError`, unchanged.
- Extra unknown keys in `ticket.toml`: ignored. This may change later, since this is a prototype.

## Acceptance tests
All in `tests/test_ticket.py`:

| Test | Covers |
|---|---|
| `test_full_folder_gives_ticket_with_every_value_and_tuples` | Example 1 |
| `test_name_is_folder_name_and_repo_path_is_two_folders_up` | Example 2 |
| `test_by_hand_true_and_three_touches_are_read_normally` | Example 3 |
| `test_missing_ticket_toml_raises_file_not_found_naming_it` | Example 4 |
| `test_missing_key_in_ticket_toml_raises_key_error_naming_it` | Missing key |
| `test_relative_path_gives_absolute_repo_path` | Relative path |
| `test_trailing_slash_gives_same_ticket` | Trailing slash |

## Out of scope
- It should only ever read a ticket folder and output a Ticket record.
- It does not refuse `by_hand` tickets. `pipeline` does that.
- It does not check that `base` is a real commit. `sandbox` finds out when it clones.
- A missing `brief.md` or `spec.md`. The brief is always written before the spec, so both are expected to exist.
- Any type checking beyond the key types and string items listed above.

## Proposed
Not covered by the acceptance tests. Approve, change or drop each one.

1. Assumption: a wrong value type raises `TypeError`. You asked for the check but did not name the error. `TypeError` is the standard Python error for a wrong type.
2. Assumption: a non-string item in `acceptance` or `touches` also raises `TypeError` naming the key. You asked for the check but did not name the error.
3. Not tested, by your choice: a missing folder, broken TOML, extra keys, symlinks and the type checks (wrong key types and non-string list items) are in the spec but have no tests. The type checks may change as more fields are added.
