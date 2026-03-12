# PEF 规范：Prompt 可执行文件格式

> PEF (Prompt Executable Format) 是 IntentOS 的"可执行文件格式"，类似 ELF/PE，但采用 YAML/JSON 声明式。

---

## 1. 概述

### 1.1 什么是 PEF

**PEF (Prompt Executable Format)** 是 IntentOS 中 Prompt 的标准化格式，用于：

- 描述意图的完整执行计划
- 绑定能力和资源
- 定义 SLO 和安全策略
- 支持分布式执行

### 1.2 格式特点

| 特点 | 说明 |
|------|------|
| **声明式** | YAML/JSON 格式，人类可读 |
| **结构化** | 明确的段 (Section) 划分 |
| **可验证** | Schema 验证 |
| **可组合** | 支持引用和继承 |

---

## 2. PEF 结构

### 2.1 段 (Section) 定义

PEF 包含 8 个段：

| 段名 | 说明 | 必填 |
|------|------|------|
| `metadata` | 元数据 | 是 |
| `intent` | 意图声明 | 是 |
| `context` | 上下文 | 否 |
| `capabilities` | 能力绑定 | 否 |
| `constraints` | 约束条件 | 否 |
| `workflow` | 工作流 (DAG) | 否 |
| `ops_model` | 运维模型 | 否 |
| `safety` | 安全策略 | 否 |

### 2.2 结构图

```
┌─────────────────────────────────────────┐
│  metadata                               │
│  - version, name, execution_mode        │
├─────────────────────────────────────────┤
│  intent                                 │
│  - goal, intent_type, parameters        │
├─────────────────────────────────────────┤
│  context                                │
│  - user_id, event_graph                 │
├─────────────────────────────────────────┤
│  capabilities                           │
│  - name, protocol, endpoint             │
├─────────────────────────────────────────┤
│  constraints                            │
│  - resource_limits, compliance          │
├─────────────────────────────────────────┤
│  workflow                               │
│  - steps, on_error                      │
├─────────────────────────────────────────┤
│  ops_model                              │
│  - slo_targets, alert_rules             │
├─────────────────────────────────────────┤
│  safety                                 │
│  - level, approvers                     │
└─────────────────────────────────────────┘
```

---

## 3. 段详解

### 3.1 metadata 段

```yaml
metadata:
  version: "1.0.0"           # PEF 规范版本
  name: "sales_analysis"     # Prompt 名称
  description: "分析销售数据" # 描述
  author: "intentos"         # 作者
  created_at: "2024-01-01T00:00:00Z"
  modified_at: "2024-01-02T00:00:00Z"
  
  # 执行配置
  execution_mode: "dag"      # sequential | parallel | dag
  timeout_seconds: 300       # 超时时间
  retry_count: 3             # 重试次数
  priority: 5                # 优先级 (1-10)
  
  # 标签
  tags: ["sales", "analysis"]
```

### 3.2 intent 段

```yaml
intent:
  goal: "分析华东区 Q3 销售数据，对比去年同期"
  intent_type: "functional"    # functional | operational
  expected_outcome: "交互式分析报告"
  
  # 性能目标 (操作意图)
  performance_targets:
    latency_p99_ms: 100
    availability: 99.9
    error_rate: 0.001
  
  # 输入参数
  inputs:
    regions: ["华东"]
    period: "Q3"
    compare_with: "last_year"
  
  # 输出格式
  output_format: "interactive_dashboard"
```

### 3.3 context 段

```yaml
context:
  # 用户上下文
  user_id: "manager_001"
  user_role: "manager"
  session_id: "sess_123"
  
  # 业务上下文
  business_context:
    department: "sales"
    fiscal_year: 2024
  
  # 技术上下文
  technical_context:
    cluster: "prod-us-east-1"
    namespace: "default"
  
  # 多模态事件图
  event_graph:
    - type: "metric"
      source: "prometheus"
      query: "rate(http_requests_total[5m])"
    - type: "log"
      source: "elasticsearch"
      query: "level:ERROR service:order"
    - type: "trace"
      source: "jaeger"
      trace_id: "abc123"
```

### 3.4 capabilities 段

```yaml
capabilities:
  - name: "query_sales"
    version: "1.0"
    endpoint: "https://api.sales.com/query"
    protocol: "http"
    authentication:
      type: "bearer"
      token_ref: "SECRET_SALES_TOKEN"
    
    # LLM 特定配置
    llm_config:
      model: "gpt-4o"
      temperature: 0.7
      max_tokens: 2000
    
    # 降级策略
    fallback:
      - "query_sales_backup"
      - "query_sales_cache"
```

### 3.5 constraints 段

```yaml
constraints:
  # 资源约束
  resource_limits:
    max_tokens: 10000
    max_api_calls: 100
    budget_usd: 10.0
  
  # 时间约束
  time_constraints:
    deadline: "2024-12-31T23:59:59Z"
    business_hours_only: true
  
  # 合规约束
  compliance_rules:
    - "GDPR: no_pii_in_logs"
    - "SOC2: audit_all_actions"
```

### 3.6 workflow 段

