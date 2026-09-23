"""Async webhook retry budget.

Implements ECT-10005, and also carries a TODO naming it.

Part of the ECG evaluation test bed. This module is fixture, not product code:
it exists so the code->work-item edges in Capability CAP-B have something real
to resolve against. It is deliberately outside saleor/ so the ingestion counts
asserted by band A do not move.
"""


RETRY_BACKOFF_SECONDS = 10
MAX_RETRIES = 5


def retry_policy() -> dict:
    """Return the delivery retry policy.

    Implements ECT-10005: five attempts with exponential backoff from
    ten seconds, replacing the previous three attempts at a fixed thirty.
    """
    return {"max_retries": MAX_RETRIES, "backoff": RETRY_BACKOFF_SECONDS}


# TODO(ECT-10005): the webhook delivery design page still documents the
# old policy and needs correcting.
#
# This file is therefore in BOTH lists for that ticket - it implements it and
# it references it. That is a valid state and must not be de-duplicated away.
