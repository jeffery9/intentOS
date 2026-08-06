# CRM Marketing Closed Loop Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement an end-to-end, decoupled closed-loop CRM-Marketing cycle in IntentOS where customer actions (leads, high-value quotes, refund requests) automatically trigger retention, loyalty, and nurture marketing campaigns via an asynchronous event bridge.

**Architecture:** A separate `marketing_pipeline` package will listen to CRM event hooks routed through `CRMBridge`. This preserves complete architectural decoupling and enables clean, independent operation.

**Tech Stack:** Python 3, Pytest, AnyIO async framework, Pydantic.

## Global Constraints
- Target workspace directory: `/Users/jeffery/_project/IntentOS/`
- Module directories: `intentos/apps/crm_pipeline/` and `intentos/apps/marketing_pipeline/`
- Test file: `tests/unit/test_crm_marketing_bridge.py`
- Absolute ASCII diagrams and text summaries (no Mermaid or LaTeX).
- Do not log, print, or commit secrets.
- Use `/opt/homebrew/bin/python3` and standard AnyIO pytest-asyncio structures.

---

### Task 1: Create Centralized Event Bridge

**Files:**
- Create: `intentos/apps/crm_pipeline/bridge.py`
- Modify: `intentos/apps/crm_pipeline/__init__.py`

**Interfaces:**
- Produces: `CRMBridge` class with registration methods (`register_lead_listener`, `register_quote_listener`, `register_refund_listener`) and notify methods (`notify_lead_analyzed`, `notify_quote_generated`, `notify_refund_requested`).

- [ ] **Step 1: Write the failing test**

Open `tests/unit/test_crm_marketing_bridge.py` and write the test cases verifying bridge initialization and registering:

```python
# -*- coding: utf-8 -*-
import pytest
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: FAIL due to `ModuleNotFoundError: No module named 'intentos.apps.crm_pipeline.bridge'`

- [ ] **Step 3: Write minimal implementation**

Create `intentos/apps/crm_pipeline/bridge.py`:

```python
# -*- coding: utf-8 -*-
"""
CRM Event Bridge Broker
"""
from __future__ import annotations
from typing import Any, Callable

class CRMBridge:
    _lead_listeners: list[Callable[[str, dict[str, Any]], None]] = []
    _quote_listeners: list[Callable[[str, dict[str, Any]], None]] = []
    _refund_listeners: list[Callable[[str, dict[str, Any]], None]] = []

    @classmethod
    def register_lead_listener(cls, callback: Callable[[str, dict[str, Any]], None]) -> None:
        cls._lead_listeners.append(callback)

    @classmethod
    def register_quote_listener(cls, callback: Callable[[str, dict[str, Any]], None]) -> None:
        cls._quote_listeners.append(callback)

    @classmethod
    def register_refund_listener(cls, callback: Callable[[str, dict[str, Any]], None]) -> None:
        cls._refund_listeners.append(callback)

    @classmethod
    def notify_lead_analyzed(cls, customer_id: str, analysis_data: dict[str, Any]) -> None:
        for cb in cls._lead_listeners:
            cb(customer_id, analysis_data)

    @classmethod
    def notify_quote_generated(cls, customer_id: str, quote_data: dict[str, Any]) -> None:
        for cb in cls._quote_listeners:
            cb(customer_id, quote_data)

    @classmethod
    def notify_refund_requested(cls, customer_id: str, refund_data: dict[str, Any]) -> None:
        for cb in cls._refund_listeners:
            cb(customer_id, refund_data)
```

Expose it inside `intentos/apps/crm_pipeline/__init__.py`:

```python
# -*- coding: utf-8 -*-
"""
CRM Pipeline Module
"""
from __future__ import annotations
from .app import CRMPipelineApp
from .bridge import CRMBridge

def create_crm_pipeline_app() -> CRMPipelineApp:
    """创建 CRM 运作流水线 App"""
    return CRMPipelineApp()

