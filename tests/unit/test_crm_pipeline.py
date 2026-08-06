# -*- coding: utf-8 -*-
"""
Unit tests for the CRM Pipeline Intent Package.
"""

from pathlib import Path

from intentos.apps import IntentPackageLoader


def test_crm_pipeline_manifest_loading():
    """Verify that crm_pipeline manifest.yaml successfully compiles and validates."""
    app_dir = Path(__file__).parent.parent.parent / "intentos" / "apps" / "crm_pipeline"
    manifest_path = app_dir / "manifest.yaml"

    assert manifest_path.exists(), f"manifest.yaml should exist at {manifest_path}"

    loader = IntentPackageLoader()
    package = loader.load(str(app_dir))

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

    # Run standard validation
    result = loader.validate(package)
    assert result.is_valid is True, f"Manifest validation failed: {result.errors}"


def test_crm_pipeline_app_lead_analyzer():
    """Test lead analyzer functionality including scoring, sentiment, and logging."""
    from intentos.apps.crm_pipeline.app import CRMPipelineApp

    app = CRMPipelineApp()

    # Normal query
    res1 = app.lead_analyzer("cust1", "你好，我想咨询一下产品定价信息")
    assert res1["customer_id"] == "cust1"
    assert res1["score"] == 50  # 30 (base) + 20 (定价)
    assert res1["sentiment"] == "NORMAL"
    assert res1["anger_score"] == 0.1

    # Buying interest query
    res2 = app.lead_analyzer("cust2", "我想购买你们的软件，怎么合作？")
    assert res2["customer_id"] == "cust2"
    assert res2["score"] == 70  # 30 (base) + 40 (购买)
    assert res2["sentiment"] == "NORMAL"
    assert res2["anger_score"] == 0.1

    # Angry complaint query
    res3 = app.lead_analyzer("cust3", "你们的服务太差了，我要投诉退钱，真垃圾！")
    assert res3["customer_id"] == "cust3"
    assert res3["sentiment"] == "ANGRY"
    assert res3["anger_score"] == 0.9


def test_crm_pipeline_app_quote_generator():
    """Test quote generator pricing and manual approval trigger threshold."""
    from intentos.apps.crm_pipeline.app import CRMPipelineApp

    app = CRMPipelineApp()

    # Low discount (<= 20%)
    res1 = app.quote_generator("cust1", 1000.0, 15.0)
    assert res1["quote_id"].startswith("Q-")
    assert res1["customer_id"] == "cust1"
    assert res1["original_amount"] == 1000.0
    assert res1["discount"] == 15.0
    assert res1["final_price"] == 850.0
    assert res1["requires_approval"] is False

    # High discount (> 20%)
    res2 = app.quote_generator("cust2", 1000.0, 25.0)
    assert res2["requires_approval"] is True
    assert res2["final_price"] == 750.0


def test_crm_pipeline_app_refund_handler_and_handoff():
    """Test refund handling approval trigger and summary generation."""
    from intentos.apps.crm_pipeline.app import CRMPipelineApp

    app = CRMPipelineApp()

    # Set up messages for context
    app.lead_analyzer("cust1", "产品不好用")
    app.lead_analyzer("cust1", "退钱！")

    # Request refund
    refund_res = app.refund_handler("cust1", 500.0)
    assert refund_res["refund_id"].startswith("RF-")
    assert refund_res["customer_id"] == "cust1"
    assert refund_res["amount"] == 500.0
    assert refund_res["status"] == "PENDING_APPROVAL"
    assert refund_res["requires_approval"] is True

    # Generate summary
    summary = app.generate_handoff_summary("cust1", "退款审批申请", "需要人工审批退款额 $500.0")
    assert "CRM HANDOFF SUMMARY" in summary
    assert "Client ID   : cust1" in summary
    assert "Emotion     : ANGRY" in summary
    assert "Reason      : 退款审批申请" in summary
    assert "Action      : 需要人工审批退款额 $500.0" in summary
    assert "Context     : 产品不好用 | 退钱！" in summary


def test_crm_pipeline_imports_and_exports():
    """Verify that CRMPipelineApp and create_crm_pipeline_app are exported from the package init."""
    from intentos.apps.crm_pipeline import CRMPipelineApp as ExposedApp, create_crm_pipeline_app
    from intentos.apps.crm_pipeline.app import CRMPipelineApp as BaseApp

    assert ExposedApp is BaseApp

    app = create_crm_pipeline_app()
    assert isinstance(app, BaseApp)
    assert app.app_id == "crm_pipeline"


