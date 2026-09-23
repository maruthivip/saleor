# ECG test bed - code link fixture

These files exist to give Capability CAP-B (story B1) real code-to-work-item
edges to resolve. They are fixture, not product code, and they sit outside
`saleor/` so the ingestion counts asserted elsewhere in the suite do not change.

| Work item | Implements (strong) | References (weak) |
| --- | --- | --- |
| `ECT-10004` | breaker_board_impl.py, breaker_board_metrics.py | breaker_board_followup.py |
| `ECT-10005` | retry_budget.py | retry_budget.py (same file, both edges) |
| `ECT-10033` | *(none)* | deferred_payload_todo.py |
| `ECT-10031` + `ECT-10081` | shared_locking.py (one file, two tickets) | *(none)* |
| `ECT-10071` | schema_validation.py | *(none)* |
| `ECT-10077` | *(none)* | schema_validation.py |
| `ECT-10022` | *(none)* | *(none)* |

The strong edge is a commit message or code comment stating that the code
implements the ticket. The weak edge is a mention - typically a TODO naming a
ticket that has not been built. Conflating them creates false confidence about
what actually shipped, which is the whole point of B1.

Push this directory to the indexed repository, or the edges do not exist for
the connector to find.