__all__ = [
    "CRMPipelineApp",
    "create_crm_pipeline_app",
    "CRMBridge",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add intentos/apps/crm_pipeline/bridge.py intentos/apps/crm_pipeline/__init__.py tests/unit/test_crm_marketing_bridge.py
git commit -m "feat(crm): implement centralized decoupled CRMBridge event broker"
```

---

### Task 2: Trigger Bridge Hooks in CRM App

**Files:**
- Modify: `intentos/apps/crm_pipeline/app.py`

**Interfaces:**
- Consumes: `CRMBridge` notify endpoints from Task 1.

- [ ] **Step 1: Write the failing test**

Append a test inside `tests/unit/test_crm_marketing_bridge.py`:

```python
def test_crm_app_hook_triggers():
    from intentos.apps.crm_pipeline.app import CRMPipelineApp
    triggered_leads = []
    CRMBridge._lead_listeners.clear()
    CRMBridge.register_lead_listener(lambda cid, data: triggered_leads.append((cid, data)))

    app = CRMPipelineApp()
    app.lead_analyzer("cust_123", "我想咨询购买产品")

    assert len(triggered_leads) == 1
    assert triggered_leads[0][0] == "cust_123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: FAIL because CRM App does not notify CRMBridge.

- [ ] **Step 3: Write minimal implementation**

Import and call `CRMBridge` notify methods inside `intentos/apps/crm_pipeline/app.py` at the end of `lead_analyzer`, `quote_generator`, and `refund_handler`:

```python
        # In lead_analyzer:
        self.leads[customer_id] = result
        CRMBridge.notify_lead_analyzed(customer_id, result)
        return result

        # In quote_generator:
        self.quotes[quote_id] = result
        CRMBridge.notify_quote_generated(customer_id, result)
        return result

        # In refund_handler:
        self.refunds[refund_id] = result
        CRMBridge.notify_refund_requested(customer_id, result)
        return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add intentos/apps/crm_pipeline/app.py tests/unit/test_crm_marketing_bridge.py
git commit -m "feat(crm): trigger CRMBridge event notifications inside capability handlers"
```

---

### Task 3: Create Marketing Pipeline Package and manifest

**Files:**
- Create: `intentos/apps/marketing_pipeline/__init__.py`
- Create: `intentos/apps/marketing_pipeline/manifest.yaml`

**Interfaces:**
- Produces: `marketing_pipeline` package directory structure with standard `manifest.yaml`.

- [ ] **Step 1: Write the failing test**

Append test to `tests/unit/test_crm_marketing_bridge.py`:

```python
def test_marketing_manifest_loading():
    from pathlib import Path
    app_dir = Path(__file__).parent.parent.parent / "intentos" / "apps" / "marketing_pipeline"
    manifest_path = app_dir / "manifest.yaml"
    assert manifest_path.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: FAIL with `AssertionError: assert False` as manifest does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `intentos/apps/marketing_pipeline/manifest.yaml`:

```yaml
app_id: "marketing_pipeline"
name: "CRM 营销投放流水线"
version: "1.0.0"
description: "AI-driven closed-loop automated marketing campaign pipeline."
intents:
  - name: "enroll_campaign"
    description: "Enroll a customer manually in a marketing campaign"
capabilities:
  - name: "campaign_manager"
    description: "Manage enrollment, campaign status and voucher generation"
```

Create empty `intentos/apps/marketing_pipeline/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add intentos/apps/marketing_pipeline/
git commit -m "feat(marketing): initialize marketing pipeline package and manifest.yaml"
```

---

### Task 4: Implement Marketing App Logic

**Files:**
- Create: `intentos/apps/marketing_pipeline/app.py`
- Modify: `intentos/apps/marketing_pipeline/__init__.py`

**Interfaces:**
- Produces: `MarketingPipelineApp` and `create_marketing_pipeline_app()`.
- Logic: Registers CRMBridge listeners automatically. Enrolls clients in campaigns (Retention, VIP, Nurture) and creates voucher codes.

- [ ] **Step 1: Write the failing test**

Append test to `tests/unit/test_crm_marketing_bridge.py`:

```python
def test_marketing_app_auto_registration():
    from intentos.apps.marketing_pipeline import create_marketing_pipeline_app
    m_app = create_marketing_pipeline_app()
    assert len(CRMBridge._lead_listeners) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: FAIL because package export and creator don't exist.

- [ ] **Step 3: Write minimal implementation**

Create `intentos/apps/marketing_pipeline/app.py`:

```python
# -*- coding: utf-8 -*-
"""
Marketing Campaign Application Model
"""
from __future__ import annotations
import uuid
from typing import Any
from intentos.apps.crm_pipeline.bridge import CRMBridge

class MarketingPipelineApp:
    def __init__(self) -> None:
        self.app_id: str = "marketing_pipeline"
        self.name: str = "CRM 营销投放流水线"
        self.version: str = "1.0.0"

        # Campaign state: {customer_id: [campaign_records]}
        self.campaign_enrollments: dict[str, list[dict[str, Any]]] = {}

        # Auto-register event hook listeners
        CRMBridge.register_lead_listener(self.on_lead_analyzed)
        CRMBridge.register_quote_listener(self.on_quote_generated)
        CRMBridge.register_refund_listener(self.on_refund_requested)

    def enroll_campaign(self, customer_id: str, campaign_name: str, voucher_prefix: str, discount_rate: float = 0.0, credit: float = 0.0) -> dict[str, Any]:
        """Helper to create campaign enrollment and voucher code."""
        voucher = f"{voucher_prefix}-{uuid.uuid4().hex[:8].upper()}"
        record = {
            "campaign_name": campaign_name,
            "voucher_code": voucher,
            "discount_rate": discount_rate,
            "credit": credit,
            "status": "ACTIVE"
        }
        if customer_id not in self.campaign_enrollments:
            self.campaign_enrollments[customer_id] = []
        self.campaign_enrollments[customer_id].append(record)
        return record

    def on_lead_analyzed(self, customer_id: str, lead_data: dict[str, Any]) -> None:
        """Processes lead analysis. Triggers Retention or Nurture flows."""
        # Flow 1: High Anger (anger_score > 0.8)
        if lead_data.get("anger_score", 0.0) > 0.8:
            self.enroll_campaign(customer_id, "Win-Back Retention Program", "RET-COMP", discount_rate=30.0)
        # Flow 3: Warm prospects (score >= 60, not angry)
        elif lead_data.get("score", 0) >= 60:
            self.enroll_campaign(customer_id, "Lead Nurture Campaign", "NURTURE-WARM", discount_rate=15.0)

    def on_quote_generated(self, customer_id: str, quote_data: dict[str, Any]) -> None:
        """Processes quote events. Triggers VIP loyalty flow if final_price >= 1000."""
        # Flow 2: VIP loyalty (final_price >= 1000.0)
        if quote_data.get("final_price", 0.0) >= 1000.0:
            self.enroll_campaign(customer_id, "VIP Loyalty Program", "VIP-CLUB", credit=150.0)

    def on_refund_requested(self, customer_id: str, refund_data: dict[str, Any]) -> None:
        """Processes refund requests. Triggers Retention win-back immediately."""
        self.enroll_campaign(customer_id, "Win-Back Retention Program", "RET-COMP", discount_rate=30.0)
```

Export creator in `intentos/apps/marketing_pipeline/__init__.py`:

```python
# -*- coding: utf-8 -*-
"""
Marketing Pipeline Module
"""
from __future__ import annotations
from .app import MarketingPipelineApp

def create_marketing_pipeline_app() -> MarketingPipelineApp:
    """创建 Marketing App 实例"""
    return MarketingPipelineApp()

__all__ = [
    "MarketingPipelineApp",
    "create_marketing_pipeline_app",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add intentos/apps/marketing_pipeline/app.py intentos/apps/marketing_pipeline/__init__.py tests/unit/test_crm_marketing_bridge.py
git commit -m "feat(marketing): implement MarketingPipelineApp campaign logic and automatic hook registrations"
```

---

### Task 5: Write and Execute Closed-Loop Integration Tests

**Files:**
- Modify: `tests/unit/test_crm_marketing_bridge.py`

**Interfaces:**
- Consumes: Both `crm_pipeline` and `marketing_pipeline` modules.

- [ ] **Step 1: Write the failing test**

Consolidate `tests/unit/test_crm_marketing_bridge.py` into a robust test suite checking full lifecycle scenarios:

```python
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
    CRMBridge._lead_listeners.clear()
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
    CRMBridge._quote_listeners.clear()
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
    CRMBridge._lead_listeners.clear()
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
    CRMBridge._lead_listeners.clear()
    CRMBridge._quote_listeners.clear()
    CRMBridge._refund_listeners.clear()

    # Executing crm methods should pass completely without marketing active
    lead = crm.lead_analyzer("cust_fallback", "普通问题")
    quote = crm.quote_generator("cust_fallback", 100.0, 5.0)
    refund = crm.refund_handler("cust_fallback", 50.0)

    assert lead is not None
    assert quote is not None
    assert refund is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: FAIL if some triggers/logic are wrong or imports are misaligned.

- [ ] **Step 3: Write minimal implementation**

Adjust any imports, lists, or logic to ensure all test assertions cleanly pass.

- [ ] **Step 4: Run test to verify it passes**

Run: `/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v`
Expected: PASS with 100% success (5/5 tests passing).

- [ ] **Step 5: Commit**

```bash
git add tests/unit/test_crm_marketing_bridge.py
git commit -m "test(marketing): consolidate end-to-end closed-loop CRM-Marketing integration tests"
```
