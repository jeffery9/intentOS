# IntentOS 快速开始指南

> **语言即系统 · Prompt 即可执行文件 · 语义 VM**

欢迎使用 IntentOS！本指南将帮助你在 5 分钟内开始使用 AI 原生操作系统。

---

## 目录

- [5 分钟快速开始](#5-分钟快速开始)
- [核心概念](#核心概念)
- [安装指南](#安装指南)
- [使用示例](#使用示例)
- [进阶用法](#进阶用法)
- [故障排查](#故障排查)
- [下一步](#下一步)

---

## 5 分钟快速开始

### 步骤 1: 安装

```bash
# 克隆仓库
git clone https://github.com/jeffery9/intentOS.git
cd intentOS

# 安装依赖
pip install -e .
```

### 步骤 2: 运行第一个示例

```python
# example.py
import asyncio
from intentos.agent import AIAgent, AgentContext

async def main():
    # 创建 Agent
    agent = AIAgent()
    await agent.initialize()
    
    # 创建上下文
    context = AgentContext(user_id="demo")
    
    # 执行意图
    result = await agent.execute("列出当前目录的文件", context)
    print(f"结果：{result.message}")
    print(f"数据：{result.data}")

asyncio.run(main())
```

运行：
```bash
python example.py
```

输出：
```
结果：✓ 执行成功
数据：{"files": ["example.py", "README.md", ...]}
```

**恭喜！你已经成功运行了第一个 IntentOS 应用！** 🎉

---

## 核心概念

### 1. 语言即系统

用户通过**自然语言**与系统交互，无需学习复杂的 API：

```python
# 传统方式
os.system("ls -la")
subprocess.run(["ls", "-la"])

# IntentOS 方式
await agent.execute("列出当前目录的所有文件，包括隐藏文件")
```

### 2. Prompt 即可执行文件

IntentOS 将自然语言编译为 **PEF (Prompt Executable File)**：

```
用户输入："计算 123 乘以 456"
    ↓
PEF 编译:
{
    "intent": "计算 123 乘以 456",
    "system_prompt": "你是一个数学助手...",
    "capabilities": ["计算器"],
    ...
}
    ↓
执行并返回：{"result": 56088}
```

### 3. 语义 VM

LLM 作为**语义 CPU**执行 PEF：

```
┌─────────────────────────────────────┐
│  语义 VM                            │
├─────────────────────────────────────┤
│  • LLM Processor (语义 CPU)         │
│  • Memory System (语义内存)         │
│  • Instruction Set (语义指令集)     │
└─────────────────────────────────────┘
```

---

## 安装指南

### 系统要求

- Python 3.10+
- pip 21.0+
- 1GB+ 可用内存

### 基础安装

```bash
# 从 GitHub 安装
pip install git+https://github.com/jeffery9/intentOS.git

# 或克隆后安装
git clone https://github.com/jeffery9/intentOS.git
cd intentOS
pip install -e .
```

### 验证安装

```bash
python -c "from intentos.agent import AIAgent; print('✓ 安装成功')"
```

### 可选依赖

```bash
# MCP 支持（可选）
pip install aiohttp

# 完整功能
pip install "intentos[all]"
```

---

## 使用示例

### 示例 1: 基础使用

```python
import asyncio
from intentos.agent import AIAgent, AgentContext

async def demo():
    # 1. 创建 Agent
    agent = AIAgent()
    await agent.initialize()
    
    # 2. 创建上下文
    context = AgentContext(user_id="user123")
    
    # 3. 执行意图
    intents = [
        "列出当前目录的 Python 文件",
        "计算 (123 + 456) * 789",
        "现在几点了",
    ]
    
    for intent in intents:
        print(f"\n用户：{intent}")
        result = await agent.execute(intent, context)
        print(f"Agent: {result.message}")
        if result.data:
            print(f"数据：{result.data}")

asyncio.run(demo())
```

### 示例 2: 使用 MCP

```python
import asyncio
from intentos.agent import AIAgent, AgentContext

async def demo():
    agent = AIAgent(enable_mcp=True)
    await agent.initialize()
    
    # 连接 MCP 服务器
    await agent.connect_mcp(
        name="weather",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-weather"],
    )
    
    context = AgentContext(user_id="user123")
    
    # 使用 MCP 工具
    result = await agent.execute("北京天气怎么样", context)
    print(result.data)

asyncio.run(demo())
```

### 示例 3: 使用 Skills

```python
import asyncio
from intentos.agent import AIAgent, AgentContext

async def demo():
    agent = AIAgent(enable_skills=True)
    await agent.initialize()
    
    # 查看已加载的 Skills
    skills = agent.get_loaded_skills()
    print(f"已加载 {len(skills)} 个 Skills:")
    for skill in skills:
        print(f"  • {skill}")
    
    context = AgentContext(user_id="user123")
    
    # 使用 Skill
    result = await agent.execute("创建内容策略", context)
    print(result.data)

asyncio.run(demo())
```

### 示例 4: 自定义能力

```python
import asyncio
from intentos.agent import AIAgent, AgentContext

async def demo():
    agent = AIAgent()
    await agent.initialize()
    
    # 注册自定义能力
    @agent.registry.register(
        id="greeting",
        name="问候",
        description="打招呼",
        tags=["问候", "打招呼"],
        source="builtin",
    )
    def greeting(name: str) -> dict:
        return {"message": f"你好，{name}！"}
    
    context = AgentContext(user_id="user123")
    
    # 使用自定义能力
    result = await agent.execute("跟我打个招呼，我叫小明", context)
    print(result.data)  # {"message": "你好，小明！"}

asyncio.run(demo())
```

### 示例 5: 监控和指标

```python
import asyncio
from intentos.agent import AIAgent, AgentContext

async def demo():
    agent = AIAgent()
    await agent.initialize()
    context = AgentContext(user_id="user123")
    
    # 执行多次
    for i in range(10):
        await agent.execute("计算 123 * 456", context)
    
    # 获取监控数据
    monitor = agent.get_monitor()
    metrics = monitor.get_metrics()
    
    print(f"总执行：{metrics['total_executions']}")
    print(f"成功率：{metrics['success_rate']*100:.2f}%")
    print(f"P90 延迟：{metrics['p90_latency_ms']:.2f}ms")
    print(f"缓存命中：{metrics['cache_hits']}")
    
    # 获取能力使用统计
    cap_stats = monitor.get_capability_stats()
    print(f"能力使用：{cap_stats}")

asyncio.run(demo())
```

---

## 进阶用法

### 1. 配置 Agent

```python
from intentos.agent import AgentConfig, AIAgent

config = AgentConfig(
    name="My Agent",
    enable_mcp=True,       # 启用 MCP
    enable_skills=True,    # 启用 Skills
    max_iterations=10,     # 最大迭代次数
    timeout=300,           # 超时时间（秒）
)

agent = AIAgent(config)
await agent.initialize()
```

### 2. 上下文管理

```python
from intentos.agent import AgentContext

# 创建带历史的上下文
context = AgentContext(
    user_id="user123",
    session_id="session_abc",
    conversation_history=[
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮你的？"},
    ],
    variables={"preferred_language": "zh-CN"},
)
```

### 3. 错误处理

```python
from intentos.agent import AgentException, ErrorCode

try:
    result = await agent.execute("意图", context)
    if not result.success:
        print(f"执行失败：{result.error}")
except AgentException as e:
    print(f"错误码：{e.code.value}")
    print(f"错误消息：{e.message}")
    print(f"详细信息：{e.details}")
```

### 4. 性能优化

```python
# 启用 PEF 缓存
from intentos.agent import IntentCompiler

compiler = IntentCompiler(
    enable_cache=True,      # 启用缓存
    enable_optimization=True,  # 启用优化
)

# 清空缓存
compiler.clear_cache()

# 获取缓存统计
stats = compiler.get_stats()
print(f"缓存命中率：{stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) * 100:.2f}%")
```

---

## 故障排查

### 问题 1: 导入错误

```bash
# 错误：ModuleNotFoundError: No module named 'intentos'

# 解决：
pip install -e .
```

### 问题 2: Agent 初始化失败

```python
# 错误：Agent initialization failed

# 解决：检查依赖
python -c "from intentos.agent import AIAgent; print('OK')"

# 检查日志
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 问题 3: 能力匹配不准确

```python
# 解决：使用 LLM 语义匹配
from intentos.agent import AgentExecutor

executor = AgentExecutor(
    registry,
    llm_processor=your_llm,  # 传入 LLM Processor
)
```

### 问题 4: MCP 连接失败

```bash
# 错误：MCP connection failed

# 解决：
# 1. 检查 npx 是否安装
which npx

# 2. 检查 MCP 服务器
npx -y @modelcontextprotocol/server-weather --help

# 3. 检查网络连接
curl -I https://registry.npmjs.org
```

### 问题 5: Skill 加载失败

```bash
# 错误：Skill load failed

# 解决：
# 1. 检查 SKILL.md 格式
cat ~/.claude/skills/your-skill/SKILL.md

# 2. 验证 YAML 格式
python -c "import yaml; yaml.safe_load(open('SKILL.md'))"

# 3. 检查文件权限
ls -la ~/.claude/skills/your-skill/
```

---

## 下一步

恭喜你完成快速开始！接下来可以：

### 学习资源

- 📖 [应用开发指南](./APP_DEVELOPMENT_GUIDE.md) - 学习如何开发应用
- 📖 [愿景实现文档](./VISION_IMPLEMENTATION.md) - 了解核心愿景
- 📖 [架构文档](./APPS_ARCHITECTURE.md) - 深入理解架构

### 实践项目

1. **创建你的第一个能力**
   ```python
   @agent.registry.register(...)
   def my_capability(...):
       ...
   ```

2. **连接 MCP 服务器**
   ```python
   await agent.connect_mcp("weather", "npx", [...])
   ```

3. **加载 Skills**
   ```bash
   mkdir -p ~/.claude/skills/my-skill
   # 创建 SKILL.md
   ```

### 社区

- 💬 加入讨论
- 🐛 报告问题
- 💡 提出建议

---

## 总结

你现在已经掌握了 IntentOS 的基础知识：

✅ 安装和配置  
✅ 基础使用  
✅ 核心概念  
✅ 进阶用法  
✅ 故障排查  

**开始构建你的 AI 原生应用吧！** 🚀✨

---

**最后更新**: 2026-03-16  
**版本**: v10.1
