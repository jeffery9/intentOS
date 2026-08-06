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


def test_marketing_manifest_loading():
    from pathlib import Path
    app_dir = Path(__file__).parent.parent.parent / "intentos" / "apps" / "marketing_pipeline"
    manifest_path = app_dir / "manifest.yaml"
    assert manifest_path.exists()


def test_marketing_app_auto_registration():
    from intentos.apps.marketing_pipeline import create_marketing_pipeline_app
    m_app = create_marketing_pipeline_app()
    assert len(CRMBridge._lead_listeners) > 0


def test_marketing_campaign_enrollments():
    from intentos.apps.marketing_pipeline import create_marketing_pipeline_app
    CRMBridge._lead_listeners.clear()
    CRMBridge._quote_listeners.clear()
    CRMBridge._refund_listeners.clear()

    m_app = create_marketing_pipeline_app()

    # Flow 1: High Anger lead
    CRMBridge.notify_lead_analyzed("cust_angry", {"anger_score": 0.9, "score": 70})
    assert len(m_app.campaign_enrollments.get("cust_angry", [])) == 1
    assert m_app.campaign_enrollments["cust_angry"][0]["campaign_name"] == "Win-Back Retention Program"
    assert m_app.campaign_enrollments["cust_angry"][0]["discount_rate"] == 30.0

    # Flow 3: Warm prospect lead
    CRMBridge.notify_lead_analyzed("cust_warm", {"anger_score": 0.2, "score": 65})
    assert len(m_app.campaign_enrollments.get("cust_warm", [])) == 1
    assert m_app.campaign_enrollments["cust_warm"][0]["campaign_name"] == "Lead Nurture Campaign"
    assert m_app.campaign_enrollments["cust_warm"][0]["discount_rate"] == 15.0

    # Flow 2: VIP loyalty quote
    CRMBridge.notify_quote_generated("cust_vip", {"final_price": 1200.0})
    assert len(m_app.campaign_enrollments.get("cust_vip", [])) == 1
    assert m_app.campaign_enrollments["cust_vip"][0]["campaign_name"] == "VIP Loyalty Program"
    assert m_app.campaign_enrollments["cust_vip"][0]["credit"] == 150.0

    # Flow 4: Refund triggers Win-Back
    CRMBridge.notify_refund_requested("cust_refund", {"amount": 250.0})
    assert len(m_app.campaign_enrollments.get("cust_refund", [])) == 1
    assert m_app.campaign_enrollments["cust_refund"][0]["campaign_name"] == "Win-Back Retention Program"




