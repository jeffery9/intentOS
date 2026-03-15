"""
AI Agent 主实现

基于意图包和能力注册，支持 MCP 和 Skill
"""

from __future__ import annotations

from typing import Any, Optional

from .core import Agent, AgentConfig, AgentContext, AgentResult
from .registry import CapabilityRegistry
from .mcp_integration import MCPIntegration
from .skill_integration import SkillIntegration
from .compiler import IntentCompiler
from .executor import AgentExecutor


class AIAgent(Agent):
    """
    AI Agent 实现
    
    支持:
    - 内置能力 (Shell/文件/计算器等)
    - MCP Tools (Model Context Protocol)
    - Skills (Claude Skills 规范)
    """
    
    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        super().__init__(config)
        self.registry: CapabilityRegistry = CapabilityRegistry()
        self.compiler: IntentCompiler = IntentCompiler()
        self.executor: Optional[AgentExecutor] = None
        self.mcp: Optional[MCPIntegration] = None
        self.skills: Optional[SkillIntegration] = None
    
    async def initialize(self) -> bool:
        """初始化 Agent"""
        await super().initialize()
        
        # 注册内置能力
        self._register_builtin_capabilities()
        
        # 创建执行器
        self.executor = AgentExecutor(self.registry)
        
        # 初始化 MCP (如果启用)
        if self.config.enable_mcp:
            self.mcp = MCPIntegration(self.registry)
        
        # 初始化 Skills (如果启用)
        if self.config.enable_skills:
            self.skills = SkillIntegration(self.registry)
            await self._load_skills()
        
        return True
    
    def _register_builtin_capabilities(self) -> None:
        """注册内置能力"""
        import subprocess
        import shlex
        from datetime import datetime
        
        # Shell
        def shell_exec(command: str, timeout: int = 30) -> dict[str, Any]:
            try:
                result = subprocess.run(
                    shlex.split(command),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=True,
                )
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        self.registry.register(
            id="shell",
            name="Shell 命令",
            description="执行 Shell 命令",
            handler=shell_exec,
            tags=["system", "shell"],
            source="builtin",
        )
        
        # 计算器
        def calc(expression: str) -> dict[str, Any]:
            try:
                result: float = eval(expression, {"__builtins__": {}}, {})
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        self.registry.register(
            id="calculator",
            name="计算器",
            description="数学计算",
            handler=calc,
            tags=["math"],
            source="builtin",
        )
        
        # 时间
        def get_time() -> dict[str, Any]:
            now: datetime = datetime.now()
            return {
                "success": True,
                "datetime": now.isoformat(),
                "time": now.strftime("%H:%M:%S"),
            }
        
        self.registry.register(
            id="current_time",
            name="当前时间",
            description="获取时间",
            handler=get_time,
            tags=["system", "time"],
            source="builtin",
        )
    
    async def _load_skills(self) -> None:
        """加载 Skills"""
        if self.skills:
            skill_ids: list[str] = self.skills.discover_skills()
            for skill_id in skill_ids:
                await self.skills.load_skill(skill_id)
    
    async def execute(self, intent: str, context: AgentContext) -> AgentResult:
        """执行意图"""
        if not self.executor:
            return AgentResult(success=False, error="Agent not initialized")
        
        capabilities: list[str] = [cap.name for cap in self.registry.list_capabilities()]
        pef = self.compiler.compile(intent, capabilities, context.to_dict())
        result: AgentResult = await self.executor.execute(pef, context.to_dict())
        
        context.conversation_history.append({"role": "user", "content": intent})
        context.conversation_history.append({"role": "assistant", "content": result.message})
        
        return result
    
    def get_capabilities(self) -> list[str]:
        """获取能力列表"""
        caps: list[str] = []
        for cap in self.registry.list_capabilities():
            caps.append(f"{cap.name} ({cap.source}): {cap.description}")
        return caps
    
    async def connect_mcp(
        self,
        name: str,
        command: str,
        args: Optional[list[str]] = None
    ) -> bool:
        """连接 MCP 服务器"""
        if self.mcp:
            return await self.mcp.connect_server(name, command, args)
        return False
    
    def get_loaded_skills(self) -> list[str]:
        """获取已加载的 Skills"""
        return self.skills.get_loaded_skills() if self.skills else []
