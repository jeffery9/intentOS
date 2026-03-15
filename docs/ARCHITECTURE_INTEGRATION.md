# IntentOS 架构集成说明

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户界面层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Chat TUI   │  │  REST API   │  │  Shell CLI  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
└─────────┼────────────────┼────────────────┼─────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│              Layer 1: Application Layer (应用层)              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  intentos/apps/                                      │    │
│  │  ├── base.py         # 应用基类 (AppBase)            │    │
│  │  ├── ai_agent.py     # AI Agent 应用                 │    │
│  │  ├── manager.py      # 应用层管理器                  │    │
│  │  ├── registry.py     # 应用注册表                    │    │
│  │  ├── template.py     # 意图模板                      │    │
│  │  ├── router.py       # 意图路由器                    │    │
│  │  └── services/       # 应用服务                      │    │
│  │      ├── llm_provider.py  # LLM 后端                 │    │
│  │      ├── memory.py        # 记忆系统                 │    │
│  │      ├── knowledge.py     # 知识库                  │    │
│  │      └── tools.py         # 工具注册                │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          ↓ 调用意图
┌─────────────────────────────────────────────────────────────┐
│              Layer 2: IntentOS Layer (意图层)                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  intentos/                                           │    │
│  │  ├── kernel/engine.py     # 内核执行引擎             │    │
│  │  ├── semantic_vm/vm.py    # 语义虚拟机               │    │
│  │  ├── engine/engine.py     # 执行引擎                 │    │
│  │  ├── compiler/          # 编译器                     │    │
│  │  └── registry/          # 意图注册表                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  7 Level 处理流程:                                           │
│  L1 意图解析 → L2 任务规划 → L3 上下文收集 →                │
│  L4 安全验证 → L5 能力绑定 → L6 执行 → L7 改进              │
└─────────────────────────┬───────────────────────────────────┘
                          ↓ Prompt 执行
┌─────────────────────────────────────────────────────────────┐
│              Layer 3: LLM Layer (模型层)                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  intentos/llm/                                       │    │
│  │  ├── backends/                                       │    │
│  │  │   ├── openai_backend.py   # OpenAI               │    │
│  │  │   ├── anthropic_backend.py # Anthropic           │    │
│  │  │   ├── ollama_backend.py    # Ollama              │    │
│  │  │   └── mock_backend.py      # Mock                │    │
│  │  └── executor.py           # LLM 执行器              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Apps 层与内核集成方式

### 1. 应用通过内核执行

```python
# intentos/interface/chat_tui.py (TUI 层)
from intentos.kernel.engine import get_kernel, ExecutionRequest

# 获取内核
kernel = get_kernel()

# 创建执行请求
request = ExecutionRequest(
    intent="安排明天下午 3 点的会议",
    context=Context(user_id="user123"),
)

# 通过内核执行
response = await kernel.execute(request)

# 显示结果
print(response.message)
```

**流程**:
```
TUI → Kernel Engine → IntentOS 内核 → 语义 VM → LLM → 结果
```

### 2. AI Agent 作为应用层组件

```python
# intentos/apps/ai_agent.py
from .base import AppBase, app_metadata

@app_metadata(
    app_id="ai_agent",
    name="AI 智能助理",
    category="productivity",
)
class AIAgentApp(AppBase):
    """AI Agent 应用"""
    
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        # 1. 理解意图 (调用 LLM 服务)
        understanding = await self.services.call_llm(...)
        
        # 2. 根据意图类型执行
        if intent_type == "schedule":
            result = await self._handle_schedule(intent)
        
        # 3. 返回结果
        return AppResult(success=True, message="✓ 完成")
```

### 3. 应用层服务调用内核

```python
# intentos/apps/services/llm_provider.py
from intentos.llm.executor import LLMExecutor

class LLMProvider:
    """LLM 提供者服务"""
    
    async def chat(self, messages, **kwargs) -> str:
        # 调用内核的 LLM 执行器
        executor = LLMExecutor()
        response = await executor.execute(messages)
        return response.content
```

### 4. 意图模板路由到内核能力

```python
# intentos/apps/template.py
class IntentTemplate:
    """意图模板"""
    
    def match(self, text: str) -> tuple[bool, dict]:
        # 匹配用户输入
        # 例如："安排会议" → schedule 能力
        pass

# intentos/apps/router.py
class IntentRouter:
    """意图路由器"""
    
    async def route(self, intent: str) -> AppResult:
        # 1. 匹配模板
        template = self.template_registry.match_intent(intent)
        
        # 2. 路由到内核能力
        if template.action == "schedule":
            # 调用内核的日程管理能力
            result = await self.kernel.execute("schedule", intent)
        
        return result
```

---

## 集成点详解

### 集成点 1: Kernel Engine

