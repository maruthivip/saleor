"""Row-locking helper shared by checkout and payment.

Implements ECT-10031 and ECT-10081.

Part of the ECG evaluation test bed. This module is fixture, not product code:
it exists so the code->work-item edges in Capability CAP-B have something real
to resolve against. It is deliberately outside saleor/ so the ingestion counts
asserted by band A do not move.
"""


from contextlib import contextmanager


@contextmanager
def lock_objects(qs, *, skip_locked: bool = False):
    """Lock a queryset for update.

    Implements ECT-10031 for the checkout path and
    ECT-10081 for the payment path. One utility, two tickets - a
    valid N:N state, and the reverse lookup must return both.
    """
    yield qs.select_for_update(skip_locked=skip_locked)
