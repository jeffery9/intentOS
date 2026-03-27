# 3 Layer / 7 Level 架构模型

> AI Native 应用体系结构划分为3 Layer，其中 IntentOS 又划分为7 Level。

---

## 1. 3 Layer 架构

AI Native 应用体系结构划分为三个层次：

| 层/级 | 名称 | 职责 | 类比传统计算 |
|------|------|------|-------------|
| **Layer 3** | **Application Layer** (应用层) | 领域意图包、业务能力、用户交互 | 应用程序 |
| **Layer 2** | **IntentOS Layer** (意图操作系统层) | 意图编译、调度、执行、记忆 | 操作系统 |
| **Layer 1** | **LLM Layer** (大语言模型层) | 语义理解、推理、生成 | CPU |

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 3: Application Layer                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Sales App  │  │  CRM App    │  │  BI App     │  ...    │
│  │  (意图包)    │  │  (意图包)    │  │  (意图包)    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└────────────────────────────┬────────────────────────────────┘
                             │ 意图调用
┌────────────────────────────▼────────────────────────────────┐
│                    Layer 2: IntentOS (7 Level)                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ [Level 7] 意图层 → 解析功能意图 + 操作意图                  │  │
│  │ [Level 6] 规划层 → 生成任务 DAG + Ops Model                 │  │
│  │ [Level 5] 上下文层 → 多模态事件图                           │  │
│  │ [Level 4] 安全环 → 权限校验 + Human-in-the-loop            │  │
│  │ [Level 3] 工具层 → 绑定能力调用                             │  │
│  │ [Level 2] 执行层 → 分布式调度执行                           │  │
│  │ [Level 1] 改进层 → 意图漂移检测 + 自动修复                  │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ Prompt 执行
┌────────────────────────────▼────────────────────────────────┐
│                    Layer 1: LLM Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   OpenAI    │  │  Anthropic  │  │   Ollama    │  ...    │
│  │  (语义 CPU)  │  │  (语义 CPU)  │  │  (语义 CPU)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 3: 应用层

### 2.1 职责

应用层是**面向用户的意图入口**，负责：

1. **领域意图包**: 封装特定业务领域的意图模板和能力
2. **用户交互**: 提供多模态交互界面（对话、图表、表单等）
3. **结果呈现**: 将执行结果渲染为用户友好的形式

### 2.2 应用组成

```yaml
# 应用定义示例 (CRM App)
app:
  name: "CRM"
  description: "客户关系管理意图包"
  
  # 意图模板
  intents:
    - query_customer: 查询客户信息
    - analyze_pipeline: 分析销售漏斗
    - generate_report: 生成周报
    
  # 能力注册
  capabilities:
    - customer_query: 客户查询 API
    - pipeline_analysis: 漏斗分析
    - report_generation: 报告生成
```

### 2.3 应用示例

```python
from intentos import create_app

crm_app = create_app(
    name="CRM",
    intents=[
        {"name": "query_customer", "description": "查询客户信息"},
        {"name": "analyze_pipeline", "description": "分析销售漏斗"},
    ],
    capabilities=[
        {"name": "customer_query", "endpoint": "https://api.crm.com/query"},
    ],
)
```

---

## 3. Layer 2: IntentOS (7 Level)

### 3.1 Level 7: 意图层 (Intent Level)

**职责**: 解析自然语言为结构化意图

**输入**: 自然语言  
**输出**: 结构化意图

```python
# 输入
"分析华东区 Q3 销售数据，对比去年同期"

# 输出
{
    "functional_intent": {
        "action": "analyze",
        "target": "sales_data",
        "parameters": {
            "region": "华东",
            "period": "Q3",
            "compare_with": "last_year"
        }
    },
    "operational_intent": {
        "slo": {"latency_p99_ms": 1000},
        "output_format": "dashboard"
    }
}
```

### 3.2 Level 6: 规划层 (Planning Level)

**职责**: 生成任务 DAG 和运维模型

**输入**: 结构化意图  
**输出**: 任务 DAG + Ops Model

```python
# 任务 DAG
{
    "tasks": [
        {"id": "t1", "capability": "query_sales"},
        {"id": "t2", "capability": "query_sales", "params": {"period": "last_year"}},
        {"id": "t3", "capability": "compare", "depends_on": ["t1", "t2"]},
        {"id": "t4", "capability": "render_dashboard", "depends_on": ["t3"]},
    ]
}
```

