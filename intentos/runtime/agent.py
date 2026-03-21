"""
Runtime Agent (Full-Service Node Daemon)

每个节点都是一个全功能的 IntentOS 实例，提供：
1. 分布式内核 (Distributed VM)
2. 物理执行层 (AI Agent / IO)
3. 外部 REST API (v1 API)
4. 实时聊天接口 (Chat Interface)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from aiohttp import web

from intentos.interface.interface import IntentOS

logger = logging.getLogger(__name__)

class RuntimeAgent:
    """
    Runtime Agent: 每个节点都是对外服务的入口
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        host: str = "0.0.0.0",
        port: int = 8000,
        is_seed: bool = False
    ):
        self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
        self.host = host
        self.port = port

        # 每个节点实例化一个主 IntentOS 对象
        # 它会自动包含分布式 VM、注册中心和接口
        self.os = IntentOS()
        self.is_seed = is_seed

        # Web 服务器
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        # --- 1. 节点间 RPC 路由 (Internal) ---
        self.app.router.add_post("/rpc/execute", self.handle_rpc_execute)
        self.app.router.add_post("/rpc/memory/set", self.handle_rpc_memory_set)
        self.app.router.add_get("/rpc/status", self.handle_node_status)

        # --- 2. 对外公共 API (Public v1 API) ---
        self.app.router.add_post("/v1/execute", self.handle_v1_execute)
        self.app.router.add_get("/v1/status", self.handle_v1_status)
        self.app.router.add_get("/v1/registry", self.handle_v1_registry)

        # --- 3. Chat 接口 (WebSocket) ---
        self.app.router.add_get("/v1/chat", self.handle_chat_ws)

    # --- 内部 RPC 处理 ---

    async def handle_rpc_execute(self, request: web.Request) -> web.Response:
        data = await request.json()
        from intentos.semantic_vm import SemanticProgram
        program = SemanticProgram.from_dict(data["program"])
        # 在本地 VM 执行
        asyncio.create_task(self.os.vm.local_vm.execute_program(program.name, data.get("context")))
        return web.json_response({"status": "accepted"})

    async def handle_rpc_memory_set(self, request: web.Request) -> web.Response:
        data = await request.json()
        self.os.vm.local_vm.memory.set(data["store"], data["key"], data["value"])
        return web.json_response({"success": True})

    async def handle_node_status(self, request: web.Request) -> web.Response:
        return web.json_response(self.os.vm.local_node.to_dict())

    # --- 对外 v1 API 处理 ---

    async def handle_v1_execute(self, request: web.Request) -> web.Response:
        """接收外部意图请求，利用分布式内核执行"""
        data = await request.json()
        intent_text = data.get("intent")

        # 调用 OS 接口层处理
        result = await self.os.execute(intent_text)
        return web.json_response({
            "status": "success",
            "node": self.node_id,
            "result": result
        })

    async def handle_v1_status(self, request: web.Request) -> web.Response:
        """获取整个集群的视角状态"""
        status = await self.os.get_kernel_status()
        return web.json_response(status)

    async def handle_v1_registry(self, request: web.Request) -> web.Response:
        return web.json_response(self.os.registry.introspect())

    # --- WebSocket Chat 处理 ---

    async def handle_chat_ws(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        logger.info(f"Chat connection established on node {self.node_id}")

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # 作为一个 AI Native OS，对话即执行
                response = await self.os.execute(msg.data)
                await ws.send_str(response)
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WS error: {ws.exception()}")

        return ws

    async def start(self):
        """启动节点并加入集群"""
        self.os.initialize()
        await self.os.start_background_services()

        # 如果不是种子节点，则需要连接并同步集群状态（此处逻辑可扩展）
        if not self.is_seed:
            logger.info("Connecting to cluster seed...")
            # await self.sync_with_seed()

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        logger.info(f"✅ Full-Service Node {self.node_id} active at http://{self.host}:{self.port}")

        # 保持运行
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            self.os.shutdown()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    agent = RuntimeAgent(port=port)
    asyncio.run(agent.start())
