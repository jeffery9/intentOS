# IntentOS 应用层架构与 AI Agent 实现指南

## 概述

在 IntentOS 的架构体系中，**应用层（Apps Layer）** 位于三层调用架构的最顶部，是开发者构建具体功能和用户直接交互的场所。

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Application Layer (应用层)                         │
│  • 领域意图包                                                │
│  • 用户交互                                                  │
│  • 结果呈现                                                  │
└───────────────┬─────────────────────────────────────────────┘
                ↓ 调用意图
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 2: IntentOS Layer (意图层 - 7 Level 处理流程)          │
│  [L1] 意图解析 → [L2] 任务规划 → [L3] 上下文收集 →           │
│  [L4] 安全验证 → [L5] 能力绑定 → [L6] 执行 → [L7] 改进       │
└───────────────┬─────────────────────────────────────────────┘
                ↓ Prompt 执行 (Semantic Opcode)
┌───────────────▼─────────────────────────────────────────────┐
│  Layer 3: Model Layer (模型层 - LLM Processor)               │
│  • 语义 CPU (LLM)                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 一、Apps 层（应用层）的职责

应用层是**面向用户的意图入口**，其核心职责是实现从业务逻辑到系统能力的映射。具体职责包括：

### 1. 封装领域意图包 (Domain Intent Packages)

应用层负责定义和封装特定业务领域的**意图模板（Intent Templates）**和**能力（Capabilities）**。意图包是 AI 原生应用的核心载体，包含了将自然语言转化为结构化逻辑的代码和描述。

**意图包结构**:
```
intent-package/
├── SKILL.md              # 意图包元数据和规范
├── intents/              # 意图模板定义
│   ├── schedule.yaml
│   └── email.yaml
├── capabilities/         # 能力定义
│   ├── api_client.py
│   └── llm_tool.py
└── resources/            # 资源文件
    ├── prompts/
    └── templates/
```

### 2. 提供用户交互接口

通过多模态交互界面（如对话、图表、表单、交互式 Shell 或 REST API）接收人类的自然语言意图。在 AI 原生范式下，用户不再通过点击按钮，而是通过"表达目标"来驱动系统。

**交互方式**:
```python
# 1. 交互式 Shell
from intentos.interface import IntentShell
shell = IntentShell()
await shell.run()

# 2. REST API
POST /v1/execute
{
    "intent": "分析华东区销售数据",
    "context": {"user_id": "user123"}
}

# 3. Python SDK
from intentos.apps import AIAgentApp
agent = AIAgentApp()
result = await agent.execute("分析销售数据", context)
```

### 3. 结果呈现与渲染

将系统执行后的结果（如数据视图、artifacts）渲染为用户友好的形式。界面在这一层不再是固定的容器，而是可随语言意图即时派生和重建的"表达层"。

**渲染示例**:
```python
# 数据可视化
if result.data.get('chart'):
    render_chart(result.data['chart'])

# 文本摘要
if result.data.get('summary'):
    display_summary(result.data['summary'])

# 可执行 Artifact
if result.artifacts:
    for artifact in result.artifacts:
        yield artifact
```

### 4. 管理高维抽象层

管理用户目标的语义解析、能力图谱的映射、动态上下文（Context）的建模以及执行结构（Executable Structure）的生成。

**上下文管理**:
```python
from intentos.core import Context

context = Context(
    user_id="user123",
    session_id="session_abc",
    history=[...],  # 对话历史
    preferences={...},  # 用户偏好
)
```

---

## 二、如何实现 AI Agent

在 IntentOS 中，实现 AI Agent 不再是编写传统的硬编码逻辑，而是通过构建**意图包（Intent Package）**并将其注册到系统内核（意图层）中。

### 1. 构建意图包的核心组件

开发者需要通过以下结构化单位来构建 Agent：

#### 意图模板 (Intent Templates)
定义如何将自然语言转化为结构化逻辑的源代码层级。

```python
from intentos.apps.template import IntentTemplate

schedule_template = IntentTemplate(
    id="schedule_meeting",
    name="安排会议",
    description="安排会议、设置提醒",
    keywords=["会议", "安排", "预约", "提醒"],
    category="schedule",
)
```

#### 自然语言描述
封装人类的自然语言意图，作为系统处理的输入源。

```python
# 用户输入
intent = "安排明天下午 3 点的产品评审会"

# 系统解析
parsed = {
    "type": "schedule",
    "entities": {
        "time": "明天下午 3 点",
        "event": "产品评审会",
    }
}
```

#### 能力定义与注册
声明 Agent 需要调用的外部工具或 API（如查订单、发邮件等技能）。

```python
from intentos.apps.services.tools import ToolRegistry

registry = ToolRegistry()

@registry.register(
    id="send_email",
    name="发送邮件",
    description="发送电子邮件",
    handler=send_email_handler,
    tags=["communication", "email"],
)
def send_email_handler(to: str, subject: str, body: str) -> dict:
    """发送邮件处理函数"""
    ...
```

#### 符号与链接信息
提供给链接器（Linker）的元数据，用于在编译阶段将指令与能力绑定。

```python
# PEF (Prompt Executable File) 结构
pef = {
    "version": "1.0",
    "metadata": {...},
    "sections": {
        "prompt": {...},
        "capabilities": [
            {"name": "send_email", "binding": "..."},
        ],
        "constraints": {...},
    }
}
```

### 2. 实现的具体步骤

实现过程遵循从"声明"到"绑定"的标准化流程：

