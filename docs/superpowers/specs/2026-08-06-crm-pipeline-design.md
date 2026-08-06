# CRM Verification Application Design Specification
Date: 2026-08-06
Topic: crm-pipeline

## 1. Overview
This design specification defines the architecture, data models, and execution flow for a customer relationship management (CRM) verification application ("CRM Pipeline") running natively on IntentOS. 

The application serves as a concrete verification of the IntentOS Layer 3 application layer, and specifically validates the **L4 Security Gate (Human-in-the-loop fallback)** in high-risk CRM situations (e.g., highly angry customers, large discounts, refund requests).

## 2. Architecture & Directory Layout
The application is structured as an Intent Package sibling under the core apps directory:

```
intentos/apps/crm_pipeline/
├── __init__.py           # Package exports and registry hooks
├── manifest.yaml         # Intent Package Spec compliant configuration
└── app.py                # Python model containing CRM state & Capability Handlers
```

### 2.1 Component Architecture (ASCII Diagram)

```
┌────────────────────────────────────────────────────────┐
│                   CRM Pipeline Flow                     │
│                                                        │
│  User Intent (NL)                                      │
│        │                                               │
│        ▼                                               │
│  L7/L6 Parse & Task Plan (IntentCompiler)              │
│        │                                               │
│        ▼                                               │
│  L5 Context Collection (Lead, Contact, Pipeline State) │
│        │                                               │
│        ▼                                               │
│  L4 Security Gate (CapabilityGate Evaluation)          │
│        ├────────────────────────────────────┐          │
│        │ [High Anger, Refund, Discount>20%] │          │
│        ▼                                    ▼          │
│   [Decision: ASK]                    [Decision: ALLOW] │
│        │                                    │          │
│        ├─► Generate Handoff Summary         │          │
│        │                                    │          │
│        ▼                                    ▼          │
│  Prompt for Confirmation             L3/L2 Execution   │
│                                             │          │
│                                             ▼          │
│                                      Update Pipeline   │
└────────────────────────────────────────────────────────┘
```

## 3. Package Specification (`manifest.yaml`)
The package configuration defines intents for analyzing leads, generating quotes, and requesting refunds, along with their mapped capability requirements:

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

## 4. Operational & Capability Model (`app.py`)
The class `CRMPipelineApp` acts as the execution agent and is responsible for managing CRM state and defining Python implementations for the package capabilities.

### 4.1 Internal State Representation
* **Pipeline State Store**: Memory storage containing customer logs, active quotes, lead scores, and communication logs.
* **Handoff Generation Engine**: Dynamically synthesizes an interactive handoff summary in ASCII structure:
  ```
  =========================================
  CRM HANDOFF SUMMARY (L4 Security Gate Trigger)
  =========================================
  Client ID   : [customer_id]
  Emotion     : [angry / disappointed]
  Anger Level : [0.0 - 1.0]
  Action      : [requested action]
  Context     : [prior communication log]
  -----------------------------------------
  Decision Required: Approve/Deny
  =========================================
  ```

### 4.2 Security Rules Implementation
* **Rule 1 (High Anger)**: Inside `lead_analyzer`, if the customer message contains highly angry words (anger score calculated > 0.8), the capability flags the action as requiring manual human-in-the-loop intervention.
* **Rule 2 (High Discount)**: Inside `quote_generator`, if the discount requested is strictly greater than 20%, it returns `requires_approval = True`.
* **Rule 3 (Refund)**: Inside `refund_handler`, any processed refund amount strictly triggers `requires_approval = True`.

Each capability hooks into the global `CapabilityGate` or simulates a gate check which transitions the current state to pending approval, generating the exact handoff summary context before executing.

## 5. Testing & Verification Plan
A dedicated test suite `tests/unit/test_crm_pipeline.py` will be created to verify functionality:
1. **Manifest Parsing Test**: Verify `IntentPackageLoader` successfully reads and parses the configuration.
2. **Package Registration Test**: Ensure the application is registered correctly in the `IntentPackageRegistry`.
3. **Safe Path Execution Test**: Confirm that normal customer inquires, standard quotes (<20% discount), and mild messages process completely without pausing.
4. **L4 Gate Interception Test**:
   * Confirm high anger level message triggers L4 confirmation.
   * Confirm high discount (>20%) triggers L4 confirmation.
   * Confirm any refund request triggers L4 confirmation.
5. **Handoff Summary Verification**: Assert that the generated handoff summary contains key customer variables (sentiment, action, context) and complies with the design parameters.
