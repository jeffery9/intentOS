# IntentOS 应用开发指南：语言即软件

## 概述

在 IntentOS 中，**语言即软件 (Language is Software)** 不是口号，而是核心设计哲学。本指南将展示开发者如何通过**定义意图**和**注册能力**来创建应用，而无需编写传统的硬编码逻辑。

---

## 一、范式转变：从"编写"到"定义"

### 传统开发方式

```python
# ❌ 传统方式：硬编码逻辑
@app.route('/weather')
def get_weather():
    city = request.args.get('city')
    api_key = os.getenv('WEATHER_API_KEY')
    response = requests.get(f'https://api.weather.com/{city}?key={api_key}')
    data = response.json()
    return jsonify({
        'temperature': data['temp'],
        'condition': data['condition'],
    })
```

**问题**:
- 固定的 API 端点
- 硬编码的逻辑流程
- 用户必须知道如何调用
- 扩展需要修改代码

### IntentOS 开发方式

```python
# ✅ IntentOS 方式：定义能力
from intentos.agent import CapabilityRegistry

registry = CapabilityRegistry()

@registry.register(
    id="weather_query",
    name="天气查询",
    description="查询全球各地天气信息",
    tags=["weather", "query"],
    source="builtin",
)
def query_weather(city: str) -> dict:
    """查询天气"""
    return {
        "city": city,
        "temperature": "25°C",
        "condition": "晴",
    }

# 用户只需说："北京天气怎么样"
# → 自动匹配能力 → 执行 → 返回结果
```

**优势**:
- 自然语言交互
- 自动意图匹配
- 能力可组合
- 扩展无需修改核心代码

---

## 二、应用开发核心概念

### 1. 能力 (Capability)

**能力是 IntentOS 的基本构建单元**，是一个可执行的功能单元。

```python
from intentos.agent import CapabilityRegistry

registry = CapabilityRegistry()

# 定义能力的三要素
registry.register(
    # 1. 标识
    id="unique_id",
    name="人类可读名称",
    description="能力描述（用于意图匹配）",
    
    # 2. 执行逻辑
    handler=your_function,
    
    # 3. 元数据
    tags=["tag1", "tag2"],  # 用于关键词匹配
    input_schema={...},     # 输入参数定义
    output_schema={...},    # 输出结果定义
    source="builtin",       # 来源：builtin/mcp/skill
)
```

### 2. 意图 (Intent)

**意图是用户目标的自然语言表达**。

```
用户说："北京明天会下雨吗"
    ↓
系统解析：
{
    "type": "weather_query",
    "entities": {
        "location": "北京",
        "time": "明天",
        "query_type": "rain",
    }
}
    ↓
匹配能力：weather_query
    ↓
执行并返回结果
```

### 3. 能力注册中心 (Capability Registry)

**所有能力的中央注册表**，支持三种来源：

```python
from intentos.agent import CapabilityRegistry

registry = CapabilityRegistry()

# 1. 内置能力 (Builtin)
registry.register(..., source="builtin")

# 2. MCP 工具 (Model Context Protocol)
await agent.connect_mcp("weather", "npx", ["-y", "@mcp/server-weather"])
# → 自动注册 MCP 工具为能力

# 3. Skills (Claude Skills 规范)
agent = AIAgent(enable_skills=True)
# → 自动加载 ~/.claude/skills/ 中的 Skills
```

---

## 三、开发流程：五步创建应用

### 步骤 1: 定义能力

```python
# weather_app.py
from intentos.agent import CapabilityRegistry

registry = CapabilityRegistry()

@registry.register(
    id="weather_query",
    name="天气查询",
    description="查询全球各地天气信息",
    tags=["weather", "query", "forecast"],
    source="builtin",
)
def query_weather(city: str, days: int = 1) -> dict:
    """
    查询天气
    
    Args:
        city: 城市名称
        days: 预报天数 (默认 1 天)
    
    Returns:
        dict: 天气信息
    """
    # 实际实现会调用天气 API
    return {
        "city": city,
        "forecast": [
            {
                "date": "2026-03-16",
                "temperature": "25°C",
                "condition": "晴",
            }
        ] * days,
    }
```

