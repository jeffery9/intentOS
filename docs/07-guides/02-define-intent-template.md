# 定义意图模板

> 意图模板是 IntentOS 中可复用的意图定义，类似函数定义，支持参数化和组合。

---

## 1. 什么是意图模板

**意图模板 (Intent Template)** 是预定义的意图结构，包含：

- **参数 Schema**: 输入参数的定义和验证
- **执行步骤**: 能力调用的顺序和依赖
- **约束条件**: 执行的安全和合规约束

### 类比

| 编程概念 | IntentOS | 说明 |
|---------|---------|------|
| **函数定义** | 意图模板 | 可复用的逻辑单元 |
| **函数参数** | 模板参数 | 输入变量 |
| **函数体** | 执行步骤 | 能力调用序列 |
| **函数调用** | 意图实例化 | 填入参数执行 |

---

## 2. 模板结构

```python
from intentos import IntentTemplate, IntentType, IntentStep

template = IntentTemplate(
    # 基本信息
    name="template_name",           # 模板名称
    description="模板描述",          # 描述
    intent_type=IntentType.COMPOSITE,  # 类型
    version="1.0.0",                # 版本
    tags=["tag1", "tag2"],          # 标签
    
    # 参数定义
    params_schema={
        "param1": {"type": "string"},
        "param2": {"type": "number"},
    },
    
    # 执行步骤
    steps=[
        IntentStep(
            capability_name="capability_1",
            params={"arg": "{{param1}}"},
            output_var="result1",
        ),
        IntentStep(
            capability_name="capability_2",
            params={"data": "${result1}"},
            depends_on=["step1"],
        ),
    ],
    
    # 约束条件
    constraints={
        "required_permissions": ["read_data"],
        "timeout_seconds": 300,
    },
)
```

---

## 3. 参数定义

### 3.1 基本参数

```python
params_schema = {
    # 字符串参数
    "region": {
        "type": "string",
        "description": "区域名称",
    },
    
    # 数字参数
    "threshold": {
        "type": "number",
        "description": "阈值",
        "default": 0.8,
    },
    
    # 布尔参数
    "include_details": {
        "type": "boolean",
        "description": "是否包含详情",
        "default": False,
    },
    
    # 枚举参数
    "format": {
        "type": "string",
        "enum": ["pdf", "html", "markdown"],
        "default": "pdf",
    },
    
    # 数组参数
    "regions": {
        "type": "array",
        "items": {"type": "string"},
    },
}
```

### 3.2 必填和可选

```python
params_schema = {
    # 必填参数（在 required 列表中）
    "region": {"type": "string"},
    "period": {"type": "string"},
    
    # 可选参数（有 default 值）
    "format": {
        "type": "string",
        "default": "pdf",
    },
}

# required 列表
required = ["region", "period"]
```

### 3.3 参数验证

```python
from intentos import IntentTemplate

template = IntentTemplate(
    name="validated_template",
    params_schema={
        "email": {
            "type": "string",
            "format": "email",  # 邮箱格式
        },
        "amount": {
            "type": "number",
            "minimum": 0,       # 最小值
            "maximum": 10000,   # 最大值
        },
        "name": {
            "type": "string",
            "minLength": 1,     # 最小长度
            "maxLength": 100,   # 最大长度
        },
    },
    required=["email", "amount"],
)
```

---

## 4. 执行步骤

### 4.1 基本步骤

```python
from intentos import IntentStep

steps = [
    # 步骤 1: 查询数据
    IntentStep(
        capability_name="query_sales",
        params={
            "region": "{{region}}",      # 模板参数
            "period": "{{period}}",
        },
        output_var="sales_data",         # 输出变量
    ),
    
    # 步骤 2: 分析数据
    IntentStep(
        capability_name="analyze_data",
        params={
            "data": "${sales_data}",     # 引用步骤 1 的输出
        },
        output_var="analysis",
    ),
    
    # 步骤 3: 生成报告
    IntentStep(
        capability_name="generate_report",
        params={
            "analysis": "${analysis}",
            "format": "{{format}}",
        },
    ),
]
```

### 4.2 依赖管理

```python
steps = [
    # 步骤 1: 无依赖
    IntentStep(
        id="step1",
        capability_name="query_east",
        params={"region": "华东"},
    ),
    
    # 步骤 2: 无依赖（可与 step1 并行）
    IntentStep(
        id="step2",
        capability_name="query_south",
        params={"region": "华南"},
    ),
    
    # 步骤 3: 依赖 step1 和 step2
    IntentStep(
        id="step3",
        capability_name="compare",
        params={
            "east": "${step1_result}",
            "south": "${step2_result}",
        },
        depends_on=["step1", "step2"],
    ),
]
```

### 4.3 条件执行

```python
steps = [
    # 步骤 1: 查询数据
    IntentStep(
        id="step1",
        capability_name="query_data",
        output_var="data",
    ),
    
    # 步骤 2: 条件执行
    IntentStep(
        id="step2",
        capability_name="send_alert",
        params={"data": "${data}"},
        condition="exists(${data}) and ${data}.error_rate > 0.1",
    ),
]
```

---

## 5. 模板组合

### 5.1 嵌套模板

