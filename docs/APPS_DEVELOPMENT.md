# IntentOS 应用开发指南 (v9.0 及更早版本)

> ⚠️ **注意**: 本文档基于旧版应用层架构 (`intentos/apps/`)。
> 
> **新架构** (`intentos/agent/`) 已发布，请查看 [新应用开发指南](./APP_DEVELOPMENT_GUIDE.md) 了解基于能力注册、MCP 和 Skills 的开发方式。

---

## 概述 (旧架构)

应用层 (Layer 1) 是 3 层 7 级架构的最上层，负责：
- 领域意图包
- 用户交互
- 结果呈现

**注意**: 旧架构位于 `intentos/deprecated/apps/`，新架构位于 `intentos/agent/`。

---

## 快速开始 (旧方式)

### 1. 创建应用类

```python
from intentos.apps import AppBase, AppContext, AppResult, app_metadata

@app_metadata(
    app_id="my_app",
    name="我的应用",
    description="应用描述",
    version="1.0.0",
    category="productivity",
    icon="🚀",
    author="你的名字"
)
class MyApp(AppBase):
    """我的应用"""

    async def execute(self, intent: str, context: AppContext) -> AppResult:
        """执行应用"""
        return AppResult(
            success=True,
            message="✓ 完成",
            data={"result": "数据"},
        )
```

### 2. 注册应用

```python
from intentos.apps import get_app_layer

layer = get_app_layer()
app = MyApp()
layer.register_app(app)
```

---

## 新架构对比

| 特性 | 旧架构 (v9.0) | 新架构 (v10.0+) |
|------|--------------|----------------|
| **位置** | `intentos/apps/` | `intentos/agent/` |
| **基类** | `AppBase` | `AIAgent` |
| **能力管理** | 硬编码在应用中 | `CapabilityRegistry` |
| **意图处理** | 直接匹配 | 编译为 PEF |
| **MCP 支持** | 有限 | 原生支持 |
| **Skill 支持** | 有限 | 原生支持 |

---

## 新架构快速开始

### 1. 定义能力

```python
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
    return {"city": city, "temperature": "25°C"}
```

### 2. 创建 Agent

```python
from intentos.agent import AIAgent, AgentContext

agent = AIAgent()
await agent.initialize()

context = AgentContext(user_id="user123")
```

### 3. 执行意图

```python
result = await agent.execute("北京天气怎么样", context)
print(result.message)  # ✓ 执行成功
print(result.data)     # {"city": "北京", "temperature": "25°C"}
```

---

## 完整新架构文档

请查看以下文档了解新架构：

1. **[应用开发指南 - 语言即软件](./APP_DEVELOPMENT_GUIDE.md)**
   - 范式转变：从"编写"到"定义"
   - 五步创建应用流程
   - 完整示例

2. **[应用层架构与 AI Agent 实现](./APPS_ARCHITECTURE.md)**
   - 新 AI Agent 实现 (v10.0+)
   - MCP 集成详解
   - Skill 集成详解

3. **[Self-Bootstrap 机制](./SELF_BOOTSTRAP.md)**
   - 三大技术定理
   - 元意图层级结构
   - 超界即生长机制

---

## 旧架构参考 (保留)

### 应用元数据

```python
@app_metadata(
    app_id="unique_id",
    name="应用名称",
    description="应用描述",
    version="1.0.0",
    category="分类",
    icon="📱",
    author="作者"
)
```

### 生命周期方法

```python
class MyApp(AppBase):
    async def initialize(self, services) -> bool:
        await super().initialize(services)
        return True

    async def shutdown(self) -> None:
        pass
```

### 执行方法

```python
async def execute(self, intent: str, context: AppContext) -> AppResult:
    return AppResult(
        success=True,
        message="✓ 完成",
        data={"key": "value"},
    )
```

### 意图模板

```python
from intentos.apps import IntentTemplate

IntentTemplate(
    id="template_id",
    name="模板名称",
    keywords=["关键词"],
    patterns=[r"正则.*表达式"],
    category="my_app",
)
```

---

## 迁移指南

### 从旧架构迁移到新架构

**旧方式**:
```python
class MyApp(AppBase):
    async def execute(self, intent, context):
        if "天气" in intent:
            return self.query_weather(...)
```

**新方式**:
```python
@registry.register(
    id="weather_query",
    name="天气查询",
    tags=["weather"],
)
def query_weather(city: str):
    return {"temperature": "25°C"}

# Agent 自动匹配和执行
agent = AIAgent()
await agent.execute("北京天气")
```

### 迁移步骤

1. 将能力提取为独立函数
2. 使用 `@registry.register` 装饰器注册
3. 创建 `AIAgent` 实例
4. 移除硬编码的意图匹配逻辑

---

## 总结

**旧架构** (`intentos/apps/`) 已移至 `intentos/deprecated/apps/`，建议所有新应用使用**新架构** (`intentos/agent/`)。

**新架构核心优势**:
✓ 基于能力注册 (而非硬编码)
✓ 意图编译为 PEF
✓ 原生支持 MCP 和 Skills
✓ 清晰的模块职责

**查看新文档**: [应用开发指南 - 语言即软件](./APP_DEVELOPMENT_GUIDE.md) 🚀
