"""Circuit breaker board - state transition metrics.

Implements ECT-10004.

Part of the ECG evaluation test bed. This module is fixture, not product code:
it exists so the code->work-item edges in Capability CAP-B have something real
to resolve against. It is deliberately outside saleor/ so the ingestion counts
asserted by band A do not move.
"""


STATES = ("closed", "half_open", "open")


def emit_transition(app_id: str, before: str, after: str) -> dict:
    """Emit one state-change event.

    Implements ECT-10004. Second of the two modules built for that
    ticket, so the strong list for it has exactly two members.
    """
    assert before in STATES and after in STATES
    return {"app": app_id, "from": before, "to": after}
