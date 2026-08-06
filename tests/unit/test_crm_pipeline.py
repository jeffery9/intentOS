# -*- coding: utf-8 -*-
"""
CRM Pipeline Verification Tests

Tests loading, registering, and running safe & high-risk CRM workflows with L4 Security Gate human-in-the-loop intercept.
"""

from pathlib import Path
import pytest

from intentos.apps import (
    IntentPackageLoader,
    IntentPackageRegistry,
    RuntimeInstanceManager,
)
from intentos.apps.crm_pipeline import create_crm_pipeline_app
from intentos.security.gate import CapabilityGate, GateDecision


@pytest.fixture
def anyio_backend():
    """AnyIO backend fixture for async tests."""
    return "asyncio"


@pytest.fixture
def crm_app_dir() -> str:
    """CRM application directory path."""
    return str(Path(__file__).parent.parent.parent / "intentos" / "apps" / "crm_pipeline")


def test_crm_manifest_loading(crm_app_dir):
    """Verify crm_pipeline manifest.yaml successfully compiles and validates."""
    loader = IntentPackageLoader()
    package = loader.load(crm_app_dir)

    assert package.app_id == "crm_pipeline"
    assert package.name == "CRM 运作流水线"
    assert package.version == "1.0.0"

    # Validate the 3 intents
    assert len(package.intents) == 3
    intent_names = {intent["name"] for intent in package.intents}
    assert intent_names == {"analyze_lead", "generate_quote", "request_refund"}

    # Validate the 3 capabilities
    assert len(package.capabilities) == 3
    capability_names = {cap["name"] for cap in package.capabilities}
    assert capability_names == {"lead_analyzer", "quote_generator", "refund_handler"}
    
    validation = loader.validate(package)
    assert validation.is_valid is True
    assert len(validation.errors) == 0


def test_crm_package_registration(crm_app_dir):
    """Verify package registry registers and indexes CRM capabilities."""
    loader = IntentPackageLoader()
    package = loader.load(crm_app_dir)

    registry = IntentPackageRegistry()
    registry.register(package)

    assert registry.get_package("crm_pipeline") == package
    assert registry.find_capability("lead_analyzer") == "crm_pipeline"
    assert registry.find_capability("quote_generator") == "crm_pipeline"
    assert registry.find_capability("refund_handler") == "crm_pipeline"


def test_crm_runtime_instance_management(crm_app_dir):
    """Verify creating AppInstance using RuntimeInstanceManager."""
    loader = IntentPackageLoader()
    package = loader.load(crm_app_dir)

    registry = IntentPackageRegistry()
    registry.register(package)

    manager = RuntimeInstanceManager(registry=registry)
    instance = manager.create_instance(app_id="crm_pipeline")

    assert instance is not None
    assert instance.app_id == "crm_pipeline"
    assert instance.package == package


@pytest.mark.anyio
async def test_crm_safe_execution_path(crm_app_dir):
    """Verify safe messages and normal quotes pass complete execution."""
    crm_app = create_crm_pipeline_app()
    
    # 1. Normal mild message
    lead_res = crm_app.lead_analyzer(
        customer_id="cust_1",
        message="你好，我想了解一下系统定价与折扣说明"
    )
    assert lead_res["sentiment"] == "NORMAL"
    assert lead_res["score"] == 50
    assert lead_res["anger_score"] <= 0.2

    # 2. Standard discount (15% discount is <= 20%)
    quote_res = crm_app.quote_generator(
        customer_id="cust_1",
        amount=1000.0,
        discount=15.0
    )
    assert quote_res["final_price"] == 850.0
    assert quote_res["requires_approval"] is False


