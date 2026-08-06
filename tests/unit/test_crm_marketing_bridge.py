# -*- coding: utf-8 -*-
"""
CRM-Marketing Bridge Integration Tests
"""
from pathlib import Path
import pytest

from intentos.apps import IntentPackageLoader
from intentos.apps.crm_pipeline import create_crm_pipeline_app, CRMBridge
from intentos.apps.marketing_pipeline import create_marketing_pipeline_app

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
def clean_listeners():
    """Autouse fixture to clean global CRMBridge listeners state before and after every test."""
    CRMBridge.clear_listeners()
    yield
    CRMBridge.clear_listeners()

def test_marketing_manifest_validates():
    loader = IntentPackageLoader()
    app_dir = Path(__file__).parent.parent.parent / "intentos" / "apps" / "marketing_pipeline"
    package = loader.load(str(app_dir))
    assert package.app_id == "marketing_pipeline"
    val = loader.validate(package)
    assert val.is_valid is True

@pytest.mark.anyio
async def test_closed_loop_retention_on_anger():
    """Verify high anger triggers 30% retention campaign."""
    crm = create_crm_pipeline_app()
    mkt = create_marketing_pipeline_app()

    # Trigger high anger
    crm.lead_analyzer("cust_angry", "垃圾服务！太差了，我要退钱！")

    assert "cust_angry" in mkt.campaign_enrollments
    enrollments = mkt.campaign_enrollments["cust_angry"]
    assert any(e["campaign_name"] == "Win-Back Retention Program" and e["discount_rate"] == 30.0 for e in enrollments)

@pytest.mark.anyio
async def test_closed_loop_vip_on_high_quote():
    """Verify quote price >= 1000 triggers VIP loyalty $150 credit campaign."""
    crm = create_crm_pipeline_app()
    mkt = create_marketing_pipeline_app()

    # Trigger high quote
    crm.quote_generator("cust_vip", 2000.0, 10.0) # Price = 1800.0

    assert "cust_vip" in mkt.campaign_enrollments
    enrollments = mkt.campaign_enrollments["cust_vip"]
    assert any(e["campaign_name"] == "VIP Loyalty Program" and e["credit"] == 150.0 for e in enrollments)

@pytest.mark.anyio
async def test_closed_loop_nurture_on_warm_lead():
    """Verify lead score >= 60 triggers nurture 15% discount campaign."""
    crm = create_crm_pipeline_app()
    mkt = create_marketing_pipeline_app()

    # Trigger warm lead (Buying interest)
    crm.lead_analyzer("cust_warm", "我想购买合作产品")

    assert "cust_warm" in mkt.campaign_enrollments
    enrollments = mkt.campaign_enrollments["cust_warm"]
    assert any(e["campaign_name"] == "Lead Nurture Campaign" and e["discount_rate"] == 15.0 for e in enrollments)

@pytest.mark.anyio
async def test_graceful_fallback_without_marketing():
    """Verify that clearing listeners does not crash the CRM app flow."""
    crm = create_crm_pipeline_app()
    # Explicitly clear listeners to ensure no callbacks are registered
    CRMBridge.clear_listeners()

    # Executing crm methods should pass completely without marketing active
    lead = crm.lead_analyzer("cust_fallback", "普通问题")
    quote = crm.quote_generator("cust_fallback", 100.0, 5.0)
    refund = crm.refund_handler("cust_fallback", 50.0)

    assert lead is not None
    assert quote is not None
    assert refund is not None

def test_crm_bridge_registration_and_cleanup():
    """Verify that CRMBridge handles listener registration, duplicate prevention, and cleanup correctly."""
    triggered = []
    def dummy_callback(customer_id, data):
        triggered.append((customer_id, data))

    # Test registration and duplicate prevention
    CRMBridge.register_lead_listener(dummy_callback)
    CRMBridge.register_lead_listener(dummy_callback)  # Duplicate registration

    assert len(CRMBridge._lead_listeners) == 1

    CRMBridge.notify_lead_analyzed("cust_abc", {"val": 123})
    assert len(triggered) == 1
    assert triggered[0] == ("cust_abc", {"val": 123})

    # Test cleanup
    CRMBridge.clear_listeners()
    assert len(CRMBridge._lead_listeners) == 0
    assert len(CRMBridge._quote_listeners) == 0
    assert len(CRMBridge._refund_listeners) == 0
