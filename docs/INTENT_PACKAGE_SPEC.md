# IntentOS 意图包格式规范 (Intent Package Specification)

**版本**: 1.0  
**日期**: 2026-03-27  
**状态**: ✅ 完成

---

## 📋 概述

意图包 (Intent Package) 是 AI Native App 的核心载体，是一个标准化的、可分发的软件单元。其物理形式是一个包含 `manifest.yaml` 和相关资源的目录或压缩包。

### 核心原则

1. **语言即系统**: 自然语言意图是驱动系统的第一性原理
2. **能力与执行分离**: 意图包定义能力需求，运行时 Agent 负责绑定物理实现
3. **按需即时编译**: 软件根据用户意图按需编译为 PEF 执行

---

## 📁 意图包结构

```
my-app/
├── manifest.yaml          # ⭐ 核心配置文件
├── intents/               # 意图定义目录
│   ├── query_sales.yaml   # 查询销售意图
│   ├── analyze_data.yaml  # 分析数据意图
│   └── generate_report.yaml # 生成报表意图
├── skills/                # 技能定义目录（可选）
│   └── data_loader.py     # 数据加载技能
├── assets/                # 资源文件（可选）
│   └── templates/         # Prompt 模板
└── README.md              # 应用说明文档
```

---

## 📝 manifest.yaml 规范

### 完整示例

