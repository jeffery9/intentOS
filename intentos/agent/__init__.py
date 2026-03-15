"""
IntentOS AI Agent - 新一代实现

基于意图包和能力注册，支持 MCP 和 Skill
"""

from __future__ import annotations

from .core import Agent, AgentConfig, AgentContext, AgentResult
from .registry import CapabilityRegistry, Capability
from .mcp_integration import MCPIntegration
from .skill_integration import SkillIntegration
from .compiler import IntentCompiler, PEF
from .executor import AgentExecutor
from .agent import AIAgent

__all__: list[str] = [
    # 核心
    "Agent",
    "AgentConfig",
    "AgentContext",
    "AgentResult",
    
    # 注册
    "CapabilityRegistry",
    "Capability",
    
    # 集成
    "MCPIntegration",
    "SkillIntegration",
    
    # 编译执行
    "IntentCompiler",
    "PEF",
    "AgentExecutor",
    
    # Agent
    "AIAgent",
]
