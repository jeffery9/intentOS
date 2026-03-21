# 意图包格式规范

> **标准化 · 可移植 · 易扩展**

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: Release Candidate

---

## 一、概述

### 1.1 什么是意图包？

**意图包 (Intent Package)** 是 AI Native App 的基本单位，包含：

- **意图定义** - 应用能做什么
- **能力定义** - 如何执行
- **计费规则** - 如何收费
- **资源配置** - 需要什么资源

### 1.2 意图包结构

```
my-app/
├── SKILL.md                    # 元数据和规范 (必需)
├── manifest.yaml               # 意图包清单 (必需)
├── intents/                    # 意图模板目录 (必需)
│   ├── analyze.yaml
│   ├── report.yaml
│   └── query.yaml
├── capabilities/               # 能力定义目录 (必需)
│   ├── data_loader.py
│   ├── analyzer.py
│   └── reporter.py
├── pricing/                    # 计费规则目录 (必需)
│   └── rules.yaml
├── resources/                  # 资源文件目录 (可选)
│   ├── prompts/               # Prompt 模板
│   │   ├── system.txt
│   │   └── user.txt
│   └── templates/             # 输出模板
│       └── report.md.jinja
├── tests/                      # 测试用例目录 (推荐)
│   ├── test_intents.py
│   └── test_capabilities.py
└── README.md                   # 使用说明 (推荐)
```

---

## 二、SKILL.md 格式

### 2.1 基本结构

```markdown
---
name: <应用名称>
version: <语义化版本号>
description: <应用描述，限 200 字>
author: <开发者名称>
email: <开发者邮箱>
license: <许可证类型>
category: <应用分类>
tags: [<标签 1>, <标签 2>, ...]
icon: <emoji 图标>
homepage: <项目主页 URL>
repository: <代码仓库 URL>
---

# {应用名称}

## 应用描述

详细描述应用的功能、用途和特点。

## 功能特性

- 功能 1
- 功能 2
- 功能 3

## 何时使用

- 使用场景 1
- 使用场景 2
- 使用场景 3

## 计费说明

说明应用的计费方式和价格。

## 使用示例

提供 1-2 个使用示例。

## 资源

### Scripts
- `scripts/main.py`

### References
- `references/docs.md`
```

### 2.2 示例

```markdown
---
name: data_analyst
version: 1.0.0
description: 数据分析助手，用自然语言分析数据
author: IntentOS Team
email: team@intentos.io
license: MIT
category: analytics
tags: ["数据分析", "商业智能", "报告生成"]
icon: 📊
homepage: https://intentos.io/apps/data_analyst
repository: https://github.com/intentos/data_analyst
---

# 数据分析助手

## 应用描述

数据分析助手是一个强大的 AI Native 应用，允许用户通过自然语言进行数据分析。
无需编写 SQL 或代码，只需描述分析需求，即可生成洞察和报告。

## 功能特性

- 📊 自然语言数据分析
- 📈 自动生成可视化图表
- 📝 智能洞察和建议
- 📑 多格式报告导出

## 何时使用

- 销售数据分析
- 市场趋势分析
- 运营报告生成
- 业务洞察发现

## 计费说明

- 按分析时长计费：$0.10/分钟
- 首次使用免费 1 分钟

## 使用示例

```
用户：分析华东区 Q3 销售数据

助手：分析完成

关键洞察:
1. Q3 销售额：$12.5M (环比 +15%, 同比 +28%)
2. Top 产品：产品 A (占比 35%, 增长最快 +42%)
3. 区域表现：浙江 (+28%) > 江苏 (+18%) > 上海 (+12%)

💰 服务费用：$0.15 (执行 1.5 分钟)
```

## 资源

### Scripts
- `capabilities/data_loader.py`
- `capabilities/analyzer.py`
- `capabilities/reporter.py`
```

---

## 三、manifest.yaml 完整 Schema

### 3.1 基本信息