**位置**: `intentos/kernel/engine.py`

**作用**: 连接应用层和内核

```python
class KernelEngine:
    """内核执行引擎"""
    
    def __init__(self):
        self.registry = IntentRegistry()      # 内核注册表
        self.vm = SemanticVM()                # 语义 VM
        self.engine = ExecutionEngine()       # 执行引擎
    
    async def execute(self, request: ExecutionRequest) -> ExecutionResponse:
        # 1. 创建意图对象
        intent = Intent(
            name="user_request",
            intent_type=IntentType.ATOMIC,
            goal=request.intent,
            context=request.context,
        )
        
        # 2. 通过内核执行
        result = await self.engine.execute(intent)
        
        # 3. 返回结果
        return ExecutionResponse(success=True, result=result)
```

### 集成点 2: AppLayer Manager

**位置**: `intentos/apps/manager.py`

**作用**: 管理应用层，连接到内核

```python
class AppLayer:
    """应用层管理器"""
    
    def __init__(self):
        self.app_registry = AppRegistry()
        self.template_registry = TemplateRegistry()
        self.router = IntentRouter()
        self.services = AppServices()
    
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        # 通过路由器执行
        return await self.router.route(intent, context)
```

### 集成点 3: AppServices

**位置**: `intentos/apps/app_services.py`

**作用**: 为应用提供内核服务

```python
class AppServices:
    """应用服务"""
    
    async def call_llm(self, prompt: str) -> str:
        """调用 LLM(通过内核)"""
        from intentos.llm.executor import LLMExecutor
        executor = LLMExecutor()
        return await executor.generate(prompt)
    
    async def execute_capability(self, name: str, **kwargs) -> Any:
        """执行能力 (通过内核)"""
        from intentos.kernel.engine import get_kernel
        kernel = get_kernel()
        response = await kernel.execute(ExecutionRequest(
            intent=name,
            context=AppContext(),
        ))
        return response.result
```

---

## 完整执行流程示例

### 示例：用户说"安排明天下午 3 点的会议"

```
1. 用户输入
   ↓
2. Chat TUI (interface/chat_tui.py)
   - 显示用户消息
   - 创建 ExecutionRequest
   ↓
3. Kernel Engine (kernel/engine.py)
   - 创建 Intent 对象
   - 调用 ExecutionEngine
   ↓
4. IntentOS 内核 (engine/engine.py)
   - 编译意图 (compiler)
   - 生成 PEF
   ↓
5. 语义 VM (semantic_vm/vm.py)
   - 解析 PEF
   - 调用 LLM
   ↓
6. LLM Layer (llm/executor.py)
   - 调用 OpenAI/Anthropic
   - 生成响应
   ↓
7. 结果返回
   LLM → 语义 VM → 内核 → Kernel Engine → TUI → 用户
```

---

## 应用开发集成

### 开发新应用

```python
# my_app.py
from intentos.apps import AppBase, app_metadata

@app_metadata(
    app_id="my_app",
    name="我的应用",
    description="应用描述",
)
class MyApp(AppBase):
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        # 通过内核服务执行
        result = await self.services.call_llm(f"处理：{intent}")
        return AppResult(success=True, message=result)

# 注册到应用层
from intentos.apps import get_app_layer

layer = get_app_layer()
layer.register_app(MyApp())
```

### 应用调用内核能力

```python
class MyApp(AppBase):
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        # 方式 1: 通过服务调用
        llm_result = await self.services.call_llm(intent)
        
        # 方式 2: 通过内核执行
        from intentos.kernel.engine import get_kernel
        kernel = get_kernel()
        response = await kernel.execute(ExecutionRequest(
            intent=intent,
            context=context,
        ))
        
        return AppResult(success=True, message=response.message)
```

---

## 总结

### 集成层次

| 层次 | 模块 | 职责 |
|------|------|------|
| **UI 层** | `interface/chat_tui.py` | 用户交互 |
| **应用层** | `apps/*` | 应用框架、服务 |
| **内核层** | `kernel/engine.py` | 执行引擎 |
| **意图层** | `engine/*`, `semantic_vm/*` | 意图处理 |
| **模型层** | `llm/*` | LLM 后端 |

### 集成方式

1. **应用通过内核执行** - 不直接调用 LLM
2. **服务封装内核调用** - 统一接口
3. **意图路由到能力** - 内核注册表
4. **结果逐层返回** - 统一响应格式

### 关键设计

- ✅ **分层清晰** - UI/App/Kernel/Intent/LLM
- ✅ **统一接口** - ExecutionRequest/Response
- ✅ **松耦合** - 层与层之间通过接口通信
- ✅ **可扩展** - 易于添加新应用和能力

**Apps 层通过 Kernel Engine 与 IntentOS 内核集成！** 🔗✨