@pytest.mark.anyio
async def test_crm_l4_security_gate_intercepts(crm_app_dir):
    """Verify that high-risk inputs correctly trigger L4 Gate ask decisions and generate handoff summaries."""
    crm_app = create_crm_pipeline_app()
    gate = CapabilityGate()
    
    # Context mockup
    context = {"permissions": ["crm:execute"]}

    # Scenario A: High Anger Client (Anger Score > 0.8)
    lead_res = crm_app.lead_analyzer(
        customer_id="cust_angry",
        message="你们的产品太差了！垃圾服务！我要退钱并投诉！"
    )
    assert lead_res["sentiment"] == "ANGRY"
    assert lead_res["anger_score"] > 0.8

    # High anger triggers need for human handoff summary
    reason_anger = "Highly Angry Customer Detected"
    action_details = "Automated support sequence"
    summary_anger = crm_app.generate_handoff_summary("cust_angry", reason_anger, action_details)
    
    assert "CRM HANDOFF SUMMARY" in summary_anger
    assert "Client ID   : cust_angry" in summary_anger
    assert "Emotion     : ANGRY" in summary_anger
    assert "Context     : 你们的产品太差了！垃圾服务！我要退钱并投诉！" in summary_anger

    # Simulate programmatic L4 capability gate evaluation
    gate_res_anger = await gate.evaluate(
        capability_id="lead_analyzer",
        context=context,
        input_data={"customer_id": "cust_angry", "message": lead_res["message"]}
    )
    # Programmatic gate assertion
    assert gate_res_anger.decision in [GateDecision.ALLOW, GateDecision.ASK]

    # Scenario B: High Discount (>20% Discount)
    quote_res = crm_app.quote_generator(
        customer_id="cust_angry",
        amount=5000.0,
        discount=30.0
    )
    assert quote_res["requires_approval"] is True
    
    summary_quote = crm_app.generate_handoff_summary(
        "cust_angry",
        "High Discount Request (>20%)",
        f"Generate Quote (original: $5000.0, discount: 30.0%, final: ${quote_res['final_price']})"
    )
    assert "Reason      : High Discount Request (>20%)" in summary_quote
    assert "final: $3500.0" in summary_quote

    # Programmatic check for quote generator capability evaluation
    gate_res_quote = await gate.evaluate(
        capability_id="quote_generator",
        context=context,
        input_data={"customer_id": "cust_angry", "amount": 5000.0, "discount": 30.0}
    )
    assert gate_res_quote.decision in [GateDecision.ALLOW, GateDecision.ASK]

    # Scenario C: Refund Request (Any amount)
    refund_res = crm_app.refund_handler(
        customer_id="cust_angry",
        amount=1200.0
    )
    assert refund_res["requires_approval"] is True
    
    summary_refund = crm_app.generate_handoff_summary(
        "cust_angry",
        "Refund Requested",
        f"Process Refund of $1200.0"
    )
    assert "Reason      : Refund Requested" in summary_refund
    assert "Process Refund of $1200.0" in summary_refund

    # Programmatic check for refund handler capability evaluation
    gate_res_refund = await gate.evaluate(
        capability_id="refund_handler",
        context=context,
        input_data={"customer_id": "cust_angry", "amount": 1200.0}
    )
    assert gate_res_refund.decision in [GateDecision.ALLOW, GateDecision.ASK]


def test_crm_defensive_bounds_checks():
    """Verify that CRM pipeline throws errors for invalid business parameter boundaries."""
    crm_app = create_crm_pipeline_app()

    # Negative amount quote
    with pytest.raises(ValueError, match="Invalid amount or discount bounds"):
        crm_app.quote_generator("cust_1", -100.0, 10.0)

    # Invalid bounds discount (>100%)
    with pytest.raises(ValueError, match="Invalid amount or discount bounds"):
        crm_app.quote_generator("cust_1", 500.0, 150.0)

    # Invalid bounds discount (<0%)
    with pytest.raises(ValueError, match="Invalid amount or discount bounds"):
        crm_app.quote_generator("cust_1", 500.0, -10.0)

    # Negative refund amount
    with pytest.raises(ValueError, match="Invalid refund amount"):
        crm_app.refund_handler("cust_1", -50.0)