```yaml
# manifest.yaml - 意图包清单
schema_version: "1.0"  # Schema 版本

# 基本信息
app:
  id: "io.intentos.data_analyst"  # 唯一标识符 (reverse.domain.app_name)
  name: "数据分析助手"
  version: "1.0.0"                 # 语义化版本
  description: "用自然语言分析数据"
  author: "IntentOS Team"
  license: "MIT"

# 分类和标签
category:
  primary: "analytics"             # 主分类
  secondary: ["business_intelligence"]  # 次分类（可选）
tags:
  - "数据分析"
  - "商业智能"
  - "报告生成"

# 图标和展示
display:
  icon: "📊"
  color: "#4A90D9"                 # 主题色
  screenshots:                     # 截图（可选）
    - "screenshots/demo1.png"
    - "screenshots/demo2.png"
```

### 3.2 意图定义

```yaml
# 意图定义
intents:
  - id: "data_analysis"
    name: "数据分析"
    description: "分析数据并生成洞察"
    patterns:                      # 意图匹配模式
      - "分析.*数据"
      - "帮我看看.*销售情况"
      - "生成.*报告"
    parameters:                    # 参数定义（可选）
      - name: "data_source"
        type: "string"
        required: true
        description: "数据源路径"
      - name: "time_range"
        type: "object"
        required: false
        properties:
          start: { type: "string", format: "date" }
          end: { type: "string", format: "date" }
    required_capabilities:         # 需要的能力
      - "data_loader"
      - "analyzer"
      - "reporter"
    pricing:                       # 计费规则
      model: "pay_per_use"
      unit: "minute"
      price_per_unit: 0.10
      minimum_charge: 0.01
    output:                        # 输出格式
      type: "markdown"
      sections:
        - summary
        - insights
        - recommendations
    timeout: 300                   # 超时时间（秒）
    retry:                         # 重试配置（可选）
      max_attempts: 3
      backoff: "exponential"
```

### 3.3 能力定义

```yaml
# 能力定义
capabilities:
  - id: "data_loader"
    name: "数据加载"
    description: "从文件/数据库加载数据"
    source: "builtin"              # builtin/mcp/skill/external
    entry_point: "capabilities.data_loader:load_data"
    parameters:
      - name: "path"
        type: "string"
        required: true
    returns:
      type: "object"
      properties:
        data: { type: "array" }
        metadata: { type: "object" }
    pricing:
      model: "free"
    rate_limit:                    # 速率限制（可选）
      requests_per_minute: 60
      requests_per_day: 10000

  - id: "weather_api"
    name: "天气查询"
    description: "查询实时天气"
    source: "mcp"
    mcp_server: "weather"
    mcp_method: "get_current_weather"
    pricing:
      model: "pay_per_call"
      price_per_call: 0.01
```

### 3.4 依赖项

```yaml
# 依赖项
dependencies:
  intentos: ">=12.0.0"             # IntentOS 版本要求
  python: ">=3.10"                 # Python 版本要求
  packages:                        # Python 依赖包
    - "pandas>=2.0"
    - "numpy>=1.24"
```

### 3.5 权限声明

```yaml
# 权限声明
permissions:
  - "file:read"                    # 文件读取
  - "file:write"                   # 文件写入
  - "network:api_call"             # API 调用
  - "memory:store"                 # 记忆存储
```

### 3.6 配置项

```yaml
# 配置项
config:
  defaults:
    max_data_size: 10000           # 最大数据量
    cache_enabled: true            # 启用缓存
    cache_ttl: 3600                # 缓存 TTL（秒）

# 环境变量
env:
  - name: "DATA_API_KEY"
    description: "数据 API 密钥"
    required: true
  - name: "CACHE_SIZE"
    description: "缓存大小 (MB)"
    required: false
    default: "100"
```

### 3.7 计量和计费

