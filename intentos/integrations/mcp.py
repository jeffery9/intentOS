"""
MCP (Model Context Protocol) 客户端

支持标准 MCP 协议的服务器
https://modelcontextprotocol.io/

MCP 是一个开放协议，用于 AI 模型与外部数据源和工具的标准化集成。
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional


class MCPClient:
    """
    MCP (Model Context Protocol) 客户端

    支持标准 MCP 协议的服务器
    https://modelcontextprotocol.io/
    """

    def __init__(self):
        self.servers: dict[str, Any] = {}

    async def connect(
        self,
        name: str,
        command: str,
        args: list[str] = None
    ) -> bool:
        """
        连接到 MCP 服务器

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

            return True
        except Exception as e:
            print(f"连接 MCP 服务器失败：{name}, 错误：{e}")
            return False

    async def disconnect(self, name: str) -> bool:
        """断开连接"""
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
        """列出工具"""
        result = await self._send_request(name, "tools/list", {})
        return result or []

    async def call_tool(
        self,
        name: str,
        tool_name: str,
        arguments: dict
    ) -> Any:
        """调用工具"""
        result = await self._send_request(name, "tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        return result

    async def list_resources(self, name: str) -> list[dict]:
        """列出资源"""
        result = await self._send_request(name, "resources/list", {})
        return result or []

    async def read_resource(self, name: str, uri: str) -> str:
        """读取资源"""
        result = await self._send_request(name, "resources/read", {"uri": uri})
        if result and "contents" in result:
            return result["contents"][0].get("text", "")
        return ""

    async def list_prompts(self, name: str) -> list[dict]:
        """列出提示"""
        result = await self._send_request(name, "prompts/list", {})
        return result or []

    async def get_prompt(
        self,
        name: str,
        prompt_name: str,
        arguments: dict
    ) -> str:
        """获取提示"""
        result = await self._send_request(name, "prompts/get", {
            "name": prompt_name,
            "arguments": arguments,
        })
        if result and "messages" in result:
            return result["messages"][0].get("content", "")
        return ""


# ========== 单例 ==========

_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """获取 MCP 客户端"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
