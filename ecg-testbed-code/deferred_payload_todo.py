"""Deferred webhook payload generation - open work.

References ECT-10033. No implementing code exists for it.

Part of the ECG evaluation test bed. This module is fixture, not product code:
it exists so the code->work-item edges in Capability CAP-B have something real
to resolve against. It is deliberately outside saleor/ so the ingestion counts
asserted by band A do not move.
"""


DEFERRED_PAYLOAD_MAX_RETRIES = 12

# TODO(ECT-10033): raise the retry budget for deferred payload
# generation once the queue split lands. This is the only mention of that
# ticket anywhere in the repository: its "Implements" list must come back
# empty, and an empty strong list is a finding, not an error.