### 3.3 Level 5: 上下文层 (Context Level)

**职责**: 收集和管理多模态上下文

**输入**: 任务 DAG  
**输出**: enriched DAG with context

```python
{
    "user_context": {
        "user_id": "manager_001",
        "role": "sales_manager",
        "permissions": ["read_sales", "create_report"]
    },
    "business_context": {
        "domain": "sales",
        "fiscal_year": 2024,
    },
    "event_graph": [
        {"type": "metric", "source": "prometheus"},
        {"type": "log", "source": "elasticsearch"}
    ]
}
```

### 3.4 Level 4: 安全环 (Safety Level)

**职责**: 权限校验和人工审批

**输入**: enriched DAG  
**输出**: security-cleared DAG

```python
# 权限检查
if not context.has_permission("read_sales"):
    raise PermissionError("无权访问销售数据")

# 高风险操作需要审批
if operation in ["delete_data", "export_all"]:
    approval = await request_approval(user_id, operation)
```

### 3.5 Level 3: 工具层 (Tool Level)

**职责**: 能力绑定和协议适配

**输入**: security-cleared DAG  
**输出**: bound DAG with capabilities

```python
{
    "tasks": [
        {
            "capability": {
                "name": "query_sales",
                "endpoint": "https://api.sales.com/query",
                "protocol": "http",
                "fallback": ["query_sales_backup"]
            }
        }
    ]
}
```

### 3.6 Level 2: 执行层 (Execution Level)

**职责**: 分布式调度执行

**输入**: bound DAG  
**输出**: 执行结果

```python
results = await execute_dag(
    dag=bound_dag,
    mode="parallel",
    max_concurrency=10,
)
```

### 3.7 Level 1: 改进层 (Improvement Level)

**职责**: 意图漂移检测和自动修复

**输入**: 执行结果 + 预期  
**输出**: 改进建议

```python
# 意图漂移检测
if actual_result != expected_outcome:
    drift = detect_drift(actual_result, expected_outcome)
    
    # 自动修复
    if drift.type == "template_mismatch":
        await optimize_template(intent_template)
```

---

## 4. Layer 1: LLM 层

### 4.1 职责

LLM 层是**语义 CPU**，负责：

1. **语义理解**: 理解 Prompt 的含义
2. **推理生成**: 基于训练数据进行推理和生成
3. **Tool Calling**: 调用外部工具/API

### 4.2 支持的 LLM 后端

| 提供商 | 模型 | 特点 | 适用场景 |
|--------|------|------|---------|
| **OpenAI** | GPT-4o, GPT-4 | 通用能力强 | 复杂推理、代码生成 |
| **Anthropic** | Claude 3.5 | 长上下文、安全 | 文档分析、合规场景 |
| **Ollama** | Llama 3.1 | 本地部署、免费 | 隐私敏感、成本敏感 |

---

## 5. 层间交互

### 5.1 数据流

```
用户："分析华东区 Q3 销售"
    ↓
┌─────────────────────────────────────┐
│ App Layer                           │
│ • 接收输入                          │
│ • 调用 IntentOS.execute()           │
└───────────────┬─────────────────────┘
                ↓ Intent Call
┌───────────────▼─────────────────────┐
│ IntentOS (7 Level)                     │
│ L7: 解析 → {action: analyze, ...}   │
│ L6: 规划 → DAG + Ops Model          │
│ L5: 上下文 → enriched DAG           │
│ L4: 安全 → cleared DAG              │
│ L3: 绑定 → bound DAG                │
│ L2: 执行 → results                  │
│ L1: 改进 → feedback                 │
└───────────────┬─────────────────────┘
                ↓ Prompt
┌───────────────▼─────────────────────┐
│ LLM Layer                           │
│ • 理解 Prompt                        │
│ • 生成响应/调用工具                  │
└─────────────────────────────────────┘
```

---

## 6. 总结

3 Layer / 7 Level 架构的优势：

1. **职责清晰**: 每层有明确的职责边界
2. **可组合性**: 应用可组合多个意图包
3. **可演化性**: 各层可独立演进
4. **可观测性**: 每层可独立监控和调试

---

**下一篇**: [意图即元语言](02-intent-as-metalanguage.md)

**上一篇**: [文档索引](../README.md)
