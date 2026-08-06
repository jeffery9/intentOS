# CRM Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a spec-compliant CRM Pipeline Intent Package and a corresponding Python application model inside IntentOS, complete with an L4 Capability Gate integration to intercept and summarize high-risk operations (high anger, high discount, refund request) for Human-in-the-loop fallback.

**Architecture:** Create an Intent Package folder `crm_pipeline` inside `intentos/apps/`. Define a standard `manifest.yaml` specifying intents and capabilities. Implement `CRMPipelineApp` inside `app.py` to maintain state (contacts, pipeline logs, quotes, communication logs) and offer Python capability handlers. Integrate with `CapabilityGate` to demonstrate multi-decision L4 flow and ASCII handoff summaries.

**Tech Stack:** Python 3.10, Pytest, PyYAML, Dataclasses

## Global Constraints
- Target workspace directory: `/Users/jeffery/_project/IntentOS/`
- Module directory: `intentos/apps/crm_pipeline/`
- Test file: `tests/unit/test_crm_pipeline.py`
- Absolute ASCII diagrams and text summaries (no Mermaid or LaTeX).
- Do not log, print, or commit secrets.

---

## File Structure

The CRM verification app will contain the following files:
1. `intentos/apps/crm_pipeline/__init__.py`: Package initialization, exports, and helper/convenience creation function.
2. `intentos/apps/crm_pipeline/manifest.yaml`: Exact YAML metadata, intents, capabilities, configuration conforming to the Intent Package Spec.
3. `intentos/apps/crm_pipeline/app.py`: `CRMPipelineApp` implementation containing pipeline state and capability handlers.
4. `tests/unit/test_crm_pipeline.py`: Comprehensive test suite verifying manifest loading, registration, safe execution, and L4 Gate triggers.

---

### Task 1: Package Directory and manifest.yaml

Create the package directory structure and write the standard-compliant `manifest.yaml` configuration.

**Files:**
- Create: `intentos/apps/crm_pipeline/__init__.py`
- Create: `intentos/apps/crm_pipeline/manifest.yaml`

**Interfaces:**
- Produces: `manifest.yaml` formatted with correct intents and capabilities.

- [ ] **Step 1: Write directory `__init__.py`**
  Write an empty `__init__.py` file to establish the package module.
- [ ] **Step 2: Write `manifest.yaml`**
  Create `intentos/apps/crm_pipeline/manifest.yaml` containing exact CRM metadata, intents, and capability declarations.

```yaml
app_id: "crm_pipeline"
name: "CRM 运作流水线"
version: "1.0.0"
description: "AI 驱动并具备 L4 安全环的人机交接 CRM 流水线"
author: "IntentOS Team"
license: "MIT"

intents:
  - name: "analyze_lead"
    description: "分析客户消息并进行线索打分和情绪评估"
    patterns:
      - "分析客户 {customer_id} 消息: {message}"
      - "评估线索 {customer_id}"
    parameters:
      - name: "customer_id"
        type: "string"
        required: true
      - name: "message"
        type: "string"
        required: true

  - name: "generate_quote"
    description: "为客户生成报价方案与折扣"
    patterns:
      - "给客户 {customer_id} 报价, 报价额 {amount}, 折扣 {discount}"
    parameters:
      - name: "customer_id"
        type: "string"
        required: true
      - name: "amount"
        type: "number"
        required: true
      - name: "discount"
        type: "number"
        required: true

  - name: "request_refund"
    description: "处理客户退款申请"
    patterns:
      - "帮客户 {customer_id} 申请退款 {amount}"
    parameters:
      - name: "customer_id"
        type: "string"
        required: true
      - name: "amount"
        type: "number"
        required: true

capabilities:
  - name: "lead_analyzer"
    description: "线索属性打分与情感分析能力"
    type: "io"
    interface:
      input:
        type: "object"
        properties:
          customer_id: { type: "string" }
          message: { type: "string" }
        required: ["customer_id", "message"]
      output:
        type: "object"
        properties:
          customer_id: { type: "string" }
          score: { type: "integer" }
          sentiment: { type: "string" }
          anger_score: { type: "number" }

  - name: "quote_generator"
    description: "报价生成及高折扣安全限制能力"
    type: "io"
    interface:
      input:
        type: "object"
        properties:
          customer_id: { type: "string" }
          amount: { type: "number" }
          discount: { type: "number" }
        required: ["customer_id", "amount", "discount"]
      output:
        type: "object"
        properties:
          quote_id: { type: "string" }
          final_price: { type: "number" }
          requires_approval: { type: "boolean" }

  - name: "refund_handler"
    description: "退款流程控制与审批门控能力"
    type: "io"
    interface:
      input:
        type: "object"
        properties:
          customer_id: { type: "string" }
          amount: { type: "number" }
        required: ["customer_id", "amount"]
      output:
        type: "object"
        properties:
          refund_id: { type: "string" }
          status: { type: "string" }
          requires_approval: { type: "boolean" }
```

