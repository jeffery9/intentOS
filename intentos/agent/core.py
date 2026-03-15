"""
AI Agent 核心定义
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str = "IntentOS Agent"
    version: str = "1.0.0"
    description: str = "AI 智能助理"
    capabilities: list[str] = field(default_factory=list)
    max_iterations: int = 10
    timeout: int = 300
    enable_mcp: bool = True
    enable_skills: bool = True


@dataclass
class AgentContext:
    """Agent 执行上下文"""
    user_id: str
    session_id: str = ""
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "conversation_history": self.conversation_history,
            "variables": self.variables,
            "created_at": self.created_at,
        }


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    message: str
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    artifacts: list[Any] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "artifacts": self.artifacts,
            "next_actions": self.next_actions,
        }


class Agent:
    """
    AI Agent 基类
    
    新的实现方式：基于意图包和能力注册，支持 MCP 和 Skill
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化 Agent"""
        self._initialized = True
        return True
    
    async def execute(
        self,
        intent: str,
        context: AgentContext
    ) -> AgentResult:
        """
        执行意图
        
        Args:
            intent: 用户意图
            context: 执行上下文
        
        Returns:
            执行结果
        """
        raise NotImplementedError("子类必须实现 execute 方法")
    
    async def shutdown(self) -> None:
        """关闭 Agent"""
        self._initialized = False