```yaml
# =============================================================================
# IntentOS 意图包配置文件
# =============================================================================

# -----------------------------------------------------------------------------
# 1. 基础元数据 (Header Metadata)
# -----------------------------------------------------------------------------
app_id: "sales_analyst"           # 应用唯一标识符（命名空间）
name: "销售数据分析助手"            # 应用显示名称
version: "1.0.0"                   # 语义化版本号
description: "分析销售数据并生成可视化报表"  # 应用描述
author: "IntentOS Team"            # 作者/组织
license: "MIT"                     # 许可证
homepage: "https://github.com/intentos/sales_analyst"  # 项目主页

# -----------------------------------------------------------------------------
# 2. 意图定义 (Intents)
# -----------------------------------------------------------------------------
intents:
  # 意图 1: 查询销售数据
  - name: "query_sales"
    description: "查询指定区域和时间的销售数据"
    patterns:  # 支持的自然语言模式
      - "查询 {region} {period} 的销售数据"
      - "{region} {period} 卖得怎么样"
      - "看看 {region} 的{period}业绩"
    parameters:  # 参数定义
      - name: "region"
        type: "string"
        description: "销售区域（如：华东、华南）"
        required: true
        enum: ["华东", "华南", "华北", "华西"]
      - name: "period"
        type: "string"
        description: "时间周期（如：Q1、上月）"
        required: true
    
  # 意图 2: 分析销售趋势
  - name: "analyze_trend"
    description: "分析销售数据的趋势和模式"
    patterns:
      - "分析 {region} 的销售趋势"
      - "{region} 的销售走势如何"
    parameters:
      - name: "region"
        type: "string"
        description: "销售区域"
        required: true
      - name: "metrics"
        type: "array"
        description: "分析指标"
        required: false
        default: ["销售额", "订单量", "客单价"]
    
  # 意图 3: 生成报表
  - name: "generate_report"
    description: "生成销售数据可视化报表"
    patterns:
      - "生成 {region} 的报表"
      - "给我看{region}的销售图表"
    parameters:
      - name: "region"
        type: "string"
        description: "销售区域"
        required: true
      - name: "chart_type"
        type: "string"
        description: "图表类型"
        required: false
        default: "bar"
        enum: ["bar", "line", "pie", "table"]

# -----------------------------------------------------------------------------
# 3. 能力需求 (Capabilities)
# -----------------------------------------------------------------------------
capabilities:
  # IO 能力需求
  - name: "data_loader"
    description: "从数据库加载销售数据"
    type: "io"
    interface:
      input:
        type: "object"
        properties:
          region: { type: "string" }
          period: { type: "string" }
      output:
        type: "array"
        items: { type: "object" }
  
  - name: "data_analyzer"
    description: "分析销售数据并计算指标"
    type: "io"
    interface:
      input:
        type: "object"
        properties:
          data: { type: "array" }
          metrics: { type: "array" }
      output:
        type: "object"
  
  - name: "chart_renderer"
    description: "渲染可视化图表"
    type: "io"
    interface:
      input:
        type: "object"
        properties:
          data: { type: "array" }
          chart_type: { type: "string" }
      output:
        type: "string"  # 图表 URL 或 Base64
  
  # 系统能力需求
  - name: "shell"
    description: "执行 Shell 命令"
    type: "system"
    required: false
  
  - name: "filesystem"
    description: "访问文件系统"
    type: "system"
    required: false
    paths:
      - "/tmp/reports"  # 允许访问的路径

# -----------------------------------------------------------------------------
# 4. 配置与策略 (Configuration & Policy)
# -----------------------------------------------------------------------------
config:
  # 资源配额
  resources:
    max_memory: "512MB"      # 最大内存使用
    max_execution_time: 60   # 最大执行时间（秒）
    max_concurrent_requests: 10  # 最大并发请求数
  
  # 权限策略
  permissions:
    allow_network_access: true      # 允许网络访问
    allow_file_write: false         # 禁止文件写入
    allowed_domains:                # 允许访问的域名
      - "api.sales.internal"
      - "charts.internal"
  
  # 应用特定配置
  app_settings:
    default_region: "华东"
    cache_ttl: 300  # 缓存过期时间（秒）
    report_format: "pdf"

# -----------------------------------------------------------------------------
# 5. 依赖管理 (Dependencies)
# -----------------------------------------------------------------------------
dependencies:
  - app_id: "data_connector"
    version: ">=1.0.0"
    optional: false
  
  - app_id: "chart_library"
    version: "^2.0.0"
    optional: true

# -----------------------------------------------------------------------------
# 6. 分布式执行配置 (Distributed Execution)
# -----------------------------------------------------------------------------
distributed:
  enabled: true                    # 是否支持分布式执行
  map_reduce: true                 # 是否支持 Map-Reduce 模式
  data_partitions: ["region"]      # 数据分区键
  reduce_strategy: "llm_summary"   # 汇总策略：llm_summary / aggregate / concat

# -----------------------------------------------------------------------------
# 7. 监控与日志 (Monitoring & Logging)
# -----------------------------------------------------------------------------
monitoring:
  metrics:
    - name: "query_count"
      type: "counter"
      description: "查询次数"
    - name: "execution_time"
      type: "histogram"
      description: "执行时间分布"
  
  logging:
    level: "INFO"
    format: "json"
    outputs:
      - "stdout"
      - "file:/var/log/intentos/sales_analyst.log"

# -----------------------------------------------------------------------------
# 8. 发布与分发 (Publishing & Distribution)
# -----------------------------------------------------------------------------
publishing:
  registry: "https://marketplace.intentos.io"
  visibility: "public"  # public / private / internal
  categories:
    - "数据分析"
    - "销售工具"
  tags:
    - "销售"
    - "分析"
    - "报表"
```

---

## 🔧 字段详细说明

### 1. 基础元数据

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `app_id` | string | ✅ | 应用唯一标识符，用于命名空间隔离 |
| `name` | string | ✅ | 应用显示名称 |
| `version` | string | ✅ | 语义化版本号 (MAJOR.MINOR.PATCH) |
| `description` | string | ✅ | 应用描述 |
| `author` | string | ❌ | 作者/组织 |
| `license` | string | ❌ | 开源许可证 |
| `homepage` | string | ❌ | 项目主页 URL |

### 2. 意图定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 意图唯一名称 |
| `description` | string | ✅ | 意图描述 |
| `patterns` | string[] | ✅ | 支持的自然语言模式 |
| `parameters` | Parameter[] | ❌ | 参数定义列表 |