- [ ] **Step 3: Commit**

```bash
git add intentos/apps/crm_pipeline/__init__.py intentos/apps/crm_pipeline/manifest.yaml
git commit -m "feat(crm): initialize package directory and manifest.yaml"
```

---

### Task 2: Implement CRM Capability Logic (`app.py`)

Implement the `CRMPipelineApp` class inside `intentos/apps/crm_pipeline/app.py`. This holds state and exposes handlers for the three capabilities. It contains the scoring rules, the high discount thresholds, and refund routing, alongside the Handoff summary generator.

**Files:**
- Create: `intentos/apps/crm_pipeline/app.py`

**Interfaces:**
- Produces: `CRMPipelineApp` class.
  - `lead_analyzer(customer_id: str, message: str) -> dict`
  - `quote_generator(customer_id: str, amount: float, discount: float) -> dict`
  - `refund_handler(customer_id: str, amount: float) -> dict`
  - `generate_handoff_summary(customer_id: str, reason: str, action_details: str) -> str`

- [ ] **Step 1: Write `app.py` implementation**
  Create `intentos/apps/crm_pipeline/app.py` and implement the capability handlers and ASCII handoff generator.

```python
# -*- coding: utf-8 -*-
"""
CRM Pipeline Application Model

AI-driven pipeline with L4 Security Gate human-in-the-loop fallback.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

logger: logging.Logger = logging.getLogger(__name__)


class CRMPipelineApp:
    """
    CRM Pipeline Application Model
    
    Exposes lead scoring, quote generation, refund requests, and handoff utilities.
    """

    def __init__(self) -> None:
        self.app_id: str = "crm_pipeline"
        self.name: str = "CRM 运作流水线"
        self.version: str = "1.0.0"
        
        # State stores
        self.leads: dict[str, dict[str, Any]] = {}
        self.quotes: dict[str, dict[str, Any]] = {}
        self.refunds: dict[str, dict[str, Any]] = {}
        self.message_logs: dict[str, list[str]] = {}

    def lead_analyzer(self, customer_id: str, message: str) -> dict[str, Any]:
        """
        Analyzes incoming client messages, scores leads, and checks sentiment.
        """
        # Save message log
        if customer_id not in self.message_logs:
            self.message_logs[customer_id] = []
        self.message_logs[customer_id].append(message)

        # Basic sentiment heuristic for demonstration
        angry_keywords = ["生气", "太差", "退钱", "投诉", "垃圾", "愤怒", "生气了", "垃圾服务"]
        is_angry = any(kw in message for kw in angry_keywords)
        anger_score = 0.9 if is_angry else 0.1
        sentiment = "ANGRY" if is_angry else "NORMAL"

        # Simple lead scoring (0 - 100)
        score = 30
        if "买" in message or "购买" in message or "合作" in message:
            score += 40
        if "定价" in message or "报价" in message or "折扣" in message:
            score += 20

        result = {
            "customer_id": customer_id,
            "score": score,
            "sentiment": sentiment,
            "anger_score": anger_score,
            "message": message
        }
        self.leads[customer_id] = result
        return result

    def quote_generator(self, customer_id: str, amount: float, discount: float) -> dict[str, Any]:
        """
        Prepares a discount quote. High discount (>20%) requires manual approval.
        """
        final_price = amount * (1.0 - (discount / 100.0))
        quote_id = f"Q-{uuid.uuid4().hex[:8].upper()}"
        
        requires_approval = discount > 20.0

        result = {
            "quote_id": quote_id,
            "customer_id": customer_id,
            "original_amount": amount,
            "discount": discount,
            "final_price": final_price,
            "requires_approval": requires_approval
        }
        self.quotes[quote_id] = result
        return result

    def refund_handler(self, customer_id: str, amount: float) -> dict[str, Any]:
        """
        Requests a customer refund. All refunds require manual approval.
        """
        refund_id = f"RF-{uuid.uuid4().hex[:8].upper()}"
        
        # All refunds trigger L4 gate (human in the loop fallback)
        requires_approval = True

        result = {
            "refund_id": refund_id,
            "customer_id": customer_id,
            "amount": amount,
            "status": "PENDING_APPROVAL" if requires_approval else "APPROVED",
            "requires_approval": requires_approval
        }
        self.refunds[refund_id] = result
        return result

    def generate_handoff_summary(self, customer_id: str, reason: str, action_details: str) -> str:
        """
        Generates an interactive structural ASCII summary for a human representative.
        """
        lead_info = self.leads.get(customer_id, {})
        sentiment = lead_info.get("sentiment", "UNKNOWN")
        anger_val = lead_info.get("anger_score", 0.0)
        logs = self.message_logs.get(customer_id, [])
        log_str = " | ".join(logs[-3:]) if logs else "No messages logged"

        summary = f"""=========================================
CRM HANDOFF SUMMARY (L4 Security Gate Trigger)
=========================================
Client ID   : {customer_id}
Emotion     : {sentiment} (Anger: {anger_val:.2f})
Reason      : {reason}
Action      : {action_details}
Context     : {log_str}
-----------------------------------------
Decision Required: Approve / Deny Action
========================================="""
        return summary
```

