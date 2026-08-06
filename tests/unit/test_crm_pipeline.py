# -*- coding: utf-8 -*-
"""
Unit tests for the CRM Pipeline Intent Package.
"""

from pathlib import Path
import pytest
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