```yaml
# 计量和计费
metering:
  enabled: true
  metrics:
    - name: "cpu_time"
      unit: "millisecond"
    - name: "tokens"
      unit: "count"
    - name: "execution_time"
      unit: "second"
    - name: "memory"
      unit: "megabyte"

# 收益分成
revenue_share:
  developer: 0.80    # 开发者 80%
  platform: 0.15     # 平台 15%
  referrer: 0.05     # 推荐者 5%
```

### 3.8 发布配置

```yaml
# 发布配置
publish:
  visibility: "public"             # public/private/unlisted
  regions: ["global"]              # 发布区域
  approval_required: true          # 需要审核
```

---

## 四、意图模板详细格式

### 4.1 意图匹配

```yaml
# intents/analyze.yaml
---
id: "data_analysis"
name: "数据分析"
description: "分析数据并生成业务洞察"
version: "1.0.0"

# 意图匹配
matching:
  patterns:
    - regex: "分析.*数据"
      priority: 100
    - regex: "帮我看看.*销售情况"
      priority: 90
    - regex: "生成.*报告"
      priority: 80
    - keyword: ["分析", "数据", "报告", "洞察"]
      priority: 50
  examples:  # 训练示例（用于意图识别模型）
    - "分析华东区 Q3 销售数据"
    - "帮我看看上个月的销售情况"
    - "生成一份业绩报告"
```

### 4.2 参数定义

```yaml
# 参数定义
parameters:
  - name: "data_source"
    type: "string"
    required: true
    description: "数据源路径或连接字符串"
    validation:
      pattern: "^(file://|db://|s3://).+"
      error_message: "无效的数据源格式"
    extraction:
      patterns:
        - "分析 (.+) 的数据"
        - "从 (.+) 分析"

  - name: "metrics"
    type: "array"
    required: false
    description: "要分析的指标"
    default: ["revenue", "volume", "growth"]
    items:
      type: "string"
      enum: ["revenue", "volume", "growth", "profit", "cost"]

  - name: "time_range"
    type: "object"
    required: false
    properties:
      start:
        type: "string"
        format: "date"
      end:
        type: "string"
        format: "date"
      granularity:
        type: "string"
        enum: ["daily", "weekly", "monthly", "quarterly", "yearly"]
        default: "monthly"
```

### 4.3 执行计划

```yaml
# 执行计划（DAG 形式）
execution:
  steps:
    - id: "load_data"
      capability: "data_loader"
      input:
        path: "${parameters.data_source}"
      output:
        variable: "raw_data"

    - id: "validate_data"
      capability: "data_validator"
      input:
        data: "${raw_data}"
      output:
        variable: "validated_data"
      condition: "${raw_data.length} > 0"

    - id: "analyze"
      capability: "analyzer"
      input:
        data: "${validated_data}"
        metrics: "${parameters.metrics}"
      output:
        variable: "analysis_result"

    - id: "generate_report"
      capability: "reporter"
      input:
        analysis: "${analysis_result}"
        template: "resources/templates/report.md.jinja"
      output:
        variable: "final_report"

  # 错误处理
  error_handling:
    on_error: "rollback"
    fallback:
      - id: "fallback_report"
        capability: "simple_reporter"
        input:
          message: "分析失败，返回基础报告"

  # 超时和重试
  timeout: 300
  retry:
    max_attempts: 3
    backoff: "exponential"
    retry_on:
      - "timeout"
      - "rate_limit"
```

### 4.4 输出定义

```yaml
# 输出定义
output:
  format: "markdown"
  schema:
    type: "object"
    properties:
      summary:
        type: "string"
        description: "分析摘要"
      insights:
        type: "array"
        items:
          type: "object"
          properties:
            title: { type: "string" }
            description: { type: "string" }
            confidence: { type: "number", min: 0, max: 1 }
      recommendations:
        type: "array"
        items: { type: "string" }
      charts:
        type: "array"
        items:
          type: "object"
          properties:
            type: { type: "string", enum: ["bar", "line", "pie", "scatter"] }
            data: { type: "object" }
            config: { type: "object" }

  # 输出模板
  template: |
    # 数据分析报告

    ## 摘要
    {{ summary }}

    ## 关键洞察
    {% for insight in insights %}
    ### {{ insight.title }}
    {{ insight.description }}
    (置信度：{{ (insight.confidence * 100)|round }}%)
    {% endfor %}

    ## 建议
    {% for rec in recommendations %}
    - {{ rec }}
    {% endfor %}
```