**Parameter 结构**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 参数名称 |
| `type` | string | ✅ | 参数类型 (string/number/boolean/array/object) |
| `description` | string | ✅ | 参数描述 |
| `required` | boolean | ❌ | 是否必需 (默认 false) |
| `default` | any | ❌ | 默认值 |
| `enum` | any[] | ❌ | 枚举值列表 |

### 3. 能力需求

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 能力名称 |
| `description` | string | ✅ | 能力描述 |
| `type` | string | ✅ | 能力类型 (io/system) |
| `interface` | Interface | ❌ | 接口定义 (input/output Schema) |
| `required` | boolean | ❌ | 是否必需 (默认 true) |

### 4. 配置与策略

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `resources.max_memory` | string | ❌ | 最大内存使用 |
| `resources.max_execution_time` | number | ❌ | 最大执行时间（秒） |
| `permissions.allow_network_access` | boolean | ❌ | 允许网络访问 |
| `permissions.allow_file_write` | boolean | ❌ | 允许文件写入 |

### 5. 分布式执行

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `enabled` | boolean | ❌ | 是否支持分布式执行 |
| `map_reduce` | boolean | ❌ | 是否支持 Map-Reduce 模式 |
| `data_partitions` | string[] | ❌ | 数据分区键列表 |
| `reduce_strategy` | string | ❌ | 汇总策略 |

---

## 📦 意图包生命周期

### 1. 开发阶段

```bash
# 初始化项目
intentos init sales_analyst

# 本地调试
intentos dev --intent "查询华东区 Q1 销售数据"

# 验证配置
intentos validate

# 打包
intentos package
```

### 2. 发布阶段

```bash
# 发布到应用市场
intentos publish

# 或发布到私有仓库
intentos publish --registry https://internal.registry.io
```

### 3. 运行阶段

```bash
# 安装应用
intentos install sales_analyst

# 执行意图
intentos run sales_analyst "查询华东区 Q1 销售数据"

# 查看状态
intentos status sales_analyst
```

---

## 🔍 验证规则

### Schema 验证

```python
import yaml
from jsonschema import validate

# 加载 Schema
with open('manifest_schema.json') as f:
    schema = json.load(f)

# 验证 manifest.yaml
with open('manifest.yaml') as f:
    manifest = yaml.safe_load(f)

# 执行验证
validate(instance=manifest, schema=schema)
```

### 语义验证

1. **意图名称唯一性**: 同一应用内意图名称不能重复
2. **能力引用有效性**: 引用的能力必须在系统中注册
3. **参数类型匹配**: 默认值类型必须与声明类型一致
4. **资源配额合理性**: 资源限制不能超过租户配额

---

## 📝 最佳实践

### 1. 意图设计

✅ **推荐**:
```yaml
intents:
  - name: "query_sales"
    patterns:
      - "查询 {region} {period} 的销售数据"
      - "{region} {period} 卖得怎么样"
```

❌ **不推荐**:
```yaml
intents:
  - name: "query_sales"
    patterns:
      - "查询销售数据"  # 太模糊，缺少参数
```

### 2. 能力声明

✅ **推荐**:
```yaml
capabilities:
  - name: "data_loader"
    type: "io"
    interface:
      input:
        type: "object"
        required: ["region", "period"]
```

❌ **不推荐**:
```yaml
capabilities:
  - name: "data_loader"
    type: "io"
    # 缺少接口定义
```

### 3. 资源配置

✅ **推荐**:
```yaml
config:
  resources:
    max_memory: "512MB"
    max_execution_time: 60
```

❌ **不推荐**:
```yaml
config:
  resources:
    max_memory: "10GB"  # 过度配置
    max_execution_time: 3600  # 执行时间过长
```

---

## 🔗 相关文档

- [AI Native App 概述](./docs/AI_NATIVE_APP.md)
- [开发者工具文档](./docs/DEVELOPER_TOOLS.md)
- [能力注册规范](./docs/CAPABILITY_REGISTRY.md)
- [运行时 Agent 架构](./docs/RUNTIME_AGENT.md)

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-27  
**维护者**: IntentOS Team