```yaml
workflow:
  steps:
    - id: "step1"
      name: "查询华东销售"
      capability: "query_sales"
      params:
        region: "华东"
        period: "Q3"
      output_var: "east_data"
    
    - id: "step2"
      name: "查询去年同期"
      capability: "query_sales"
      params:
        region: "华东"
        period: "Q3_last_year"
      output_var: "east_last_year"
      depends_on: ["step1"]  # 依赖
    
    - id: "step3"
      name: "对比分析"
      capability: "compare"
      params:
        current: "${east_data}"
        previous: "${east_last_year}"
      output_var: "comparison"
      depends_on: ["step2"]
    
    - id: "step4"
      name: "生成仪表盘"
      capability: "render_dashboard"
      params:
        data: "${comparison}"
      depends_on: ["step3"]
  
  # 错误处理
  on_error:
    - action: "retry"
      max_attempts: 3
    - action: "notify"
      channel: "slack"
  
  # 成功条件
  success_condition: "all_steps_completed"
```

### 3.7 ops_model 段

```yaml
ops_model:
  # SLO 目标
  slo_targets:
    latency_p99_ms: 100
    availability_percent: 99.9
  
  # 监控指标
  metrics_to_collect:
    - "execution_duration"
    - "token_usage"
    - "api_call_count"
    - "cost_usd"
  
  # 告警规则
  alert_rules:
    - condition: "execution_duration > 30s"
      notify: "team-slack"
    - condition: "cost_usd > 10"
      notify: "finance-alert"
  
  # 自动修复策略
  auto_remediation:
    - trigger: "model_timeout"
      action: "switch_to_backup_model"
```

### 3.8 safety 段

```yaml
safety:
  # 安全等级
  level: "medium"  # low | medium | high | critical
  
  # 需要审批的操作
  requires_approval_for:
    - "delete_production_data"
    - "deploy_to_production"
  
  # 审批人
  approvers:
    - "tech_lead"
    - "oncall_manager"
  
  # 审批超时
  approval_timeout_minutes: 30
  
  # 审计配置
  audit_config:
    log_all_actions: true
    retention_days: 365
```

---

## 4. 完整示例

### 4.1 销售分析 PEF

```yaml
metadata:
  version: "1.0.0"
  name: "sales_analysis_q3"
  description: "分析 Q3 销售数据并生成报告"
  author: "intentos"
  tags: ["sales", "analysis", "report"]
  execution_mode: "dag"

intent:
  goal: "分析华东和华南区域 Q3 销售表现，对比去年同期"
  intent_type: "functional"
  expected_outcome: "交互式分析报告，包含异常检测和归因分析"
  inputs:
    regions: ["华东", "华南"]
    period: "Q3"
    compare_with: "last_year"
  output_format: "interactive_dashboard"

context:
  user_id: "sales_manager_001"
  user_role: "manager"
  business_context:
    department: "sales"
    fiscal_year: 2024

capabilities:
  - name: "query_sales_data"
    protocol: "http"
    endpoint: "https://api.example.com/sales"
  - name: "analyze_trends"
    protocol: "llm"
    llm_config:
      model: "gpt-4o"
      temperature: 0.3
  - name: "generate_dashboard"
    protocol: "http"
    endpoint: "https://api.example.com/dashboard"

workflow:
  steps:
    - id: "step1"
      name: "查询华东销售数据"
      capability: "query_sales_data"
      params:
        region: "华东"
        period: "Q3"
      output_var: "east_data"
    - id: "step2"
      name: "查询华南销售数据"
      capability: "query_sales_data"
      params:
        region: "华南"
        period: "Q3"
      output_var: "south_data"
      depends_on: ["step1"]
    - id: "step3"
      name: "分析趋势"
      capability: "analyze_trends"
      params:
        data: "${east_data} + ${south_data}"
      depends_on: ["step1", "step2"]
      output_var: "analysis"
    - id: "step4"
      name: "生成仪表盘"
      capability: "generate_dashboard"
      params:
        analysis: "${analysis}"
      depends_on: ["step3"]

ops_model:
  slo_targets:
    latency_p99_ms: 5000
    availability_percent: 99.5
  metrics_to_collect:
    - "execution_duration"
    - "token_usage"
  alert_rules:
    - condition: "execution_duration > 30s"
      notify: "team-slack"

safety:
  level: "medium"
  audit_config:
    log_all_actions: true
    retention_days: 90
```

### 4.2 JSON 格式

```json
{
  "metadata": {
    "version": "1.0.0",
    "name": "sales_analysis_q3",
    "execution_mode": "dag"
  },
  "intent": {
    "goal": "分析华东区 Q3 销售",
    "intent_type": "functional",
    "inputs": {
      "region": "华东",
      "period": "Q3"
    }
  },
  "workflow": {
    "steps": [
      {
        "id": "step1",
        "capability": "query_sales",
        "params": {"region": "华东"}
      }
    ]
  }
}
```

---

## 5. 验证

### 5.1 Schema 验证

```python
from intentos import PromptExecutable

# 从 YAML 加载
prompt = PromptExecutable.from_yaml(yaml_str)

# 验证
errors = prompt.validate()
if errors:
    print("验证失败:")
    for e in errors:
        print(f"  - {e}")
else:
    print("验证通过")
```

### 5.2 验证规则

| 规则 | 说明 |
|------|------|
| `metadata.name` 必填 | 必须有名称 |
| `intent.goal` 必填 | 必须有目标 |
| 工作流依赖必须存在 | 不能依赖不存在的步骤 |
| 关键安全等级需要审批人 | `critical` 级别必须有 approvers |

---

## 6. 总结

PEF 的核心价值：

1. **标准化**: 统一的 Prompt 格式
2. **可验证**: Schema 验证确保正确性
3. **可组合**: 支持引用和继承
4. **可执行**: 直接驱动 IntentOS 执行

---

**下一篇**: [代码生成](03-code-generation.md)

**上一篇**: [意图编译器架构](01-compiler-architecture.md)
