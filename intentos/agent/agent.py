"""
AI Agent 主实现

基于意图包和能力注册，支持 MCP 和 Skill
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .compiler import IntentCompiler
from .core import Agent, AgentConfig, AgentContext, AgentResult
from .errors import (
    AgentException,
    ErrorCode,
    ErrorHandler,
)
from .executor import AgentExecutor, ExecutionMonitor
from .mcp_integration import MCPIntegration
from .registry import CapabilityRegistry
from .skill_integration import SkillIntegration

logger: logging.Logger = logging.getLogger(__name__)


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
        self.compiler: IntentCompiler = IntentCompiler(enable_cache=True, enable_optimization=True)
        self.executor: Optional[AgentExecutor] = None
        self.mcp: Optional[MCPIntegration] = None
        self.skills: Optional[SkillIntegration] = None
        self._monitor: Optional[ExecutionMonitor] = None

    async def initialize(self) -> bool:
        """初始化 Agent"""
        await super().initialize()

        # 注册内置能力
        self._register_builtin_capabilities()

        # 创建执行器（启用监控）
        self.executor = AgentExecutor(
            self.registry,
            llm_processor=None,  # 可传入 LLM Processor
            enable_monitoring=True
        )
        self._monitor = self.executor.get_monitor()

        # 初始化 MCP (如果启用)
        if self.config.enable_mcp:
            self.mcp = MCPIntegration(self.registry)

        # 初始化 Skills (如果启用)
        if self.config.enable_skills:
            self.skills = SkillIntegration(self.registry)
            await self._load_skills()

        logger.info("Agent 初始化完成")
        return True

    def _register_builtin_capabilities(self) -> None:
        """注册内置能力"""
        import shlex
        import subprocess
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
                raise AgentException(
                    ErrorCode.CAPABILITY_EXECUTION_FAILED,
                    f"Shell 执行失败：{e}",
                    details={"command": command}
                ) from e

        self.registry.register(
            id="shell",
            name="Shell 命令",
            description="执行 Shell 命令",
            handler=shell_exec,
            tags=["system", "shell"],
            required_permissions=["system:shell"],
            source="builtin",
        )

        # 计算器
        def calc(expression: str) -> dict[str, Any]:
            try:
                result: float = eval(expression, {"__builtins__": {}}, {})
                return {"success": True, "result": result}
            except Exception as e:
                raise AgentException(
                    ErrorCode.CAPABILITY_EXECUTION_FAILED,
                    f"计算失败：{e}",
                    details={"expression": expression}
                ) from e

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
                logger.info(f"加载 Skill: {skill_id}")

    async def execute(self, intent: str, context: AgentContext) -> AgentResult:
        """执行意图"""
        if not self.executor:
            return AgentResult(
                success=False,
                message="Agent 未初始化",
                error="agent_not_initialized"
            )

        try:
            # 编译意图为 PEF
            capabilities: list[str] = [cap.name for cap in self.registry.list_capabilities()]
            pef = self.compiler.compile(intent, capabilities, context.to_dict())

            # 执行 PEF
            result: AgentResult = await self.executor.execute(pef, context.to_dict())

            # 记录对话历史
            context.conversation_history.append({"role": "user", "content": intent})
            context.conversation_history.append({"role": "assistant", "content": result.message})

            return result

        except AgentException as e:
            logger.error(f"Agent 执行失败：{e}")
            return AgentResult(
                success=False,
                message=f"执行失败：{e.message}",
                error=e.code.value,
            )
        except Exception as e:
            logger.exception(f"Agent 执行异常：{e}")
            error = ErrorHandler.handle_error(e)
            return AgentResult(
                success=False,
                message=f"执行异常：{error.message}",
                error=error.code.value,
            )

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

    def get_monitor(self) -> Optional[ExecutionMonitor]:
        """获取执行监控器"""
        return self._monitor

    def get_compiler_stats(self) -> dict[str, Any]:
        """获取编译器统计"""
        return self.compiler.get_stats()