### 4.5 计费规则

```yaml
# 计费规则
pricing:
  model: "pay_per_use"
  currency: "USD"
  
  # 计费维度
  dimensions:
    - name: "execution_time"
      unit: "minute"
      rate: 0.10
    - name: "data_volume"
      unit: "1000_rows"
      rate: 0.05
    - name: "llm_tokens"
      unit: "1000_tokens"
      rate: 0.02

  # 最低收费
  minimum_charge: 0.01
  
  # 免费额度
  free_quota:
    execution_time: 1  # 1 分钟免费
    requests: 1        # 首次免费

  # 套餐折扣
  discounts:
    - condition: "monthly_requests >= 100"
      discount: 0.10   # 10% 折扣
    - condition: "monthly_requests >= 1000"
      discount: 0.20   # 20% 折扣
```

### 4.6 监控和日志

```yaml
# 监控和日志
monitoring:
  metrics:
    - "execution_time"
    - "success_rate"
    - "error_rate"
    - "avg_cost_per_request"
  logging:
    level: "INFO"
    include_input: true
    include_output: true
    mask_sensitive_data: true
```

### 4.7 安全配置

```yaml
# 安全配置
security:
  input_validation:
    max_input_length: 10000
    allowed_file_types: [".csv", ".xlsx", ".json"]
    max_file_size: "10MB"
  data_protection:
    encrypt_at_rest: true
    encrypt_in_transit: true
    data_retention_days: 30
  access_control:
    require_auth: true
    allowed_roles: ["user", "admin"]
```

---

## 五、能力定义详细格式

### 5.1 能力定义

```yaml
# capabilities/data_loader.yaml
---
id: "data_loader"
name: "数据加载器"
description: "从多种数据源加载数据"
version: "1.0.0"

# 能力类型
type: "builtin"  # builtin/mcp/skill/external

# 入口点
entry_point:
  module: "capabilities.data_loader"
  function: "load_data"
  class: null  # 如果是类方法

# 参数定义
parameters:
  - name: "path"
    type: "string"
    required: true
    description: "数据源路径"
    validation:
      pattern: "^(file://|db://|s3://|https://).+"
    
  - name: "format"
    type: "string"
    required: false
    description: "数据格式"
    enum: ["csv", "json", "parquet", "excel", "auto"]
    default: "auto"

  - name: "options"
    type: "object"
    required: false
    description: "加载选项"
    properties:
      encoding:
        type: "string"
        default: "utf-8"
      chunk_size:
        type: "integer"
        default: 10000
      columns:
        type: "array"
        items: { type: "string" }

# 返回值定义
returns:
  type: "object"
  properties:
    success: { type: "boolean" }
    data:
      type: "array"
      items: { type: "object" }
    metadata:
      type: "object"
      properties:
        row_count: { type: "integer" }
        column_count: { type: "integer" }
        file_size: { type: "integer" }
        load_time_ms: { type: "integer" }
    error:
      type: "string"
      nullable: true

# 错误定义
errors:
  - code: "FILE_NOT_FOUND"
    message: "文件不存在"
    http_status: 404
    
  - code: "INVALID_FORMAT"
    message: "不支持的文件格式"
    http_status: 400
    
  - code: "PERMISSION_DENIED"
    message: "没有访问权限"
    http_status: 403

# 性能特性
performance:
  avg_execution_time_ms: 100
  p95_execution_time_ms: 500
  p99_execution_time_ms: 1000
  max_concurrent_calls: 100

# 资源需求
resources:
  memory_mb: 256
  cpu_cores: 0.5
  disk_mb: 100

# 依赖
dependencies:
  packages:
    - "pandas>=2.0"
    - "pyarrow>=10.0"
  services: []

# 测试配置
testing:
  unit_tests:
    - name: "test_csv_load"
      input:
        path: "file://test_data.csv"
      expected:
        success: true
        metadata:
          row_count: 100
          
  integration_tests:
    - name: "test_s3_load"
      input:
        path: "s3://bucket/data.parquet"
      expected:
        success: true

# 文档
documentation:
  usage_examples:
    - description: "加载 CSV 文件"
      code: |
        result = await load_data(path="file://data.csv")
        
    - description: "加载 S3 数据"
      code: |
        result = await load_data(
            path="s3://bucket/data.parquet",
            options={"chunk_size": 5000}
        )
  
  faq:
    - question: "支持哪些文件格式？"
      answer: "支持 CSV、JSON、Parquet、Excel 等格式"
      
    - question: "最大支持多大的文件？"
      answer: "单文件最大支持 1GB，大文件建议使用分块加载"
```

