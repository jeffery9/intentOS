# CRM Marketing Closed Loop Design Specification

This specification designs the integration of marketing campaigns with the CRM Pipeline application to form a closed-loop CRM cycle in IntentOS, adhering to Odoo-bridge-style physical isolation guidelines.

---

## 1. Architectural Overview

The CRM pipeline and Marketing pipeline operate as decoupled applications in separate namespaces. Communication is handled asynchronously via the `CRMBridge` class, which manages event callbacks without direct physical coupling or imports.

```
+--------------------------+
|    crm_pipeline (App)    |
|                          |
|  - lead_analyzer()       |
|  - quote_generator()     |
|  - refund_handler()      |
|                          |
+------------+-------------+
             | Triggers hooks
             v
+--------------------------+
|        CRMBridge         | (Bridge Broker)
+------------+-------------+
             | Dispatches callbacks
             v
+--------------------------+
| marketing_pipeline (App) |
|                          |
|  - retention_flow()      |
|  - vip_loyalty_flow()    |
|  - lead_nurture_flow()   |
|                          |
+--------------------------+
```

---

## 2. Directory Structure

The following directories and files will be created or modified:

```
intentos/
└── apps/
    ├── crm_pipeline/
    │   ├── app.py             # (Modified: trigger bridge hooks)
    │   └── bridge.py          # (New: Centralized CRMBridge broker)
    └── marketing_pipeline/
        ├── __init__.py        # (New: Export app creator and hooks)
        ├── manifest.yaml      # (New: Marketing app manifest)
        └── app.py             # (New: Marketing logic & campaign state)

tests/
└── unit/
    └── test_crm_marketing_bridge.py # (New: Closed-loop integration tests)
```

---

## 3. Component Details & Interface Specification

### A. Centralized Event Bridge (`intentos/apps/crm_pipeline/bridge.py`)

A decoupled broker that holds event callback listings for the CRM app events.

```python
class CRMBridge:
    _lead_listeners = []
    _quote_listeners = []
    _refund_listeners = []

    @classmethod
    def register_lead_listener(cls, callback):
        cls._lead_listeners.append(callback)

    @classmethod
    def register_quote_listener(cls, callback):
        cls._quote_listeners.append(callback)

    @classmethod
    def register_refund_listener(cls, callback):
        cls._refund_listeners.append(callback)

    @classmethod
    def notify_lead_analyzed(cls, customer_id, analysis_data):
        for cb in cls._lead_listeners:
            cb(customer_id, analysis_data)

    @classmethod
    def notify_quote_generated(cls, customer_id, quote_data):
        for cb in cls._quote_listeners:
            cb(customer_id, quote_data)

    @classmethod
    def notify_refund_requested(cls, customer_id, refund_data):
        for cb in cls._refund_listeners:
            cb(customer_id, refund_data)
```

### B. Marketing Pipeline Manifest (`intentos/apps/marketing_pipeline/manifest.yaml`)

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

### C. Marketing App State & Logic (`intentos/apps/marketing_pipeline/app.py`)

Handles three automated closed-loop campaign flows:

1. **Retention Flow (Angry Customers)**
   - **Trigger**: `anger_score > 0.8` or refund requested.
   - **Action**: Enrolls in "Win-Back Retention Program", generates voucher code `RET-COMP-<UUID>` offering **30.0% discount**.

2. **VIP Loyalty Flow (High-Value Customers)**
   - **Trigger**: Quote amount `final_price >= 1000.0`.
   - **Action**: Enrolls in "VIP Loyalty Program", generates voucher code `VIP-CLUB-<UUID>` with **$150.0 store credit**.

3. **Lead Nurture Flow (Warm Prospects)**
   - **Trigger**: Lead `score >= 60` with no quotes.
   - **Action**: Enrolls in "Lead Nurture Campaign", generates voucher code `NURTURE-WARM-<UUID>` offering **15.0% discount**.

---

## 4. Testing Strategy

The integration tests suite `test_crm_marketing_bridge.py` will assert:
- Successful hook registration and dispatch.
- Verification of Retention campaigns upon high anger messages and refund queries.
- Verification of VIP Loyalty campaign upon high value quotes.
- Verification of Lead Nurture campaign upon warm lead analyses.
- Graceful fallback: Removing or clearing callbacks leaves `crm_pipeline` running independently and error-free.