### 步骤 2: 定义意图模板 (可选)

```python
# 意图模板帮助更精确地匹配
from intentos.agent import IntentTemplate

weather_template = IntentTemplate(
    id="weather_intent",
    name="天气查询意图",
    description="查询天气相关",
    keywords=["天气", "气温", "下雨", "晴天", "预报"],
    category="weather",
)
```

### 步骤 3: 创建 Agent 并注册能力

```python
import asyncio
from intentos.agent import AIAgent

async def main():
    # 创建 Agent
    agent = AIAgent()
    await agent.initialize()
    
    # 能力已自动注册（通过 @registry.register）
    
    # 测试
    from intentos.agent import AgentContext
    context = AgentContext(user_id="test")
    
    result = await agent.execute("北京天气怎么样", context)
    print(result.data)

asyncio.run(main())
```

### 步骤 4: 添加 MCP 支持 (可选)

```python
# 连接外部 MCP 服务器扩展能力
await agent.connect_mcp(
    name="weather_api",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-weather"],
)

# 现在可以使用 MCP 提供的天气工具
result = await agent.execute("上海明天会下雨吗", context)
```

### 步骤 5: 打包为 Skill (可选)

```bash
# 创建 Skill 目录结构
mkdir -p ~/.claude/skills/weather-app/{scripts,references,assets}

# 创建 SKILL.md
cat > ~/.claude/skills/weather-app/SKILL.md << EOF
---
name: weather-app
description: 天气查询应用
license: MIT
---

# 天气查询应用

提供全球天气查询功能。

## 能力

- 查询当前天气
- 查询多日预报
- 天气预警查询

## 使用示例

用户：北京天气怎么样
Agent: 北京今天晴，25°C...
EOF
```

---

## 四、完整示例：销售数据分析应用

### 示例 1: 简单能力定义

```python
# sales_app.py
from intentos.agent import CapabilityRegistry
import pandas as pd

registry = CapabilityRegistry()

@registry.register(
    id="sales_analysis",
    name="销售数据分析",
    description="分析销售数据，生成洞察报告",
    tags=["sales", "analysis", "report", "数据", "销售"],
    source="builtin",
)
def analyze_sales(region: str = "all", period: str = "month") -> dict:
    """
    分析销售数据
    
    Args:
        region: 区域 (all/华东/华北/华南)
        period: 周期 (day/week/month/year)
    
    Returns:
        dict: 分析结果
    """
    # 模拟数据
    return {
        "success": True,
        "region": region,
        "period": period,
        "total_sales": 1250000,
        "growth_rate": 0.15,
        "top_products": ["产品 A", "产品 B", "产品 C"],
        "insights": [
            "华东区增长最快 (+25%)",
            "产品 A 贡献 40% 销售额",
            "周末销售额比工作日高 30%",
        ],
    }
```

### 示例 2: 复杂能力（带上下文）

```python
@registry.register(
    id="sales_report_generation",
    name="销售报告生成",
    description="生成可视化销售报告",
    tags=["sales", "report", "visualization", "报告", "图表"],
    source="builtin",
)
async def generate_report(
    region: str,
    period: str,
    format: str = "pdf"
) -> dict:
    """
    生成销售报告
    
    Args:
        region: 区域
        period: 周期
        format: 格式 (pdf/html/png)
    
    Returns:
        dict: 报告文件和信息
    """
    # 1. 获取数据
    data = await analyze_sales(region, period)
    
    # 2. 生成图表
    chart = await create_chart(data)
    
    # 3. 生成报告
    report = await create_document(data, chart, format)
    
    return {
        "success": True,
        "report_url": report.url,
        "chart_url": chart.url,
        "summary": f"{region}{period}销售额{data['total_sales']}，增长{data['growth_rate']*100}%",
    }
```

