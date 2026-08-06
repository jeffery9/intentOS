# -*- coding: utf-8 -*-
from intentos.apps.crm_pipeline.bridge import CRMBridge


def test_crm_bridge_registration():
    triggered = []
    def dummy_callback(customer_id, data):
        triggered.append((customer_id, data))

    CRMBridge._lead_listeners.clear()
    CRMBridge.register_lead_listener(dummy_callback)
    CRMBridge.notify_lead_analyzed("cust_abc", {"val": 123})

    assert len(triggered) == 1
    assert triggered[0] == ("cust_abc", {"val": 123})
