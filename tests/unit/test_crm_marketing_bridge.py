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


def test_crm_app_hook_triggers():
    from intentos.apps.crm_pipeline.app import CRMPipelineApp
    triggered_leads = []
    CRMBridge._lead_listeners.clear()
    CRMBridge.register_lead_listener(lambda cid, data: triggered_leads.append((cid, data)))

    app = CRMPipelineApp()
    app.lead_analyzer("cust_123", "我想咨询购买产品")

    assert len(triggered_leads) == 1
    assert triggered_leads[0][0] == "cust_123"

