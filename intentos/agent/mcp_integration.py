"""
MCP 集成

支持 Model Context Protocol (MCP) 工具
"""

from __future__ import annotations

from typing import Any, Optional
from .registry import CapabilityRegistry


class MCPIntegration:
    """
    MCP 集成
    
    连接和管理 MCP 服务器，将 MCP Tools 注册为能力
    """
    
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self.servers: dict[str, Any] = {}
    
    async def connect_server(
        self,
        name: str,
        command: str,
        args: list[str] = None
    ) -> bool:
        """
        连接 MCP 服务器
        
        Args:
            name: 服务器名称
            command: 启动命令
            args: 命令参数
        
        Returns:
            是否成功
        """
        import asyncio
        
        try:
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
            await self._send_request(name, "initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "IntentOS",
                    "version": "1.0.0",
                },
            })
            
            # 获取工具列表并注册
            tools = await self.list_tools(name)
            for tool in tools:
                await self._register_mcp_tool(name, tool)
            
            return True
        except Exception as e:
            print(f"连接 MCP 服务器失败：{name}, 错误：{e}")
            return False
    
    async def disconnect_server(self, name: str) -> bool:
        """断开 MCP 服务器"""
        if name in self.servers:
            server = self.servers[name]
            server["process"].terminate()
            del self.servers[name]
            return True
        return False
    
    async def _send_request(
        self,
        name: str,
        method: str,
        params: dict
    ) -> Any:
        """发送 JSON-RPC 请求"""
        import json
        import asyncio
        
        if name not in self.servers:
            return None
        
        server = self.servers[name]
        server["message_id"] += 1
        
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
    
    async def list_tools(self, name: str) -> list[dict]:
        """列出 MCP 工具"""
        result = await self._send_request(name, "tools/list", {})
        return result or []
    
    async def _register_mcp_tool(self, server_name: str, tool: dict) -> None:
        """注册 MCP 工具为能力"""
        tool_id = f"{server_name}_{tool['name']}"
        
        async def handler(**kwargs):
            return await self._send_request(
                server_name,
                "tools/call",
                {
                    "name": tool["name"],
                    "arguments": kwargs,
                }
            )
        
        self.registry.register(
            id=tool_id,
            name=tool.get("name", tool_id),
            description=tool.get("description", ""),
            handler=handler,
            input_schema=tool.get("inputSchema", {}),
            tags=["mcp", server_name],
            metadata={"server": server_name},
            source="mcp",
        )
    
    def get_connected_servers(self) -> list[str]:
        """获取已连接的服务器列表"""
        return list(self.servers.keys())
