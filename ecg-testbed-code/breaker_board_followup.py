"""Circuit breaker board - work not yet done.

References ECT-10004. Does NOT implement it.

Part of the ECG evaluation test bed. This module is fixture, not product code:
it exists so the code->work-item edges in Capability CAP-B have something real
to resolve against. It is deliberately outside saleor/ so the ingestion counts
asserted by band A do not move.
"""


# TODO(ECT-10004): persist board state in Redis so a worker restart
# does not reset every breaker to closed. Nothing here is built yet - this file
# only names the ticket, which is the weak edge B1 must keep separate from the
# strong one.


def placeholder() -> None:
    """Intentionally empty. Presence of a name is not evidence of work."""
    return None
