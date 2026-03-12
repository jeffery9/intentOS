# 注册能力

> 能力 (Capability) 是 IntentOS 中可调用的原子功能单元，注册后可被意图模板调用。

---

## 1. 什么是能力

**能力 (Capability)** 是 IntentOS 中的原子功能单元：

- **输入**: 参数（符合 input_schema）
- **输出**: 结果（符合 output_schema）
- **执行**: 函数/API 调用

### 能力类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **函数能力** | Python 函数 | 计算、转换 |
| **API 能力** | HTTP/gRPC API | 查询数据库、调用外部服务 |
| **LLM 能力** | LLM 调用 | 分析、生成文本 |

---

## 2. 定义能力

### 2.1 函数能力

```python
from intentos import Capability, Context
from typing import Any

async def query_sales(context: Context, region: str, period: str) -> dict:
    """
    查询销售数据
    
    Args:
        context: 执行上下文（包含用户信息、权限等）
        region: 区域名称
        period: 时间段
    
    Returns:
        销售数据字典
    """
    # 实际逻辑：调用 API 或数据库
    return {
        "region": region,
        "period": period,
        "revenue": 1000000,
        "growth": 0.15,
    }

# 注册能力
query_sales_capability = Capability(
    name="query_sales",
    description="查询销售数据",
    input_schema={
        "type": "object",
        "properties": {
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
        },
        "required": ["region", "period"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "revenue": {"type": "number"},
            "growth": {"type": "number"},
        },
    },
    func=query_sales,
    requires_permissions=["read_sales"],
    tags=["sales", "query"],
)
```

### 2.2 API 能力

```python
from intentos import Capability
import aiohttp

async def call_external_api(context: Context, **params) -> dict:
    """调用外部 API"""
    url = "https://api.example.com/sales"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=params) as response:
            return await response.json()

external_api_capability = Capability(
    name="external_sales_api",
    description="调用外部销售 API",
    input_schema={
        "type": "object",
        "properties": {
            "region": {"type": "string"},
        },
        "required": ["region"],
    },
    func=call_external_api,
    # API 特定配置
    endpoint="https://api.example.com/sales",
    method="POST",
    authentication={
        "type": "bearer",
        "token_ref": "SALES_API_TOKEN",  # 从配置读取
    },
)
```

### 2.3 LLM 能力

```python
from intentos import Capability, Message

async def analyze_with_llm(context: Context, data: dict) -> dict:
    """使用 LLM 分析数据"""
    from intentos import create_executor
    
    executor = create_executor(provider="openai", model="gpt-4o")
    
    messages = [
        Message.system("你是数据分析专家"),
        Message.user(f"分析以下数据：{data}"),
    ]
    
    response = await executor.execute(messages)
    
    return {
        "analysis": response.content,
        "confidence": 0.95,
    }

llm_analysis_capability = Capability(
    name="llm_analysis",
    description="使用 LLM 分析数据",
    input_schema={
        "type": "object",
        "properties": {
            "data": {"type": "object"},
        },
        "required": ["data"],
    },
    func=analyze_with_llm,
    llm_config={
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 2000,
    },
)
```

---

## 3. 注册能力

### 3.1 注册到仓库

```python
from intentos import IntentRegistry

# 创建仓库
registry = IntentRegistry()

# 注册能力
registry.register_capability(query_sales_capability)
registry.register_capability(external_api_capability)
registry.register_capability(llm_analysis_capability)

print("✅ 能力已注册")
print(f"  - {query_sales_capability.name}")
print(f"  - {external_api_capability.name}")
print(f"  - {llm_analysis_capability.name}")
```

### 3.2 批量注册

```python
def register_all_capabilities(registry: IntentRegistry) -> None:
    """批量注册所有能力"""
    capabilities = [
        query_sales_capability,
        external_api_capability,
        llm_analysis_capability,
    ]
    
    for cap in capabilities:
        registry.register_capability(cap)
    
    print(f"✅ 已注册 {len(capabilities)} 个能力")
```

---

## 4. 能力发现

### 4.1 获取能力

```python
# 通过名称获取
cap = registry.get_capability("query_sales")
print(f"能力描述：{cap.description}")
print(f"输入 Schema: {cap.input_schema}")
```

### 4.2 列出能力

```python
# 列出所有能力
all_caps = registry.list_capabilities()
for cap in all_caps:
    print(f"- {cap.name}: {cap.description}")

# 按标签过滤
sales_caps = registry.list_capabilities(tags=["sales"])
for cap in sales_caps:
    print(f"- {cap.name}")
```

### 4.3 搜索能力

```python
# 搜索能力
results = registry.search("销售")
print(f"模板：{results['templates']}")
print(f"能力：{results['capabilities']}")
```

---

## 5. 能力调用

### 5.1 直接调用

```python
from intentos import Context

# 获取能力
cap = registry.get_capability("query_sales")

# 创建上下文
context = Context(
    user_id="user_001",
    user_role="sales_manager",
    permissions=["read_sales"],
)

# 调用能力
result = await cap.execute(
    context=context,
    region="华东",
    period="Q3",
)

print(f"销售数据：{result}")
```