```python
# 子模板：数据查询
query_template = IntentTemplate(
    name="data_query",
    params_schema={"source": {"type": "string"}},
    steps=[
        IntentStep(
            capability_name="query",
            params={"source": "{{source}}"},
        ),
    ],
)

# 主模板：嵌套调用子模板
analysis_template = IntentTemplate(
    name="sales_analysis",
    params_schema={"region": {"type": "string"}},
    steps=[
        # 调用子模板
        IntentStep(
            capability_name="data_query",  # 子模板名称
            params={"source": "sales"},
            output_var="sales_data",
        ),
        IntentStep(
            capability_name="analyze",
            params={"data": "${sales_data}"},
        ),
    ],
)
```

### 5.2 模板继承

```python
# 基础模板
base_template = IntentTemplate(
    name="base_report",
    params_schema={"format": {"type": "string", "default": "pdf"}},
    steps=[
        IntentStep(
            capability_name="generate_report",
            params={"format": "{{format}}"},
        ),
    ],
)

# 继承模板
finance_template = base_template.override(
    name="finance_report",
    params_schema={
        "format": {"type": "string", "default": "excel"},
        "include_audit": {"type": "boolean", "default": True},
    },
    add_steps=[
        IntentStep(
            capability_name="audit_check",
            params={"report": "${report}"},
        ),
    ],
)
```

---

## 6. 完整示例

### 6.1 销售分析模板

```python
from intentos import IntentTemplate, IntentType, IntentStep

sales_analysis_template = IntentTemplate(
    # 基本信息
    name="sales_analysis",
    description="分析销售数据并生成报告",
    intent_type=IntentType.COMPOSITE,
    version="1.0.0",
    tags=["sales", "analysis", "report"],
    
    # 参数定义
    params_schema={
        "region": {
            "type": "string",
            "description": "区域名称",
            "enum": ["华东", "华南", "华北", "西部"],
        },
        "period": {
            "type": "string",
            "description": "时间段",
            "enum": ["Q1", "Q2", "Q3", "Q4"],
        },
        "compare_with": {
            "type": "string",
            "description": "对比对象",
            "enum": ["last_period", "last_year", "budget"],
            "default": "last_period",
        },
        "output_format": {
            "type": "string",
            "default": "dashboard",
            "enum": ["dashboard", "pdf", "excel"],
        },
    },
    required=["region", "period"],
    
    # 执行步骤
    steps=[
        # 步骤 1: 查询当前数据
        IntentStep(
            id="query_current",
            capability_name="query_sales",
            params={
                "region": "{{region}}",
                "period": "{{period}}",
            },
            output_var="current_data",
        ),
        
        # 步骤 2: 查询对比数据
        IntentStep(
            id="query_compare",
            capability_name="query_sales",
            params={
                "region": "{{region}}",
                "period": "${compare_period}",  # 动态计算
            },
            output_var="compare_data",
            depends_on=["query_current"],
        ),
        
        # 步骤 3: 对比分析
        IntentStep(
            id="analyze",
            capability_name="compare_analysis",
            params={
                "current": "${current_data}",
                "compare": "${compare_data}",
            },
            output_var="analysis",
            depends_on=["query_current", "query_compare"],
        ),
        
        # 步骤 4: 生成报告
        IntentStep(
            id="report",
            capability_name="generate_dashboard",
            params={
                "analysis": "${analysis}",
                "format": "{{output_format}}",
            },
            depends_on=["analyze"],
        ),
    ],
    
    # 约束条件
    constraints={
        "required_permissions": ["read_sales"],
        "timeout_seconds": 300,
        "max_cost_usd": 10.0,
    },
)
```

### 6.2 实例化模板

```python
from intentos import Context

# 创建上下文
context = Context(
    user_id="manager_001",
    user_role="sales_manager",
    permissions=["read_sales"],
)

# 实例化模板
intent = sales_analysis_template.instantiate(
    context=context,
    region="华东",
    period="Q3",
    compare_with="last_year",
    output_format="dashboard",
)

# 执行意图
from intentos import ExecutionEngine
engine = ExecutionEngine(registry)
result = await engine.execute(intent)
```

---

## 7. 最佳实践

### 7.1 命名规范

```python
# 好的命名
"sales_analysis"           # 清晰描述功能
"query_customer_orders"    # 动词 + 名词
"generate_monthly_report"  # 动词 + 形容词 + 名词

# 避免的命名
"template1"                # 无意义
"do_it"                    # 太模糊
"sales"                    # 太宽泛
```

### 7.2 参数设计

```python
# 好的参数设计
{
    "region": {"type": "string", "description": "区域名称"},
    "include_details": {"type": "boolean", "default": False},
}

# 避免的设计
{
    "param1": {"type": "string"},  # 无描述
    "flag": {"type": "boolean"},   # 含义不明
}
```

### 7.3 步骤设计

```python
# 好的步骤设计
# - 每个步骤职责单一
# - 依赖关系清晰
# - 有明确的输入输出

# 避免的设计
# - 步骤过多（>10 步）
# - 循环依赖
# - 无输出变量
```

---

## 8. 总结

定义意图模板的关键点：

1. **清晰的参数定义**: 使用 JSON Schema 定义参数
2. **合理的步骤设计**: 职责单一，依赖清晰
3. **适当的约束**: 权限、超时、成本限制
4. **可复用性**: 支持嵌套和继承

---

**下一篇**: [注册能力](03-register-capability.md)

**上一篇**: [构建第一个 App](01-build-first-app.md)
