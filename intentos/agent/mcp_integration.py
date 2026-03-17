"""
MCP 集成

支持 Model Context Protocol (MCP) 工具
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MCPIntegration:
    """
    MCP 集成
    
    连接和管理 MCP 服务器，将 MCP Tools 注册为能力
    """
    
    def __init__(self, registry: Any):
        self.registry = registry
        self.servers: dict[str, dict[str, Any]] = {}
    
    async def connect_server(
        self,
        name: str,
        command: str,
        args: Optional[list[str]] = None
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
            tools: list[dict[str, Any]] = await self.list_tools(name)
            for tool in tools:
                await self._register_mcp_tool(name, tool)
            
            return True
        except Exception as e:
            logging.error(f"连接 MCP 服务器失败：{name}, 错误：{e}")
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
        params: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """发送 JSON-RPC 请求"""
        if name not in self.servers:
            return None
        
        server = self.servers[name]
        server["message_id"] += 1
        
        request: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": server["message_id"],
            "method": method,
            "params": params,
        }
        
        # 发送
        request_bytes: bytes = (json.dumps(request) + "\n").encode()
        server["process"].stdin.write(request_bytes)
        await server["process"].stdin.drain()
        
        # 接收响应
        response_line: bytes = await server["process"].stdout.readline()
        if response_line:
            response: dict[str, Any] = json.loads(response_line.decode())
            return response.get("result")
        
        return None
    
    async def list_tools(self, name: str) -> list[dict[str, Any]]:
        """列出 MCP 工具"""
        result: Optional[dict[str, Any]] = await self._send_request(name, "tools/list", {})
        return result or []
    
    async def _register_mcp_tool(self, server_name: str, tool: dict[str, Any]) -> None:
        """注册 MCP 工具为能力"""
        tool_id: str = f"{server_name}_{tool.get('name', 'unknown')}"
        
        async def handler(**kwargs: Any) -> dict[str, Any]:
            return await self._send_request(
                server_name,
                "tools/call",
                {
                    "name": tool.get("name"),
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

    async def setup_metered_api_gateway(self) -> Dict[str, Any]:
        """
        Simulates setting up a public-facing API Gateway with a metering layer.

        This gateway will route requests to the core IntentOS services
        and record usage for billing purposes.

        :return: A dictionary containing details of the simulated API Gateway.
        """
        logging.info("Setting up Metered API Gateway...")

        # Placeholder: In a real implementation, this would involve actual cloud SDK calls
        # to configure API Gateway, integrate with a metering service, and expose endpoints.
        
        gateway_details = {
            "endpoint": "https://api.intentos.com/v1",
            "status": "active",
            "capabilities_exposed": [],
            "metering_system": "active",
            "pricing_model": "pay-as-you-go",
            "metrics_dashboard": "https://monitor.intentos.com/metrics"
        }

        logging.info("Simulating exposure of registered capabilities through the metered API.")
        # In a real scenario, we would iterate through self.registry.list_capabilities()
        # and configure each one as an API endpoint, linking it to the metering system.
        for cap_id, capability in self.registry.list_capabilities().items():
            # For simulation, just add the capability ID to the list
            gateway_details["capabilities_exposed"].append(cap_id)

        logging.info(f"Metered API Gateway setup complete. Endpoint: {gateway_details['endpoint']}")
        return gateway_details
