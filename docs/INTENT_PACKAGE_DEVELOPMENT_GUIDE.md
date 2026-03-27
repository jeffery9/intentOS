# IntentOS 意图包开发指南

**版本**: 1.0  
**日期**: 2026-03-27  
**状态**: ✅ 完成

---

## 📋 概述

本指南帮助开发者快速创建符合 IntentOS 规范的 AI Native App。意图包是运行于 IntentOS 之上的软件单元，通过自然语言意图与用户交互。

### 前置要求

- Python 3.10+
- IntentOS CLI 工具 (`pip install intentos`)
- 基本的 YAML 知识

---

## 🚀 快速开始

### 1. 初始化项目

```bash
# 创建新的意图包项目
intentos init sales_analyst

# 生成的目录结构
sales_analyst/
├── manifest.yaml          # 核心配置文件
├── intents/               # 意图定义
│   ├── query_sales.yaml
│   └── analyze_trend.yaml
├── skills/                # 技能实现
│   └── data_loader.py
├── assets/                # 资源文件
└── README.md
```

### 2. 编辑 manifest.yaml

```yaml
app_id: "sales_analyst"
name: "销售数据分析助手"
version: "1.0.0"
description: "分析销售数据并生成可视化报表"

intents:
  - name: "query_sales"
    description: "查询指定区域和时间的销售数据"
    patterns:
      - "查询 {region} {period} 的销售数据"
      - "{region} {period} 卖得怎么样"
    parameters:
      - name: "region"
        type: "string"
        required: true
        enum: ["华东", "华南", "华北", "华西"]
      - name: "period"
        type: "string"
        required: true

capabilities:
  - name: "data_loader"
    description: "从数据库加载销售数据"
    type: "io"
```

### 3. 本地调试

```bash
# 启动开发服务器
intentos dev

# 测试意图
intentos test --intent "查询华东区 Q1 销售数据"
```

### 4. 打包发布

```bash
# 验证配置
intentos validate

# 打包
intentos package

# 发布到应用市场
intentos publish
```

---

## 📁 目录结构详解

### manifest.yaml

核心配置文件，定义应用的元数据、意图、能力需求等。

```yaml
# 完整示例请参考 INTENT_PACKAGE_SPEC.md
```

### intents/ 目录

存放意图定义文件，每个文件定义一个意图的详细信息。

**intents/query_sales.yaml**:
```yaml
name: "query_sales"
description: "查询指定区域和时间的销售数据"
patterns:
  - "查询 {region} {period} 的销售数据"
  - "{region} {period} 卖得怎么样"
  - "看看{region}的{period}业绩"

parameters:
  - name: "region"
    type: "string"
    description: "销售区域"
    required: true
    enum: ["华东", "华南", "华北", "华西"]
  
  - name: "period"
    type: "string"
    description: "时间周期"
    required: true
    examples: ["Q1", "Q2", "上月", "本周"]

responses:
  success:
    template: "{region} {period} 的销售额为 {total} 元"
  error:
    template: "查询失败：{error_message}"
```

### skills/ 目录

存放技能的 Python 实现（可选，系统能力无需实现）。

**skills/data_loader.py**:
```python
"""
数据加载技能实现
"""

from typing import Any, Dict

async def load_sales_data(region: str, period: str) -> Dict[str, Any]:
    """
    从数据库加载销售数据
    
    Args:
        region: 销售区域
        period: 时间周期
    
    Returns:
        销售数据字典
    """
    # 实际实现会连接数据库
    # 这里返回模拟数据
    return {
        "region": region,
        "period": period,
        "total": 1000000,
        "orders": 5000,
    }
```

### assets/ 目录

存放资源文件，如 Prompt 模板、静态资源等。

**assets/templates/report_prompt.txt**:
```
你是一个专业的数据分析师，需要根据以下销售数据生成报表：

区域：{region}
周期：{period}
销售额：{total}
订单数：{orders}

请分析数据趋势并提供建议。
```

---

## 🔧 能力开发

### 系统能力 vs IO 能力

**系统能力** (System Capabilities):
- 由 IntentOS 提供
- 如 `shell`, `filesystem`, `network`
- 无需开发者实现

**IO 能力** (IO Capabilities):
- 由开发者定义和实现
- 如 `data_loader`, `chart_renderer`
- 需要在 skills/ 目录中实现

### 实现 IO 能力

**1. 在 manifest.yaml 中声明**:
```yaml
capabilities:
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
        type: "object"
```

**2. 在 skills/ 中实现**:
```python
# skills/data_loader.py

async def load_sales_data(region: str, period: str) -> dict:
    """加载销售数据"""
    # 实现逻辑
    pass
```

**3. 注册能力**:
```python
# 在应用初始化时注册
from intentos import register_capability

register_capability(
    name="data_loader",
    func=load_sales_data,
    input_schema={...},
    output_schema={...},
)
```

---

## 🧪 测试与调试