---

## 六、验证工具

### 6.1 验证命令

```bash
# 验证意图包
intentos package validate ./my_app

# 输出
✓ SKILL.md 格式正确
✓ manifest.yaml Schema 验证通过
✓ 意图模板验证通过
✓ 能力定义验证通过
✓ 计费规则验证通过
✓ 所有文件完整

验证通过！意图包可以发布。
```

### 6.2 常见错误

```bash
# 错误 1: 缺少必需文件
✗ manifest.yaml 不存在

# 错误 2: Schema 验证失败
✗ intents[0].pricing.model 必须是以下值之一：pay_per_use, subscription, quota

# 错误 3: 能力引用不存在
✗ intent "data_analysis" 引用了不存在的能力 "non_existent_cap"

# 错误 4: 循环依赖
✗ 检测到循环依赖：A → B → C → A
```

---

## 七、最佳实践

### 7.1 命名规范

```yaml
# ✅ 正确：使用反向域名标识符
app:
  id: "io.intentos.data_analyst"

# ✅ 正确：语义化版本
version: "1.0.0"

# ❌ 错误：随意命名
app:
  id: "my_app_123"
version: "final"
```

### 7.2 意图设计

```yaml
# ✅ 正确：单一职责
intents:
  - id: "data_analysis"
    name: "数据分析"
    patterns: ["分析.*数据"]
    
  - id: "report_generation"
    name: "报告生成"
    patterns: ["生成.*报告"]

# ❌ 错误：职责混杂
intents:
  - id: "everything"
    name: "万能意图"
    patterns: [".*"]  # 匹配所有
```

### 7.3 能力设计

```yaml
# ✅ 正确：明确输入输出
capabilities:
  - id: "data_loader"
    parameters:
      - name: "path"
        type: "string"
        required: true
    returns:
      type: "object"
      properties:
        data: { type: "array" }

# ❌ 错误：模糊定义
capabilities:
  - id: "do_something"
    parameters: []
    returns:
      type: "any"
```

### 7.4 计费配置

```yaml
# ✅ 正确：透明定价
pricing:
  model: "pay_per_use"
  dimensions:
    - name: "execution_time"
      unit: "minute"
      rate: 0.10
  minimum_charge: 0.01

# ❌ 错误：隐藏费用
pricing:
  model: "custom"
  # 没有明确说明如何计费
```

---

## 八、参考文档

| 文档 | 说明 |
|------|------|
| [AI Native App 概述](./AI_NATIVE_APP.md) | 核心概念、架构概览 |
| [应用开发指南](./APP_DEVELOPMENT_GUIDE.md) | 开发流程、最佳实践 |
| [计费与收益](./BILLING_AND_REVENUE.md) | 计费模式、收益分成 |

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Release Candidate