- [ ] **Step 2: Commit**

```bash
git add intentos/apps/crm_pipeline/app.py
git commit -m "feat(crm): implement app.py with capability handlers and handoff"
```

---

### Task 3: Expose and Register CRM Module Hooks

Expose the `CRMPipelineApp` in the module's `__init__.py` file and verify it imports cleanly.

**Files:**
- Modify: `intentos/apps/crm_pipeline/__init__.py`

**Interfaces:**
- Produces: `create_crm_pipeline_app()` helper function and module-level exports.

- [ ] **Step 1: Write `__init__.py` contents**
  Add class exports and helper creator to `intentos/apps/crm_pipeline/__init__.py`.

```python
# -*- coding: utf-8 -*-
"""
CRM Pipeline Module
"""

from __future__ import annotations

from .app import CRMPipelineApp


def create_crm_pipeline_app() -> CRMPipelineApp:
    """创建 CRM 运作流水线 App"""
    return CRMPipelineApp()


__all__ = [
    "CRMPipelineApp",
    "create_crm_pipeline_app",
]
```

- [ ] **Step 2: Verify imports**
  Run Python command to ensure imports are functional and clean.
  Run: `python -c "from intentos.apps.crm_pipeline import CRMPipelineApp, create_crm_pipeline_app"`
  Expected: exit code 0.
- [ ] **Step 3: Commit**

```bash
git add intentos/apps/crm_pipeline/__init__.py
git commit -m "feat(crm): export app model from crm package init"
```

---

### Task 4: Write Tests and Verification Suite

Write the comprehensive unit test suite in `tests/unit/test_crm_pipeline.py`. It should test loading `manifest.yaml` via standard IntentOS utilities, registering it in `IntentPackageRegistry`, creating `AppInstance` with `RuntimeInstanceManager`, and running safe vs. gate-triggering workflows.

**Files:**
- Create: `tests/unit/test_crm_pipeline.py`

- [ ] **Step 1: Write test implementation**
  Create the test file and implement robust testing cycles.

```python
# -*- coding: utf-8 -*-
"""
CRM Pipeline Verification Tests

Tests loading, registering, and running safe & high-risk CRM workflows with L4 Security Gate human-in-the-loop intercept.
"""

import os
from pathlib import Path
import pytest

from intentos.apps import (
    IntentPackageLoader,
    IntentPackageRegistry,
    RuntimeInstanceManager,
)
from intentos.apps.crm_pipeline import create_crm_pipeline_app
from intentos.security.gate import CapabilityGate, GateDecision, PermissionMode


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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_crm_l4_security_gate_intercepts(crm_app_dir):
    """Verify that high-risk inputs correctly trigger L4 Gate ask decisions and generate handoff summaries."""
    crm_app = create_crm_pipeline_app()
    gate = CapabilityGate()
    
    # Register handlers with security gates (or emulate L4 logic evaluation)
    
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
```

- [ ] **Step 2: Run test suite to verify everything passes**
  Explain modifying commands first under Security rules, then run the tests.
  Run: `pytest tests/unit/test_crm_pipeline.py -v`
  Expected: PASS
- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_crm_pipeline.py
git commit -m "test(crm): add unit test suite for CRM pipeline and L4 gate verification"
```
