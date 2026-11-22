# Corrections log

| Date | Ticket | What went wrong | Fix type | Fix |
|---|---|---|---|---|
| Nov 22 | T001 | Spec had 5 error cases with no tests; builder tried an outside script and was denied | test | Add the 5 tests (todo) |
| Nov 22 | T001 | Guard "before" snapshot lost when the Python shell closed | code | record saves guard.json (T005) |