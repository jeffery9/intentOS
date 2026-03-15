"""
IntentOS 应用层 (Layer 1)

遵循 3 层 7 级架构的应用层设计

架构层次:
┌─────────────────────────────────────┐
│  Layer 1: Application Layer (应用层) │ ← 本层
│  • 领域意图包                        │
│  • 用户交互                          │
│  • 结果呈现                          │
└───────────────┬─────────────────────┘
                ↓ 调用意图
┌───────────────▼─────────────────────┐
│  Layer 2: IntentOS Layer (意图层)    │
│  • 7 Level 处理流程                  │
└───────────────┬─────────────────────┘
                ↓ Prompt 执行
┌───────────────▼─────────────────────┐
│  Layer 3: LLM Layer (模型层)         │
│  • 语义 CPU (LLM Processor)          │
└─────────────────────────────────────┘

应用层职责:
1. 提供应用开发基础框架
2. 定义应用接口规范
3. 管理应用生命周期
4. 提供通用服务 (日志/配置/存储)
5. 意图路由和分发
"""

from __future__ import annotations

from .base import AppBase, AppContext, AppResult
from .registry import AppRegistry
from .template import IntentTemplate, TemplateRegistry
from .router import IntentRouter
from .app_services import AppServices
from .manager import AppLayer, get_app_layer
from .ai_agent import AIAgentApp

__version__ = "1.0.0"
__all__ = [
    "AppBase",
    "AppContext",
    "AppResult",
    "AppRegistry",
    "IntentTemplate",
    "TemplateRegistry",
    "IntentRouter",
    "AppServices",
    "AppLayer",
    "get_app_layer",
    "AIAgentApp",
]
