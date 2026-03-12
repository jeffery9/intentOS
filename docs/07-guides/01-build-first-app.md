# 构建第一个 IntentOS App

> 本指南将带你创建第一个 IntentOS 应用，理解意图包的结构和开发流程。

---

## 1. 什么是 IntentOS App

在 IntentOS 中，**App = 意图包 (Intent Pack)**，包含：

- **意图模板**: 预定义的可复用意图
- **能力注册**: 可调用的 API/函数
- **领域知识**: 特定业务领域的知识

### 传统 App vs IntentOS App

| 维度 | 传统 App | IntentOS App |
|------|---------|-------------|
| **入口** | UI 界面 | 自然语言 |
| **结构** | 页面/组件 | 意图模板 |
| **逻辑** | 硬编码流程 | 动态调度 |
| **扩展** | 版本发布 | 注册新意图 |

---

## 2. 项目结构

```
my_first_app/
├── __init__.py              # 包定义
├── intents/                 # 意图模板
│   ├── __init__.py
│   ├── sales_analysis.py    # 销售分析意图
│   └── customer_report.py   # 客户报告意图
├── capabilities/            # 能力定义
│   ├── __init__.py
│   ├── query_sales.py       # 查询销售能力
│   └── generate_report.py   # 生成报告能力
└── knowledge/               # 领域知识
    └── sales_terms.json     # 销售术语
```

---

## 3. 创建销售分析 App

### 3.1 创建项目

```bash
mkdir my_first_app
cd my_first_app
mkdir intents capabilities knowledge
touch __init__.py
touch intents/__init__.py
touch capabilities/__init__.py
```

### 3.2 定义能力

```python
# capabilities/query_sales.py
from intentos import Capability, Context
from typing import Any

async def query_sales(context: Context, region: str, period: str) -> dict:
    """
    查询销售数据
    
    Args:
        context: 执行上下文
        region: 区域（华东/华南/华北/西部）
        period: 时间段（Q1/Q2/Q3/Q4）
    
    Returns:
        销售数据
    """
    # 实际逻辑：调用 API 或数据库
    # 这里用模拟数据
    return {
        "region": region,
        "period": period,
        "revenue": 1000000,
        "growth": 0.15,
        "products": [
            {"name": "产品 A", "sales": 500000},
            {"name": "产品 B", "sales": 300000},
        ]
    }

# 注册能力
query_sales_capability = Capability(
    name="query_sales",
    description="查询销售数据",
    input_schema={
        "type": "object",
        "properties": {
            "region": {"type": "string", "description": "区域"},
            "period": {"type": "string", "description": "时间段"},
        },
        "required": ["region"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "revenue": {"type": "number"},
            "growth": {"type": "number"},
        },
    },
    func=query_sales,
)
```

### 3.3 定义意图模板

```python
# intents/sales_analysis.py
from intentos import IntentTemplate, IntentType, IntentStep

# 销售分析意图模板
sales_analysis_template = IntentTemplate(
    name="sales_analysis",
    description="分析销售数据",
    intent_type=IntentType.COMPOSITE,
    params_schema={
        "region": {"type": "string"},
        "period": {"type": "string"},
    },
    steps=[
        IntentStep(
            capability_name="query_sales",
            params={
                "region": "{{region}}",
                "period": "{{period}}",
            },
            output_var="sales_data",
        ),
        IntentStep(
            capability_name="analyze_trends",
            params={
                "data": "${sales_data}",
            },
            output_var="analysis",
        ),
    ],
    tags=["sales", "analysis"],
    version="1.0.0",
)
```

### 3.4 注册能力和意图

```python
# __init__.py
from .capabilities.query_sales import query_sales_capability
from .intents.sales_analysis import sales_analysis_template

def register(registry):
    """注册到 IntentOS"""
    # 注册能力
    registry.register_capability(query_sales_capability)
    
    # 注册意图模板
    registry.register_template(sales_analysis_template)
    
    print("✅ 销售分析 App 已注册")
    print(f"  - 能力：{query_sales_capability.name}")
    print(f"  - 意图：{sales_analysis_template.name}")
```

---

## 4. 使用 App

### 4.1 初始化 IntentOS

```python
import asyncio
from intentos import IntentOS
from my_first_app import register

async def main():
    # 创建 IntentOS 实例
    os = IntentOS()
    os.initialize()
    
    # 注册 App
    register(os.registry)
    
    # 使用意图
    result = await os.execute("分析华东区 Q3 销售数据")
    print(result)

asyncio.run(main())
```

### 4.2 执行流程

