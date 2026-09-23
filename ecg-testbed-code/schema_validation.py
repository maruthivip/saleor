"""Sync webhook response schema validation.

Implements ECT-10071. Separately references ECT-10077.

Part of the ECG evaluation test bed. This module is fixture, not product code:
it exists so the code->work-item edges in Capability CAP-B have something real
to resolve against. It is deliberately outside saleor/ so the ingestion counts
asserted by band A do not move.
"""


REQUIRED_KEYS = ("status", "errors")


def validate_response(payload: dict) -> bool:
    """Check a sync webhook response against the expected shape.

    Implements ECT-10071.
    """
    return all(k in payload for k in REQUIRED_KEYS)


# TODO(ECT-10077): the validator still accepts an empty target URL
# upstream of this check, so a subscription can be saved that can never deliver.
#
# The ticket implemented here and the ticket referenced here are DIFFERENT. A
# reverse lookup that leaks one into the other's list has cross-contaminated the
# strong and weak edges, which is exactly what B3 AC-005 is for.
