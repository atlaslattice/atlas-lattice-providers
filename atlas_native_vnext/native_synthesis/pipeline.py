"""End-to-end OFFLINE review preparation across two source-only Atlas codebases.

This does not authenticate users, post Work messages, dispatch Atlas ONE tasks,
query UWS, or write Alexandria. The SQLite store is a preparatory staging area,
NOT the SwarmChat receiver inbox or a hosted rights authority.
"""
from __future__ import annotations
from .engine import NativeSynthesis, generic_hold
from .interop import prepare_labs_crosswalk
from .offline_receipts import OfflinePreparationStore
from .wire import WireError, HEX64, IDENT

class OfflineAtlasPipeline:
    def __init__(self, labs_prepare, labs_catalog, store: OfflinePreparationStore):
        if not callable(labs_prepare) or not callable(labs_catalog) or not isinstance(store,OfflinePreparationStore):
            raise WireError('INVALID_LOCAL_PIPELINE')
        self.labs_prepare=labs_prepare
        self.labs_catalog=labs_catalog
        self.store=store
        self.native=NativeSynthesis()

    def prepare(self, lab_input, *, tenant, account, principal, room, epoch=0):
        """Two separately validated candidates -> a durable local non-send record.

        Idempotent by (opaque HMAC scope, request_id, native digest). A revoked
        *local* epoch blocks old staging; real host rights are NOT evaluated.
        """
        result=prepare_labs_crosswalk(lab_input,self.labs_prepare,self.labs_catalog,native=self.native)
        if result['status']!='LINKED_LOCAL_SOURCE_ONLY':
            return generic_hold()
        from .wire import strict_json
        try:
            x=strict_json(lab_input)
            rid=x['experiment_id']
            if type(rid) is not str or not IDENT.fullmatch(rid):
                return generic_hold()
            receipt=self.store.stage(tenant,principal,room,'review',
                                     result['labs_experiment_sha256'],rid,
                                     result['native_experiment_sha256'],epoch,account=account)
            if receipt['status'] not in ('NEW_PREPARED_LOCAL_ONLY','DEDUPLICATED_PREPARED_LOCAL_ONLY'):
                return generic_hold()
            return {'status':'LOCAL_REVIEW_PREPARED_NOT_SENT',
                    'lab_receipt_sha256':result['labs_experiment_sha256'],
                    'native_receipt_sha256':result['native_experiment_sha256'],
                    'local_sqlite_state':receipt['status'],
                    'atlas_one':'TASK_NOT_DISPATCHED',
                    'swarmchat':'WORK_MESSAGE_NOT_POSTED',
                    'alexandria':'GRAPH_NOT_WRITTEN',
                    'acl_verified':False,'peer_read':False,'host_attested':False,
                    'delivery_ack':False,'canon':False,'external_model_calls':0,
                    'provider_spend_usd':0}
        except (WireError,KeyError,TypeError,ValueError,AttributeError):
            return generic_hold()

    def withdraw_local(self, *, tenant, account, principal, room, source_sha256):
        """Synthetic local fencing only; cannot revoke actual account rights."""
        if type(source_sha256) is not str or not HEX64.fullmatch(source_sha256):
            return generic_hold()
        return self.store.withdraw(tenant,principal,room,'review',source_sha256,account=account)