### 本地测试

```bash
# 测试单个意图
intentos test --intent "查询华东区 Q1 销售数据"

# 测试所有意图
intentos test --all

# 带参数测试
intentos test --intent "查询销售数据" --params '{"region": "华东", "period": "Q1"}'
```

### 调试模式

```bash
# 启动调试服务器
intentos dev --debug

# 查看编译后的 PEF
intentos compile --intent "查询华东区 Q1 销售数据" --output-pef

# 查看执行轨迹
intentos trace --last
```

### 性能分析

```bash
# 性能分析
intentos profile --intent "查询华东区 Q1 销售数据"

# 输出示例:
# 编译时间：5.2ms
# 执行时间：350ms
# Token 使用：1200
# 缓存命中：是
```

---

## 📦 打包与发布

### 验证配置

```bash
# 验证 manifest.yaml
intentos validate

# 输出示例:
# ✅ Schema 验证通过
# ✅ 意图名称唯一性检查通过
# ✅ 能力引用有效性检查通过
# ✅ 资源配置合理性检查通过
```

### 打包

```bash
# 打包为 .intentos 格式
intentos package

# 输出：sales_analyst-1.0.0.intentos

# 查看包内容
intentos inspect sales_analyst-1.0.0.intentos
```

### 发布

```bash
# 发布到公共应用市场
intentos publish

# 发布到私有仓库
intentos publish --registry https://internal.registry.io

# 发布到本地
intentos publish --local
```

---

## 🌐 分布式开发

### 启用 Map-Reduce

在 manifest.yaml 中配置：

```yaml
distributed:
  enabled: true
  map_reduce: true
  data_partitions: ["region"]
  reduce_strategy: "llm_summary"
```

### 编写分布式意图

```yaml
intents:
  - name: "analyze_nationwide"
    description: "分析全国销售数据"
    distributed:
      enabled: true
      map_func: "analyze_region"  # 各节点分析各自区域
      reduce_func: "summarize"    # 汇总分析结果
```

### 实现分布式函数

```python
# skills/distributed_analyzer.py

async def analyze_region(region: str, data: dict) -> dict:
    """Map: 分析单个区域的数据"""
    return {
        "region": region,
        "total": sum(data["sales"]),
        "trend": calculate_trend(data),
    }

async def summarize(results: list) -> str:
    """Reduce: 汇总各节点结果"""
    # 调用 LLM 进行语义汇总
    return llm_summary(results)
```

---

## 🔐 安全与权限

### 权限声明

```yaml
config:
  permissions:
    allow_network_access: true
    allow_file_write: false
    allowed_domains:
      - "api.sales.internal"
    allowed_paths:
      - "/tmp/reports"
```

### 资源配额

```yaml
config:
  resources:
    max_memory: "512MB"
    max_execution_time: 60
    max_concurrent_requests: 10
    max_token_usage: 10000
```

### 安全最佳实践

✅ **推荐**:
- 明确声明所需权限
- 设置合理的资源限制
- 验证所有输入参数
- 使用参数化查询防止注入

❌ **不推荐**:
- 请求不必要的权限
- 无限制的资源使用
- 信任用户输入
- 硬编码敏感信息

---

## 📊 监控与日志

### 配置监控

```yaml
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
```

### 查看指标

```bash
# 查看应用指标
intentos metrics sales_analyst

# 查看日志
intentos logs sales_analyst --tail 100

# 导出指标
intentos metrics export --format prometheus
```

---

## 🎯 最佳实践

### 1. 意图设计

✅ **好的意图**:
- 目标明确，职责单一
- 参数定义清晰
- 支持多种自然语言表达

❌ **不好的意图**:
- 意图过于宽泛
- 参数过多或过少
- 只支持一种表达方式

### 2. 能力声明

✅ **推荐**:
```yaml
capabilities:
  - name: "data_loader"
    interface:
      input:
        type: "object"
        required: ["region", "period"]
```

❌ **不推荐**:
```yaml
capabilities:
  - name: "data_loader"
    # 缺少接口定义
```

### 3. 错误处理

```python
async def load_sales_data(region: str, period: str) -> dict:
    try:
        # 加载数据
        data = await db.query(...)
        return {"success": True, "data": data}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": "DATA_LOAD_FAILED",
        }
```

### 4. 性能优化

- 使用缓存减少重复查询
- 批量处理减少 IO 调用
- 异步执行提高并发能力
- 监控性能指标持续优化

---

## 📚 参考资源

- [Intent Package Specification](./INTENT_PACKAGE_SPEC.md) - 完整规范文档
- [Developer Tools](./DEVELOPER_TOOLS.md) - CLI 和 SDK 使用指南
- [Performance Optimization](./PERFORMANCE_OPTIMIZATION_V17.md) - 性能优化指南
- [GitHub 示例仓库](https://github.com/intentos/intent-packages) - 示例代码

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-27  
**维护者**: IntentOS Team