### 示例 3: 组合能力

```python
@registry.register(
    id="sales_insight_orchestrator",
    name="销售洞察编排器",
    description="综合分析销售数据并提供建议",
    tags=["sales", "insight", "orchestration"],
    source="builtin",
)
async def orchestrate_insight(intent: str, context: dict) -> dict:
    """
    编排多个能力提供综合洞察
    """
    # 1. 分析数据
    analysis = await analyze_sales(
        region=context.get("region", "all"),
        period=context.get("period", "month"),
    )
    
    # 2. 生成报告
    report = await generate_report(
        region=context.get("region", "all"),
        period=context.get("period", "month"),
    )
    
    # 3. 提供建议
    recommendations = generate_recommendations(analysis)
    
    return {
        "success": True,
        "analysis": analysis,
        "report": report,
        "recommendations": recommendations,
    }
```

### 用户使用示例

```python
import asyncio
from intentos.agent import AIAgent, AgentContext

async def demo():
    agent = AIAgent()
    await agent.initialize()
    context = AgentContext(user_id="sales_manager")
    
    # 用户自然语言交互
    intents = [
        "分析华东区上个月的销售",
        "生成可视化报告",
        "有什么洞察和建议",
    ]
    
    for intent in intents:
        print(f"\n用户：{intent}")
        result = await agent.execute(intent, context)
        print(f"Agent: {result.message}")
        if result.data:
            print(f"数据：{result.data}")

asyncio.run(demo())
```

**输出**:
```
用户：分析华东区上个月的销售
Agent: ✓ 执行成功
数据：{'region': '华东', 'period': 'month', 'total_sales': 1250000, ...}

用户：生成可视化报告
Agent: ✓ 执行成功
数据：{'report_url': '...', 'chart_url': '...', ...}

用户：有什么洞察和建议
Agent: ✓ 执行成功
数据：{'recommendations': ['增加华东区投入', '优化产品组合', ...]}
```

---

## 五、如何体现"语言即软件"

### 1. 自然语言即 API

**传统方式**:
```
POST /api/sales/analysis
{
    "region": "华东",
    "period": "2026-02",
    "metrics": ["revenue", "growth"]
}
```

**IntentOS 方式**:
```
用户："分析华东区二月份的销售"
→ 自动解析 → 自动执行 → 返回结果
```

### 2. 能力即词汇

每个注册的能力就像语言的"词汇"：

```python
# 词汇表（能力注册）
registry.register(id="query", name="查询", description="...")
registry.register(id="analyze", name="分析", description="...")
registry.register(id="generate", name="生成", description="...")

# 用户"造句"（自然语言）
"查询华东区销售"      → 匹配 query 能力
"分析销售趋势"        → 匹配 analyze 能力
"生成可视化报告"      → 匹配 generate 能力
```

### 3. 意图编译即语法解析

```
用户输入："把华东区上季度的销售数据做成图表发给产品团队"
    ↓
意图解析（语法分析）:
{
    "action": "generate_and_send",
    "data": {
        "type": "sales_chart",
        "region": "华东",
        "period": "last_quarter",
    },
    "recipient": "product_team",
}
    ↓
能力编排（语义执行）:
1. query_sales(region="华东", period="last_quarter")
2. generate_chart(data)
3. send_email(to="product_team", attachment=chart)
```

### 4. 动态生长即语言演化

```python
# 新能力注册 = 新词汇加入语言
@registry.register(id="new_capability", ...)

# 用户学会新用法 = 语言演化
用户："用新学的销售分析方法分析华东区"
→ 系统自动使用新注册的分析能力
```

---

## 六、高级主题

### 1. 能力组合与编排

