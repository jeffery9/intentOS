# CRM & Marketing Closed Loop Pipeline Specification

This document details the architecture, capabilities, event flow, and integration testing of the decoupled, closed-loop CRM-Marketing workflow built on IntentOS.

---

## 1. Architectural Blueprint (Decoupled Event-Driven Routing)

The system adheres strictly to the Odoo-style Bridge Pattern. The core transactional logic of the CRM pipeline is kept completely isolated from the marketing campaign activation pathways.

```
┌──────────────────────────┐
│    crm_pipeline (App)    │
├──────────────────────────┤
│ - lead_analyzer()        │
│ - quote_generator()      │
│ - refund_handler()       │
└────────────┬─────────────┘
             │ triggers event hooks
             ▼
┌──────────────────────────┐
│        CRMBridge         │ (Central decoupled broker)
├──────────────────────────┤
│ - register_xxx_listener()│
│ - notify_xxx()           │
└────────────┬─────────────┘
             │ dispatches callback signals
             ▼
┌──────────────────────────┐
│ marketing_pipeline (App) │
├──────────────────────────┤
│ - on_lead_analyzed()     │
│ - on_quote_generated()   │
│ - on_refund_requested()  │
└──────────────────────────┘
```

---

## 2. Component Directory Structure

The integration is distributed across the following folders and components:

```
intentos/apps/
├── crm_pipeline/
│   ├── app.py             # Transactions, scoring, L4 gate checks
│   ├── bridge.py          # Centralized CRMBridge broker class
│   └── manifest.yaml      # CRM application metadata
└── marketing_pipeline/
    ├── __init__.py        # Factory creators and package exports
    ├── app.py             # Dynamic marketing loops & campaign logic
    └── manifest.yaml      # Marketing application metadata
```

---

## 3. Automated Closed-Loop Flows

The `marketing_pipeline` package automatically registers event hooks on `CRMBridge` upon instantiating. It implements three automated customer retention and loyalty programs:

### Flow A: Customer Win-Back Retention Program (Angry / Refund Triggers)
- **Condition**: 
  - `anger_score` evaluated in `lead_analyzer` is greater than `0.8`, OR
  - A refund request is initiated in `refund_handler`.
- **Campaign Action**: Immediately enrolls the customer into the *Win-Back Retention Program*.
- **Reward Generated**: Creates a localized 30% discount coupon code: `RET-COMP-<UUID>`.

### Flow B: VIP Loyalty Program (High-Value Purchases Trigger)
- **Condition**: 
  - final quoted price computed in `quote_generator` is greater than or equal to `$1,000.0`.
- **Campaign Action**: Enrolls the customer into the *VIP Loyalty Program*.
- **Reward Generated**: Credits the customer with `$150.0` store balance via voucher code: `VIP-CLUB-<UUID>`.

### Flow C: Warm Prospect Nurture Campaign (High-Score Leads Trigger)
- **Condition**:
  - lead quality score computed in `lead_analyzer` is greater than or equal to `60` (without high anger).
- **Campaign Action**: Enrolls the prospect into the *Lead Nurture Campaign*.
- **Reward Generated**: Issues a 15% discount promotional voucher code: `NURTURE-WARM-<UUID>`.

---

## 4. Operational Safety and Defensive Guidelines

1. **Duplicate Callback Avoidance**: `CRMBridge` utilizes membership assertions (`if callback not in cls._xxx_listeners`) during subscriber registration to completely eliminate duplicate side-effects.
2. **Preventing Memory Leaks**: All global event callback listings are fully flushed via `CRMBridge.clear_listeners()` class method during context shutdowns or test teardowns, avoiding strong reference leaks on instance objects.
3. **Graceful Fallback**: If the `marketing_pipeline` package is uninstalled or unmounted, the central `CRMBridge` listeners lists remain empty. The core `crm_pipeline` transactional endpoints will proceed with execution flawlessly, meeting strict business availability constraints.

---

## 5. Integration and State Teardown Testing

The integration correctness is rigorously verified under anyIO async execution models inside `tests/unit/test_crm_marketing_bridge.py`:

```python
# To run the complete suite:
/opt/homebrew/bin/python3 -m pytest tests/unit/test_crm_marketing_bridge.py -v
```

The tests assert and guarantee:
- Absolute isolation of campaign enrollments and states using a scoped pytest `clean_listeners` autouse fixture.
- Structural correctness of the `marketing_pipeline/manifest.yaml` via standard `IntentPackageLoader`.
- Validations of high anger trigger logic, high-value VIP thresholds, and prospect scoring bounds.
- Explicit verification of duplicate registration filtering and global event broker cleanup procedures.
