# PEF (Prompt Executable File) 格式规范 v2.0

> **人类可读 · 可编辑 · 可版本控制 · YAML/JSON 双格式支持**

## 概述

PEF v2.0 是 IntentOS 语义虚拟机的**可执行文件格式**，采用人类可读的 YAML/JSON 格式，
支持直接编辑、Git 版本控制和跨节点分发。

### 设计原则

1. **人类可读**: 纯文本格式，任何文本编辑器都可查看和编辑
2. **可版本控制**: 支持 Git diff、merge 和 blame
3. **向后兼容**: 支持 v1.0 PEF 格式自动迁移
4. **模块化**: 清晰的分段结构，每段职责明确
5. **可扩展**: 支持自定义元数据和约束

## 格式规范

### 文件扩展名

- `.pef.yaml` - YAML 格式（推荐用于编辑）
- `.pef.json` - JSON 格式（推荐用于程序生成）
- `.pef` - 默认扩展名（自动检测内容格式）

### 顶层结构

```yaml
# PEF Header
version: "2.0"                    # PEF 格式版本
id: "pef_20260405_143025_abc123" # 唯一标识符
compiled_at: "2026-04-05T14:30:25+08:00"

# 意图声明
intent:
  goal: "分析华东区 Q3 销售数据"
  description: "查询并分析华东区域第三季度的销售数据，生成趋势报告"
  output_format: "json"           # json | markdown | text

# 上下文绑定
context:
  user_id: "sales_manager"
  session_id: "sess_abc123"
  business_context:
    region: "华东"
    period: "Q3"
    year: 2024

# 能力绑定
capabilities:
  - name: "query_sales_data"
    version: ">=1.0"
    params:
      region: "${context.business_context.region}"
      period: "${context.business_context.period}"

# 约束条件
constraints:
  resource_limits:
    max_tokens: 4096
    timeout_seconds: 300
  execution:
    temperature: 0.0              # 确定性执行
    max_iterations: 10

# 工作流（可选）
workflow:
  steps:
    - id: "query"
      name: "查询销售数据"
      capability: "query_sales_data"
      output_var: "sales_data"
    
    - id: "analyze"
      name: "分析趋势"
      depends_on: ["query"]
      output_var: "analysis_result"

# 元数据
metadata:
  cache_key: "abc123def456"
  token_count: 1024
  tags: ["sales", "analysis", "q3"]
```

## 字段说明

### Header 段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | ✅ | PEF 格式版本，当前为 "2.0" |
| `id` | string | ✅ | 唯一标识符，格式：`pef_{timestamp}_{hash}` |
| `compiled_at` | string | ✅ | ISO 8601 时间戳 |

### Intent 段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `goal` | string | ✅ | 目标描述（自然语言） |
| `description` | string | ❌ | 详细说明 |
| `output_format` | string | ❌ | 输出格式，默认 "json" |

### Context 段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | string | ✅ | 用户标识 |
| `session_id` | string | ❌ | 会话标识 |
| `business_context` | object | ❌ | 业务上下文 |
| `technical_context` | object | ❌ | 技术上下文 |

### Capabilities 段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 能力名称 |
| `version` | string | ❌ | 版本约束，默认 "*" |
| `params` | object | ❌ | 参数绑定（支持变量替换） |

### Constraints 段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `resource_limits` | object | ❌ | 资源限制 |
| `execution` | object | ❌ | 执行参数 |

### Workflow 段（可选）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `steps` | array | ✅ | 工作流步骤 |
| `on_error` | array | ❌ | 错误处理策略 |

### Metadata 段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `cache_key` | string | ❌ | 缓存键 |
| `token_count` | int | ❌ | Token 估算数 |
| `tags` | array | ❌ | 标签列表 |

## 变量替换

PEF 支持参数化配置，使用 `${path}` 语法引用其他字段：

```yaml
context:
  region: "华东"

capabilities:
  - name: "query_sales_data"
    params:
      region: "${context.region}"  # 运行时替换为 "华东"
```

## 示例

### 简单查询

```yaml
version: "2.0"
id: "pef_20260405_143025_001"
compiled_at: "2026-04-05T14:30:25+08:00"

intent:
  goal: "查询今日订单数量"

context:
  user_id: "user_001"

capabilities:
  - name: "query_orders"
    params:
      date: "today"
```

### 复杂分析工作流

```yaml
version: "2.0"
id: "pef_20260405_143025_002"
compiled_at: "2026-04-05T14:30:25+08:00"

intent:
  goal: "分析华东区 Q3 销售数据并生成报告"
  description: "查询华东区域 Q3 销售数据，分析趋势，生成 Markdown 报告"
  output_format: "markdown"

context:
  user_id: "sales_manager"
  session_id: "sess_abc123"
  business_context:
    region: "华东"
    period: "Q3"
    year: 2024

capabilities:
  - name: "query_sales_data"
    params:
      region: "${context.business_context.region}"
      period: "${context.business_context.period}"
  
  - name: "analyze_trends"
    params:
      data: "${steps.query.output}"

workflow:
  steps:
    - id: "query"
      name: "查询销售数据"
      capability: "query_sales_data"
      output_var: "sales_data"
    
    - id: "analyze"
      name: "分析趋势"
      capability: "analyze_trends"
      depends_on: ["query"]
      output_var: "analysis_result"
    
    - id: "report"
      name: "生成报告"
      depends_on: ["analyze"]
      output_var: "final_report"

constraints:
  resource_limits:
    max_tokens: 8192
    timeout_seconds: 600
  execution:
    temperature: 0.3

metadata:
  tags: ["sales", "analysis", "q3", "华东"]
```

## 向后兼容

PEF v2.0 支持从 v1.0 格式自动迁移：

```python
from intentos.compiler import PEF

# v1.0 格式
v1_pef = PEF(
    version="1.0",
    intent="分析华东区 Q3 销售数据",
    system_prompt="...",
    user_prompt="请执行：分析华东区 Q3 销售数据",
    capabilities=["query_sales_data"],
)

# 转换为 v2.0 格式
v2_pef = PEF.from_v1(v1_pef)
```

## 验证规则

PEF 文件必须通过以下验证：

1. **必填字段**: `version`, `id`, `compiled_at`, `intent.goal`, `context.user_id`
2. **格式检查**: 时间戳必须符合 ISO 8601
3. **工作流验证**: 如果存在 workflow，步骤依赖必须有效
4. **能力绑定**: 能力名称不能为空

## 安全考虑

- PEF 文件不应包含敏感信息（API 密钥、密码等）
- 使用变量引用而非硬编码配置
- 支持数字签名（未来版本）