```python
@registry.register(
    id="multi_step_workflow",
    name="多步骤工作流",
    description="编排多个能力完成复杂任务",
    tags=["workflow", "orchestration"],
)
async def workflow(intent: str, context: dict) -> dict:
    """编排多个能力"""
    # 步骤 1: 查询
    data = await registry.execute_capability("query_sales", **context)
    
    # 步骤 2: 分析
    analysis = await registry.execute_capability("analyze_data", data=data)
    
    # 步骤 3: 生成
    report = await registry.execute_capability("generate_report", analysis=analysis)
    
    # 步骤 4: 发送
    await registry.execute_capability("send_email", report=report)
    
    return {"success": True, "report": report}
```

### 2. 上下文感知

```python
@registry.register(
    id="context_aware_query",
    name="上下文感知查询",
    description="根据对话历史理解意图",
    tags=["context", "query"],
)
async def context_query(intent: str, context: AgentContext) -> dict:
    """上下文感知查询"""
    # 利用对话历史
    history = context.conversation_history
    
    # 指代消解
    if "它" in intent or "这个" in intent:
        # 从历史中查找指代对象
        referent = resolve_reference(intent, history)
        intent = intent.replace("它", referent)
    
    # 执行查询
    return await execute_query(intent)
```

### 3. 自愈与改进

```python
from intentos.agent import ImprovementLayer

improvement = ImprovementLayer()

# 监测执行
status = await improvement.monitor_execution()

# 检测漂移
if status.drift_detected:
    # 生成修复意图
    refinement = await improvement.generate_refinement()
    
    # 自愈
    await improvement.self_heal(refinement)
```

---

## 七、最佳实践

### 1. 能力设计原则

```python
# ✅ 好的能力设计
@registry.register(
    id="query_weather",
    name="天气查询",
    description="查询全球各地天气信息",  # 清晰描述
    tags=["weather", "query"],  # 精确标签
    input_schema={  # 明确输入
        "city": {"type": "string", "description": "城市名"},
    },
)
def query_weather(city: str) -> dict:
    return {"city": city, "temperature": "..."}

# ❌ 坏的能力设计
@registry.register(
    id="do_stuff",  # 模糊 ID
    name="处理",     # 模糊名称
    description="做一些事情",  # 无描述
)
def do_stuff(**kwargs):  # 无明确输入
    ...
```

### 2. 意图匹配优化

```python
# 使用丰富的 tags 提高匹配率
@registry.register(
    id="weather_query",
    tags=[
        # 核心词
        "weather", "天气",
        # 同义词
        "气温", "温度", "气候",
        # 相关动作
        "查询", "查看", "想知道",
        # 问题形式
        "会下雨吗", "多少度", "热不热",
    ],
)
```

### 3. 错误处理

```python
@registry.register(...)
def safe_capability(**kwargs) -> dict:
    """安全的能力实现"""
    try:
        # 参数验证
        validate_params(kwargs)
        
        # 执行逻辑
        result = execute_logic(**kwargs)
        
        return {"success": True, "data": result}
    
    except ValidationError as e:
        return {"success": False, "error": f"参数错误：{e}"}
    
    except Exception as e:
        return {"success": False, "error": f"执行失败：{e}"}
```

---

## 八、总结

在 IntentOS 中开发应用，就是**定义能力**和**注册意图**的过程：

**开发流程**:
1. 定义能力 (Capability)
2. 注册到注册中心 (Registry)
3. Agent 自动匹配和执行
4. 用户通过自然语言使用

**语言即软件的体现**:
- ✓ 自然语言即 API
- ✓ 能力即词汇
- ✓ 意图编译即语法解析
- ✓ 动态生长即语言演化

**核心优势**:
- 开发者只需关注"能做什么"（能力定义）
- 系统自动处理"如何做"（意图匹配和执行）
- 用户通过自然语言交互（无需学习 API）

**在 IntentOS 中，开发应用不是编写代码，而是定义语言！** 🌟✨

---

## 参考文档

- [应用层架构](./APPS_ARCHITECTURE.md)
- [Self-Bootstrap 机制](./SELF_BOOTSTRAP.md)
- [Skill 规范](./SKILL_SPECIFICATION.md)
- [MCP 协议](https://modelcontextprotocol.io/)
