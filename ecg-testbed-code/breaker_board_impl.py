"""Circuit breaker board - core implementation.

Implements ECT-10004.

Part of the ECG evaluation test bed. This module is fixture, not product code:
it exists so the code->work-item edges in Capability CAP-B have something real
to resolve against. It is deliberately outside saleor/ so the ingestion counts
asserted by band A do not move.
"""


BREAKER_FAILURE_THRESHOLD_PERCENTAGE = 35
BREAKER_FAILURE_MIN_COUNT = 100


def should_open(failures: int, total: int) -> bool:
    """Open once the failure rate crosses the threshold, with a floor on volume.

    Implements ECT-10004: the board must not trip on a handful of
    requests, however bad the ratio looks.
    """
    if total < BREAKER_FAILURE_MIN_COUNT:
        return False
    return (failures / total) * 100 >= BREAKER_FAILURE_THRESHOLD_PERCENTAGE