#### 步骤 1: 定义能力 (Define Capabilities)

通过**声明式描述**定义 Agent 的技能，包括名称、描述、输入/输出 Schema 以及具体的执行实现（如 HTTP API、Python 函数或 LLM 工具）。

```python
from intentos.apps.services.tools import ToolRegistry

registry = ToolRegistry()

# 定义 Shell 执行工具
registry.register(
    id="shell",
    name="Shell 命令",
    description="执行 Shell 命令（支持 bash/zsh）",
    handler=shell_execute,
    tags=["system", "shell", "command"],
    params_schema={
        "command": {"type": "string", "description": "要执行的命令"},
        "timeout": {"type": "number", "default": 30},
    }
)

# 定义文件读取工具
registry.register(
    id="file_read",
    name="读取文件",
    description="读取文件内容",
    handler=file_read,
    tags=["file", "io"],
)

# 定义 HTTP 请求工具
registry.register(
    id="http_request",
    name="HTTP 请求",
    description="发送 HTTP/HTTPS 请求",
    handler=http_request,
    tags=["network", "http", "api"],
)
```

#### 步骤 2: 向注册中心登记 (Registration)

在应用创建阶段将能力列表传入系统，或通过**元意图（Meta-Intent）**动态驱动能力的注册。

```python
from intentos.apps import AIAgentApp

# 创建 AI Agent
agent = AIAgentApp()
await agent.initialize()

# 自动注册所有内置工具
# - Shell 命令
# - 文件操作
# - HTTP 请求
# - 计算器
# - 当前时间
```

#### 步骤 3: 编译为 PEF 文件 (Compilation)

意图包作为**意图编译器**的输入，经过词法、语法和语义分析。编译器通过**套娃分层架构（L1-L5）**将模糊意图精化为可在"语义 CPU"上运行的**指令流**。

最终产物是 **PEF (Prompt Executable File)**，即 Agent 的"二进制"可执行文件。

```python
from intentos.compiler import IntentCompiler

compiler = IntentCompiler()

# 编译意图
pef = compiler.compile(
    intent="执行 ls -la 命令",
    context=context,
)

# PEF 输出
{
    "system_prompt": "你是 Shell 执行助手...",
    "user_prompt": "执行：ls -la",
    "capabilities": ["shell"],
    "constraints": {...},
}
```

#### 步骤 4: 链接与执行 (Linking & Execution)

**链接器 (Linker)** 实时将 PEF 指令与注册的能力绑定。

**语义虚拟机 (SVM)** 加载 PEF，并驱动作为运算器的 LLM 执行指令流，最终完成任务并产生反馈。

```python
from intentos.semantic_vm import SemanticVM

vm = SemanticVM()

# 加载 PEF
await vm.load_program(pef)

# 执行
result = await vm.execute()

# 输出
print(result.data)  # Shell 命令输出
```

---

## 三、完整示例：实现 Shell 工具支持

### 1. 定义工具

```python
# intentos/apps/services/tools.py

def shell_execute(command: str, timeout: int = 30, shell: str = "bash") -> dict:
    """执行 Shell 命令"""
    import subprocess
    import shlex
    
    try:
        args = shlex.split(command)
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=(shell == "bash"),
        )
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# 注册工具
registry.register(
    id="shell",
    name="Shell 命令",
    description="执行 Shell 命令（支持 bash/zsh）",
    handler=shell_execute,
    tags=["system", "shell", "command"],
)
```

### 2. 意图理解与匹配

```python
# intentos/apps/ai_agent.py

def _match_tool(self, intent: str) -> Optional[dict]:
    """匹配需要调用的工具"""
    intent_lower = intent.lower()
    
    # Shell 命令匹配
    shell_keywords = ["执行", "运行", "run", "execute", "终端", "shell"]
    
    if any(kw in intent_lower for kw in shell_keywords):
        import re
        patterns = [r'["\']([^"\']+)["\']', r'执行 (.+)', r'运行 (.+)']
        
        for pattern in patterns:
            match = re.search(pattern, intent)
            if match:
                return {
                    "id": "shell",
                    "name": "Shell 命令",
                    "params": {"command": match.group(1).strip()},
                }
    
    return None
```

### 3. 工具调用

```python
async def _call_tool(self, tool_id: str, params: dict) -> dict:
    """调用工具"""
    if not self.tool_registry:
        return {"success": False, "error": "工具系统未初始化"}
    
    result = await self.tool_registry.call(tool_id, **params)
    return result

# 使用示例
result = await agent.execute("执行 pwd", AppContext())
# → 输出当前目录
```

---

## 四、总结

在 IntentOS 体系中，实现 Agent 的本质是**设计一套意图协议和能力集合**。

### 开发者职责
- 定义"Agent 能做什么"（意图模板）
- 声明能力（工具注册）
- 提供执行逻辑（处理函数）

### IntentOS 内核职责
- "如何调度 LLM 和工具去实现它"
- 意图编译（自然语言 → PEF）
- 能力绑定（链接器）
- 执行调度（语义 VM）

### 核心优势

| 传统开发 | IntentOS AI Agent |
|---------|------------------|
| 硬编码逻辑 | 声明式意图 |
| 固定 UI | 动态生成界面 |
| 手动调用 API | 自动能力绑定 |
| 编译后运行 | 即时编译执行 |

**在 IntentOS 中，Agent 是通过意图协议和能力集合"生长"出来的，而不是"编写"出来的！** 🚀✨
