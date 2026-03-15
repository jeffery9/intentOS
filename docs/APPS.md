# IntentOS 应用架构

## 统一应用管理

所有应用（包括 AI Agent）都通过统一的应用管理器管理。

## 架构设计

```
intentos/apps/
├── __init__.py          # 导出所有应用
├── base.py              # 应用基类和应用管理器
├── cli.py               # 统一命令行界面
├── ai_agent.py          # AI 智能助理应用
├── data_analyst.py      # 数据分析师应用
├── content_creator.py   # 内容创作应用
├── code_assistant.py    # 编程助手应用
└── automation.py        # 工作流自动化应用
```

## 应用基类

```python
from intentos.apps import IntentApp

class MyCustomApp(IntentApp):
    def __init__(self):
        super().__init__(
            id="my_app",
            name="我的应用",
            description="应用描述",
            category="productivity",
            icon="🚀",
        )
    
    def get_capabilities(self) -> list[str]:
        return ["能力 1", "能力 2"]
    
    async def execute(self, intent: str, context: dict = None) -> dict:
        return {"success": True, "message": "完成"}
```

## 使用方式

### 1. 命令行

```bash
python -m intentos.apps.cli
```

### 2. Python API

```python
from intentos.apps import AppManager, AIAgentApp

# 创建管理器
manager = AppManager()

# 注册应用
manager.register_app(AIAgentApp())

# 激活应用
await manager.activate_app("ai_agent")

# 执行应用
result = await manager.execute_app("ai_agent", "安排明天下午 3 点的会议")
```

## 内置应用

| 应用 | ID | 描述 |
|------|----|------|
| **🤖 AI 智能助理** | `ai_agent` | 通用智能助理，处理各种任务 |
| **📊 数据分析师** | `data_analyst` | 用自然语言分析数据 |
| **✍️ 内容创作** | `content_creator` | 生成文章、报告、文案 |
| **💻 编程助手** | `code_assistant` | 代码生成、审查、调试 |
| **⚙️ 工作流自动化** | `automation` | 自动执行重复任务 |

## 应用路由

CLI 会根据关键词自动选择合适的应用：

| 关键词 | 应用 |
|--------|------|
| 会议/安排/预约/邮件 | AI 智能助理 |
| 销售/分析/数据/图表 | 数据分析师 |
| 文章/写/内容 | 内容创作 |
| 代码/编程/函数 | 编程助手 |
| 自动/每天/定时 | 工作流自动化 |

## 开发自定义应用

1. 继承 `IntentApp` 基类
2. 实现 `get_capabilities()` 和 `execute()` 方法
3. 注册到应用管理器

```python
from intentos.apps import IntentApp, AppManager

class MyApp(IntentApp):
    def __init__(self):
        super().__init__(
            id="my_app",
            name="我的应用",
            description="描述",
            category="custom",
            icon="⭐",
        )
    
    def get_capabilities(self) -> list[str]:
        return ["自定义能力"]
    
    async def execute(self, intent: str, context: dict = None) -> dict:
        return {"success": True, "data": {}}

# 注册
manager = AppManager()
manager.register_app(MyApp())
```

## 总结

**统一的应用架构让 IntentOS 更容易扩展和管理！**

- ✅ 统一的接口
- ✅ 插件化设计
- ✅ 易于扩展
- ✅ 自动路由
