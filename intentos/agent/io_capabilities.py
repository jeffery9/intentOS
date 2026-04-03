"""
IO 能力层 - Skill 和 MCP 的统一 IO 接口

架构定位:
- 内置能力 (builtin): OS 内核系统调用 (直接注册到 Registry)
- Skill: 用户态技能库 (通过 IO 能力动态调用)
- MCP: 外部协议工具 (通过 IO 协议访问)

设计原则:
- 语义 VM 通过 IO 能力调用 Skill 和 MCP
- 不预先注册所有 Skill/MCP, 而是按需加载
- IO 能力受 Capability Gate 保护
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..skill import SkillStore, get_skill_store
from ..skill.matcher import SkillMatcher

logger = logging.getLogger(__name__)


# =============================================================================
# Skill IO 能力
# =============================================================================


class SkillIOCapability:
    """
    Skill IO 能力 - 通过 IO 调用 Skill
    
    类似 Linux 的 `execve()` 系统调用, 允许执行用户态技能。
    """
    
    def __init__(self, registry: Any):
        """
        初始化 Skill IO 能力
        
        Args:
            registry: 能力注册中心
        """
        self.registry = registry
        self.skill_store: SkillStore = get_skill_store()
        self.skill_matcher = SkillMatcher()
    
    def register(self) -> None:
        """注册 Skill IO 能力到能力注册中心"""
        
        async def skill_io_handler(
            skill_id: Optional[str] = None,
            skill_name: Optional[str] = None,
            intent: Optional[str] = None,
            **kwargs: Any,
        ) -> Any:
            """
            Skill IO 处理器
            
            调用方式:
            1. 直接指定 skill_id
            2. 指定 skill_name
            3. 提供 intent, 自动匹配 Skill
            
            Args:
                skill_id: Skill ID (精确匹配)
                skill_name: Skill 名称 (模糊匹配)
                intent: 用户意图 (自动匹配)
                **kwargs: Skill 执行参数
            
            Returns:
                Skill 执行结果
            """
            # ① 查找 Skill
            skill = None
            
            if skill_id:
                skill = self.skill_store.get_skill(skill_id)
            elif skill_name:
                skills = self.skill_store.find_skills_by_name(skill_name)
                skill = skills[0] if skills else None
            elif intent:
                matches = self.skill_matcher.match_skills(intent)
                skill = matches[0]["skill"] if matches else None
            
            if not skill:
                raise ValueError(
                    f"Skill 未找到: "
                    f"skill_id={skill_id}, skill_name={skill_name}, intent={intent}"
                )
            
            # ② 执行 Skill
            logger.info(f"执行 Skill: {skill.name} ({skill.id})")
            result = await self._execute_skill(skill, **kwargs)
            
            return {
                "skill_id": skill.id,
                "skill_name": skill.name,
                "status": "success",
                "result": result,
            }
        
        # 注册 IO 能力
        self.registry.register(
            id="skill_io",
            name="Skill IO",
            description="通过 IO 调用 Skill (支持精确匹配/模糊匹配/意图自动匹配)",
            handler=skill_io_handler,
            input_schema={
                "skill_id": {"type": "string", "description": "Skill ID (精确匹配)"},
                "skill_name": {"type": "string", "description": "Skill 名称 (模糊匹配)"},
                "intent": {"type": "string", "description": "用户意图 (自动匹配)"},
            },
            tags=["io", "skill"],
            source="builtin",
            # 安全标注
            is_read_only=False,
            is_concurrency_safe=False,
        )
        
        logger.info("注册 Skill IO 能力")
    
    async def _execute_skill(self, skill: Any, **kwargs: Any) -> Any:
        """
        执行 Skill
        
        Args:
            skill: Skill 对象
            **kwargs: 执行参数
        
        Returns:
            执行结果
        """
        # TODO: 实现 Skill 执行逻辑
        # 1. 验证参数
        # 2. 执行 Skill 步骤
        # 3. 返回结果
        return {"status": "executed", "data": None}
    
    def list_skills(self) -> list[dict[str, Any]]:
        """列出所有可用 Skill"""
        skills = self.skill_store.list_skills()
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "level": s.level.value,
                "tags": s.tags,
            }
            for s in skills
        ]
    
    def match_skills(self, intent: str) -> list[dict[str, Any]]:
        """
        根据意图匹配 Skill
        
        Args:
            intent: 用户意图文本
        
        Returns:
            匹配的 Skill 列表 (带置信度)
        """
        skills = self.skill_store.list_skills()
        matches = self.skill_matcher.find_all_matches(skills, intent)
        
        return [
            {
                "skill_id": skill.id,
                "skill_name": skill.name,
                "confidence": confidence,
                "description": skill.description,
            }
            for skill, confidence in matches
        ]


# =============================================================================
# MCP IO 能力
# =============================================================================


class MCPIOCapability:
    """
    MCP IO 能力 - 通过 IO 调用 MCP 工具
    
    类似 Linux 的设备文件 (/dev/*), 通过标准协议访问外部工具。
    """
    
    def __init__(self, registry: Any):
        """
        初始化 MCP IO 能力
        
        Args:
            registry: 能力注册中心
        """
        self.registry = registry
        self.servers: dict[str, Any] = {}
    
    def register(self) -> None:
        """注册 MCP IO 能力到能力注册中心"""
        
        async def mcp_io_handler(
            server_name: str,
            tool_name: str,
            **kwargs: Any,
        ) -> Any:
            """
            MCP IO 处理器
            
            调用方式:
            1. 指定 server_name + tool_name
            2. 传递工具参数
            
            Args:
                server_name: MCP 服务器名称
                tool_name: MCP 工具名称
                **kwargs: 工具参数
            
            Returns:
                MCP 工具执行结果
            """
            # ① 检查服务器连接
            if server_name not in self.servers:
                raise ValueError(f"MCP 服务器未连接: {server_name}")
            
            # ② 调用 MCP 工具
            result = await self._call_mcp_tool(server_name, tool_name, kwargs)
            
            return {
                "server": server_name,
                "tool": tool_name,
                "status": "success",
                "result": result,
            }
        
        # 注册 IO 能力
        self.registry.register(
            id="mcp_io",
            name="MCP IO",
            description="通过 IO 调用 MCP 工具 (标准协议访问外部工具)",
            handler=mcp_io_handler,
            input_schema={
                "server_name": {"type": "string", "description": "MCP 服务器名称"},
                "tool_name": {"type": "string", "description": "MCP 工具名称"},
            },
            tags=["io", "mcp"],
            source="builtin",
            # 安全标注 (MCP 默认保守)
            is_read_only=False,
            is_concurrency_safe=False,
        )
        
        logger.info("注册 MCP IO 能力")
    
    async def connect_server(
        self,
        name: str,
        command: str,
        args: Optional[list[str]] = None,
    ) -> bool:
        """
        连接 MCP 服务器
        
        Args:
            name: 服务器名称
            command: 启动命令
            args: 命令参数
        
        Returns:
            是否连接成功
        """
        try:
            import asyncio
            import json
            
            # 启动子进程
            process = await asyncio.create_subprocess_exec(
                command,
                *(args or []),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            self.servers[name] = {
                "process": process,
                "message_id": 0,
            }
            
            # 发送初始化请求
            await self._send_request(
                name,
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "IntentOS",
                        "version": "1.0.0",
                    },
                },
            )
            
            logger.info(f"连接 MCP 服务器: {name}")
            return True
            
        except Exception as e:
            logger.error(f"连接 MCP 服务器失败: {name}, 错误: {e}")
            return False
    
    async def _send_request(
        self,
        name: str,
        method: str,
        params: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """发送 JSON-RPC 请求"""
        if name not in self.servers:
            return None
        
        server = self.servers[name]
        server["message_id"] += 1
        
        import json
        request = {
            "jsonrpc": "2.0",
            "id": server["message_id"],
            "method": method,
            "params": params,
        }
        
        # 发送
        request_bytes = (json.dumps(request) + "\n").encode()
        server["process"].stdin.write(request_bytes)
        await server["process"].stdin.drain()
        
        # 接收响应
        response_line = await server["process"].stdout.readline()
        if response_line:
            response = json.loads(response_line.decode())
            return response.get("result")
        
        return None
    
    async def _call_mcp_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        """调用 MCP 工具"""
        return await self._send_request(
            server_name,
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            },
        )
    
    def list_servers(self) -> list[str]:
        """列出已连接的 MCP 服务器"""
        return list(self.servers.keys())


# =============================================================================
# 统一 IO 能力层
# =============================================================================


class IOCapabilityLayer:
    """
    IO 能力层 - Skill 和 MCP 的统一 IO 接口
    
    语义 VM 通过 IO 能力层调用 Skill 和 MCP, 类似 Linux 的系统调用接口。
    
    架构:
    ┌─────────────────────────────────────────┐
    │  语义 VM (OS 内核)                       │
    │  ↓ 调用 IO 能力                         │
    ├─────────────────────────────────────────┤
    │  IO Capability Layer                    │
    │  ├─ skill_io: 调用 Skill                │
    │  └─ mcp_io: 调用 MCP 工具               │
    ├─────────────────────────────────────────┤
    │  Capability Gate (能力门控)              │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self, registry: Any):
        """
        初始化 IO 能力层
        
        Args:
            registry: 能力注册中心
        """
        self.registry = registry
        self.skill_io = SkillIOCapability(registry)
        self.mcp_io = MCPIOCapability(registry)
    
    def register_all(self) -> None:
        """注册所有 IO 能力"""
        self.skill_io.register()
        self.mcp_io.register()
        logger.info("IO 能力层注册完成")
    
    def get_stats(self) -> dict[str, Any]:
        """获取 IO 能力统计"""
        return {
            "skills": len(self.skill_io.list_skills()),
            "mcp_servers": len(self.mcp_io.list_servers()),
        }