### 5.2 错误处理

```python
from intentos import Capability, Context

async def safe_execute_capability(cap: Capability, context: Context, **params):
    """安全执行能力"""
    try:
        # 权限检查
        for perm in cap.requires_permissions:
            if not context.has_permission(perm):
                raise PermissionError(f"缺少权限：{perm}")
        
        # 执行
        result = await cap.execute(context, **params)
        return result
        
    except PermissionError as e:
        logger.error(f"权限错误：{e}")
        return {"error": "permission_denied", "message": str(e)}
        
    except Exception as e:
        logger.error(f"执行错误：{e}")
        return {"error": "execution_failed", "message": str(e)}
```

---

## 6. 能力降级

### 6.1 定义降级策略

```python
# 主能力
primary_capability = Capability(
    name="query_sales_primary",
    description="查询销售数据（主）",
    func=query_sales_primary,
    fallback=["query_sales_backup", "query_sales_cache"],  # 降级链
)

# 备用能力
backup_capability = Capability(
    name="query_sales_backup",
    description="查询销售数据（备用）",
    func=query_sales_backup,
)

# 缓存能力
cache_capability = Capability(
    name="query_sales_cache",
    description="查询销售数据（缓存）",
    func=query_sales_cache,
)
```

### 6.2 执行降级

```python
async def execute_with_fallback(cap: Capability, context: Context, **params):
    """带降级的执行"""
    fallback_chain = cap.fallback if hasattr(cap, 'fallback') else []
    
    # 尝试主能力
    try:
        return await cap.execute(context, **params)
    except Exception as e:
        logger.warning(f"主能力失败：{cap.name}, 错误：{e}")
    
    # 尝试备用能力
    for fallback_name in fallback_chain:
        try:
            fallback_cap = registry.get_capability(fallback_name)
            logger.info(f"使用备用能力：{fallback_name}")
            return await fallback_cap.execute(context, **params)
        except Exception as fe:
            logger.warning(f"备用能力失败：{fallback_name}, 错误：{fe}")
    
    # 所有能力都失败
    raise Exception(f"所有能力都失败：{cap.name}")
```

---

## 7. 能力测试

### 7.1 单元测试

```python
import pytest
from intentos import Context

@pytest.mark.asyncio
async def test_query_sales():
    """测试查询销售能力"""
    cap = registry.get_capability("query_sales")
    assert cap is not None
    
    context = Context(
        user_id="test",
        permissions=["read_sales"],
    )
    
    result = await cap.execute(
        context=context,
        region="华东",
        period="Q3",
    )
    
    assert result["region"] == "华东"
    assert "revenue" in result
    assert isinstance(result["growth"], (int, float))

@pytest.mark.asyncio
async def test_query_sales_permission():
    """测试权限检查"""
    cap = registry.get_capability("query_sales")
    
    context = Context(
        user_id="test",
        permissions=[],  # 无权限
    )
    
    with pytest.raises(PermissionError):
        await cap.execute(
            context=context,
            region="华东",
            period="Q3",
        )
```

### 7.2 集成测试

```python
@pytest.mark.asyncio
async def test_sales_analysis_workflow():
    """测试销售分析工作流"""
    from intentos import IntentTemplate, ExecutionEngine
    
    # 创建工作流
    template = registry.get_template("sales_analysis")
    intent = template.instantiate(
        Context(user_id="test", permissions=["read_sales"]),
        region="华东",
        period="Q3",
    )
    
    # 执行工作流
    engine = ExecutionEngine(registry)
    result = await engine.execute(intent)
    
    assert result is not None
    assert "analysis" in result
```

---

## 8. 最佳实践

### 8.1 能力设计原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个能力只做一件事 |
| **明确 Schema** | 清晰定义输入输出 |
| **幂等性** | 多次调用结果相同 |
| **错误处理** | 返回结构化错误信息 |
| **可降级** | 定义备用能力链 |

### 8.2 命名规范

```python
# 好的命名
"query_sales"           # 动词 + 名词
"generate_monthly_report"  # 动词 + 形容词 + 名词
"analyze_customer_churn"   # 动词 + 名词 + 名词

# 避免的命名
"do_it"                 # 太模糊
"sales"                 # 不是动词开头
"process1"              # 无意义
```

### 8.3 版本管理

```python
# 能力版本
capability = Capability(
    name="query_sales",
    version="1.0.0",  # 语义化版本
    # ...
)

# 版本兼容
# - 1.x.x: 向后兼容的更新
# - 2.0.0: 不兼容的更新（创建新能力 query_sales_v2）
```

---

## 9. 总结

注册能力的步骤：

1. **定义能力函数**: 实现业务逻辑
2. **创建 Capability 对象**: 定义 Schema 和元数据
3. **注册到仓库**: `registry.register_capability(cap)`
4. **测试验证**: 单元测试和集成测试
5. **监控运维**: 日志、指标、告警

---

**下一篇**: [部署 IntentOS](04-deploy-intentos.md)

**上一篇**: [定义意图模板](02-define-intent-template.md)
