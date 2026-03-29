# IntentOS for AI Assistants
# 为 GitHub Copilot、Cursor 等 AI 编程助手提供的上下文信息

# 项目类型
type: operating-system
category: ai-native

# 项目描述
description: |
  IntentOS 是一个 AI 原生分布式操作系统，将 LLM 视为"语义 CPU"。
  核心理念：语言即系统 · Prompt 即可执行文件 · 语义 VM

# 主要功能
features:
  - 语义虚拟机 (Semantic VM)
  - Self-Bootstrap 自我演进
  - 分布式内核
  - 意图编译器
  - 7 层套娃分层处理
  - Map-Reduce 分布式执行

# 技术栈
languages:
  - Python 3.9+
  
frameworks:
  - asyncio
  - aiohttp
  
llm_providers:
  - OpenAI
  - Anthropic
  - Ollama

# 代码组织
structure:
  intentos/semantic_vm/: 语义虚拟机核心
  intentos/distributed/: 分布式内核
  intentos/bootstrap/: Self-Bootstrap 模块
  intentos/compiler/: 意图编译器
  intentos/interface/: Shell/API/Chat接口
  intentos/llm/: LLM 后端层
  intentos/agent/: AI Agent
  intentos/runtime/: 运行时 Agent

# 常用命令
commands:
  启动 Shell: PYTHONPATH=. python intentos/interface/shell.py
  启动 API: PYTHONPATH=. python intentos/interface/api.py
  运行测试: pytest
  类型检查: mypy intentos --exclude deprecated/
  代码格式：ruff check . && ruff format .

# 代码示例
examples:
  基础使用: |
    from intentos import SemanticVM, create_executor
    
    executor = create_executor(provider="openai")
    vm = SemanticVM(executor)
    result = await vm.execute_program("my_program")

# 相关文档
documentation:
  - docs/ARCHITECTURE.md
  - docs/CORE_PRINCIPLES.md
  - docs/GET_STARTED.md
  - docs/LLM_DISCOVERY.md

# 许可证
license: MIT