```
用户："分析华东区 Q3 销售数据"
    ↓
[意图解析器]
    ↓
识别意图：sales_analysis
参数：region=华东，period=Q3
    ↓
[意图执行引擎]
    ↓
执行步骤 1: query_sales(region="华东", period="Q3")
    ↓
执行步骤 2: analyze_trends(data=${sales_data})
    ↓
[返回结果]
    ↓
{
    "region": "华东",
    "period": "Q3",
    "revenue": 1000000,
    "growth": 0.15,
    "analysis": "销售增长 15%..."
}
```

---

## 5. 添加更多功能

### 5.1 添加客户报告能力

```python
# capabilities/generate_report.py
from intentos import Capability, Context

async def generate_report(context: Context, data: dict, format: str = "pdf") -> dict:
    """生成报告"""
    return {
        "title": "销售分析报告",
        "format": format,
        "content": f"报告内容：{data}",
        "url": f"/reports/{uuid.uuid4()}.{format}",
    }

generate_report_capability = Capability(
    name="generate_report",
    description="生成报告",
    input_schema={
        "type": "object",
        "properties": {
            "data": {"type": "object"},
            "format": {"type": "string", "enum": ["pdf", "html", "markdown"]},
        },
        "required": ["data"],
    },
    func=generate_report,
)
```

### 5.2 添加复合意图模板

```python
# intents/customer_report.py
from intentos import IntentTemplate, IntentType, IntentStep

# 客户报告意图模板
customer_report_template = IntentTemplate(
    name="customer_report",
    description="生成客户报告",
    intent_type=IntentType.COMPOSITE,
    params_schema={
        "customer_id": {"type": "string"},
        "report_type": {"type": "string", "enum": ["monthly", "quarterly", "annual"]},
    },
    steps=[
        IntentStep(
            capability_name="query_customer",
            params={"customer_id": "{{customer_id}}"},
            output_var="customer_data",
        ),
        IntentStep(
            capability_name="query_orders",
            params={"customer_id": "{{customer_id}}"},
            output_var="order_data",
        ),
        IntentStep(
            capability_name="generate_report",
            params={
                "data": {
                    "customer": "${customer_data}",
                    "orders": "${order_data}",
                },
                "format": "pdf",
            },
            output_var="report",
        ),
    ],
    tags=["customer", "report"],
)
```

### 5.3 更新注册

```python
# __init__.py
from .capabilities.query_sales import query_sales_capability
from .capabilities.generate_report import generate_report_capability
from .intents.sales_analysis import sales_analysis_template
from .intents.customer_report import customer_report_template

def register(registry):
    """注册到 IntentOS"""
    # 注册能力
    registry.register_capability(query_sales_capability)
    registry.register_capability(generate_report_capability)
    
    # 注册意图模板
    registry.register_template(sales_analysis_template)
    registry.register_template(customer_report_template)
    
    print("✅ App 已注册")
    print(f"  - 能力：query_sales, generate_report")
    print(f"  - 意图：sales_analysis, customer_report")
```

---

## 6. 调试和测试

### 6.1 单元测试

```python
# tests/test_app.py
import pytest
from intentos import IntentRegistry
from my_first_app import register

@pytest.fixture
def registry():
    reg = IntentRegistry()
    register(reg)
    return reg

@pytest.mark.asyncio
async def test_query_sales(registry):
    cap = registry.get_capability("query_sales")
    assert cap is not None
    
    from intentos import Context
    result = await cap.func(
        Context(user_id="test"),
        region="华东",
        period="Q3",
    )
    
    assert result["region"] == "华东"
    assert "revenue" in result

@pytest.mark.asyncio
async def test_sales_analysis_intent(registry):
    from intentos import Intent, Context
    
    template = registry.get_template("sales_analysis")
    intent = template.instantiate(
        Context(user_id="test"),
        region="华东",
        period="Q3",
    )
    
    assert intent.name == "sales_analysis"
    assert len(intent.steps) == 2
```

### 6.2 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行测试
python -m pytest tests/ -v
```

---

## 7. 打包和分发

### 7.1 创建 setup.py

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="my-first-app",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "intentos>=0.5.0",
    ],
    entry_points={
        "intentos.apps": [
            "my_first_app = my_first_app:register",
        ],
    },
)
```

### 7.2 安装 App

```bash
# 本地安装
pip install -e .

# 或打包分发
python setup.py sdist bdist_wheel
```

---

## 8. 总结

创建 IntentOS App 的步骤：

1. **定义能力**: 注册可调用的 API/函数
2. **定义意图模板**: 预定义可复用的意图
3. **注册到 IntentOS**: 将能力和意图注册到仓库
4. **测试**: 编写单元测试验证功能
5. **打包**: 打包分发给其他用户

---

**下一篇**: [定义意图模板](02-define-intent-template.md)

**上一篇**: [LLM 后端](../05-execution/04-llm-backends.md)
