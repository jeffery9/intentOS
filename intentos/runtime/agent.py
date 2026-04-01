"""
Runtime Agent (Full-Service Node Daemon with Elected PaaS)

每个节点都是全功能的 IntentOS 实例，但只有被选举的节点才能激活 PaaS 服务：
1. 分布式内核 (Distributed Semantic VM)
2. 物理执行层 (AI Agent / IO)
3. 选举式 PaaS 能力 - 只有被选举的节点才能激活
4. 外部 REST API (v1 API)
5. 实时聊天接口 (Chat Interface)

架构理念:
- 不是所有节点都有 PaaS 能力
- 通过选举机制，指定部分节点成为 PaaS 层
- 只有被选举的节点才能激活 PaaS 服务
- 支持动态选举/罢免 PaaS 节点
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from aiohttp import web

from intentos.interface.interface import IntentOS
from intentos.paas.tenant import TenantManager, RoleManager, get_tenant_manager
from intentos.paas.metering import MeteringService, get_metering_service
from intentos.paas.wallet import DigitalWallet, PaymentGateway, get_payment_gateway
from intentos.paas.marketplace import AppMarketplace, get_marketplace

logger = logging.getLogger(__name__)


class DistributedPaaS:
    """
    分布式 PaaS 能力集合
    
    仅在被选举的节点上激活，提供：
    - 多租户管理
    - 用量计量
    - 钱包计费
    - 应用市场
    """
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self._active = False
        
        # PaaS 服务（懒加载，仅激活时初始化）
        self._tenant_manager: Optional[TenantManager] = None
        self._role_manager: Optional[RoleManager] = None
        self._metering_service: Optional[MeteringService] = None
        self._payment_gateway: Optional[PaymentGateway] = None
        self._marketplace: Optional[AppMarketplace] = None
        
        logger.info(f"分布式 PaaS 初始化完成 (node={node_id}, 待选举激活)")
    
    def activate(self) -> None:
        """激活 PaaS 服务（仅当节点被选举后调用）"""
        if not self._active:
            self._tenant_manager = get_tenant_manager()
            self._role_manager = RoleManager()
            self._metering_service = get_metering_service()
            self._payment_gateway = get_payment_gateway()
            self._marketplace = get_marketplace()
            self._active = True
            logger.info(f"PaaS 服务已激活 (node={self.node_id})")
    
    def deactivate(self) -> None:
        """休眠 PaaS 服务（节点被罢免时调用）"""
        if self._active:
            self._tenant_manager = None
            self._role_manager = None
            self._metering_service = None
            self._payment_gateway = None
            self._marketplace = None
            self._active = False
            logger.info(f"PaaS 服务已休眠 (node={self.node_id})")
    
    @property
    def is_active(self) -> bool:
        return self._active
    
    @property
    def tenant_manager(self) -> TenantManager:
        self._ensure_active()
        return self._tenant_manager
    
    @property
    def role_manager(self) -> RoleManager:
        self._ensure_active()
        return self._role_manager
    
    @property
    def metering_service(self) -> MeteringService:
        self._ensure_active()
        return self._metering_service
    
    @property
    def payment_gateway(self) -> PaymentGateway:
        self._ensure_active()
        return self._payment_gateway
    
    @property
    def marketplace(self) -> AppMarketplace:
        self._ensure_active()
        return self._marketplace
    
    def _ensure_active(self) -> None:
        if not self._active:
            raise RuntimeError("PaaS 服务未激活，节点未被选举")
    
    def get_tenant_context(self, tenant_id: str, user_id: str) -> dict:
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"租户不存在：{tenant_id}")
        
        user_context = self.role_manager.create_user_context(
            tenant_id=tenant_id,
            user_id=user_id,
        )
        
        return {
            "tenant": tenant.to_dict(),
            "user": user_context.to_dict(),
            "quota_remaining": {
                "gas": tenant.quota.total_gas_limit - tenant.cumulative_gas_used,
                "cpu": tenant.quota.cpu_seconds - tenant.current_cpu_used,
            },
        }
    
    async def record_usage(self, tenant_id: str, user_id: str, usage: dict) -> None:
        meter = self.metering_service.get_or_create_meter(user_id, session_id=f"{self.node_id}")
        if "tokens" in usage:
            meter.record_tokens(usage["tokens"])
        if "cpu_ms" in usage:
            meter.record_cpu(usage["cpu_ms"])
        
        gas_used = usage.get("gas", 0)
        if gas_used > 0:
            self.tenant_manager.report_gas_usage(tenant_id, gas_used)
    
    def get_usage_report(self, tenant_id: str) -> dict:
        return self.tenant_manager.get_usage_stats(tenant_id)


class PaaSNodeElector:
    """
    PaaS 节点选举器
    
    管理集群中哪些节点被选举为 PaaS 层。
    只有被选举的节点才能激活 PaaS 服务。
    
    支持：
    - 选举节点成为 PaaS 层
    - 罢免 PaaS 节点
    - 故障转移和自动重选举
    """
    
    def __init__(self, node_id: str, is_elected: bool = False):
        self.node_id = node_id
        self.is_elected = is_elected  # 本节点是否被选举为 PaaS 层
        self.paas_nodes: set[str] = set()  # 集群中所有 PaaS 节点
        self.primary_paas_node: Optional[str] = None
        
        if is_elected:
            self.paas_nodes.add(node_id)
            self.primary_paas_node = node_id
            logger.info(f"节点 {node_id} 已被选举为 PaaS 节点")
        else:
            logger.info(f"节点 {node_id} 是普通节点，未被选举为 PaaS 层")
    
    def elect_as_paas(self, node_id: str) -> None:
        """选举节点成为 PaaS 层"""
        self.paas_nodes.add(node_id)
        if not self.primary_paas_node:
            self.primary_paas_node = node_id
        if node_id == self.node_id:
            self.is_elected = True
            logger.info(f"本节点 {node_id} 被选举为 PaaS 节点")
        else:
            logger.info(f"节点 {node_id} 被选举为 PaaS 节点")
    
    def remove_from_paas(self, node_id: str) -> None:
        """罢免 PaaS 节点"""
        self.paas_nodes.discard(node_id)
        if node_id == self.node_id:
            self.is_elected = False
            logger.info(f"本节点 {node_id} 被罢免 PaaS 角色")
        if self.primary_paas_node == node_id:
            self.primary_paas_node = next(iter(self.paas_nodes), None)
            if self.primary_paas_node:
                logger.info(f"新主 PaaS 节点：{self.primary_paas_node}")
        logger.info(f"PaaS 节点 {node_id} 被罢免")
    
    def get_paas_nodes(self) -> list[str]:
        return list(self.paas_nodes)
    
    def get_primary_paas_node(self) -> Optional[str]:
        return self.primary_paas_node
    
    def is_paas_node(self, node_id: str) -> bool:
        return node_id in self.paas_nodes
    
    def should_forward_paas_request(self, target_node_id: Optional[str] = None) -> bool:
        """判断是否应该转发 PaaS 请求"""
        if not self.paas_nodes:
            return False
        if target_node_id:
            return target_node_id not in self.paas_nodes
        return self.node_id not in self.paas_nodes
    
    async def elect_primary(self) -> Optional[str]:
        """选举主 PaaS 节点"""
        if self.paas_nodes:
            self.primary_paas_node = next(iter(self.paas_nodes))
            logger.info(f"选举主 PaaS 节点：{self.primary_paas_node}")
        return self.primary_paas_node


class RuntimeAgent:
    """
    Runtime Agent: 每个节点都是对外服务的入口，只有被选举的节点才能激活 PaaS
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        host: str = "0.0.0.0",
        port: int = 8000,
        is_seed: bool = False,
        is_elected_paas: bool = False,  # 是否被选举为 PaaS 节点
    ):
        self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
        self.host = host
        self.port = port

        # 每个节点实例化一个主 IntentOS 对象
        self.os = IntentOS()
        self.is_seed = is_seed
        
        # PaaS 节点选举器
        self.paas_elector = PaaSNodeElector(self.node_id, is_elected=is_elected_paas)
        
        # PaaS 服务（仅被选举的节点才能激活）
        self.paas = DistributedPaaS(self.node_id)
        if is_elected_paas:
            self.paas.activate()

        # Web 服务器
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        # --- 1. 节点间 RPC 路由 (Internal) ---
        self.app.router.add_post("/rpc/execute", self.handle_rpc_execute)
        self.app.router.add_post("/rpc/memory/set", self.handle_rpc_memory_set)
        self.app.router.add_get("/rpc/status", self.handle_node_status)
        self.app.router.add_post("/rpc/paas/forward", self.handle_paas_forward)
        self.app.router.add_post("/rpc/paas/elect", self.handle_paas_elect)
        self.app.router.add_post("/rpc/paas/remove", self.handle_paas_remove)

        # --- 2. 对外公共 API (Public v1 API) ---
        self.app.router.add_post("/v1/execute", self.handle_v1_execute)
        self.app.router.add_get("/v1/status", self.handle_v1_status)
        self.app.router.add_get("/v1/nodes", self.handle_v1_nodes)
        self.app.router.add_get("/v1/registry", self.handle_v1_registry)
        
        # --- 3. PaaS API (仅被选举的节点可用) ---
        self.app.router.add_get("/v1/tenant/{tenant_id}", self.handle_v1_tenant_get)
        self.app.router.add_get("/v1/tenant/{tenant_id}/usage", self.handle_v1_tenant_usage)
        self.app.router.add_get("/v1/wallet/{user_id}", self.handle_v1_wallet_get)
        self.app.router.add_post("/v1/marketplace/install", self.handle_v1_marketplace_install)
        self.app.router.add_post("/v1/tenant", self.handle_v1_tenant_create)
        self.app.router.add_get("/v1/paas/nodes", self.handle_v1_paas_nodes)
        self.app.router.add_post("/v1/paas/elect", self.handle_v1_paas_elect)
        self.app.router.add_post("/v1/paas/remove", self.handle_v1_paas_remove)

        # --- 4. Chat 接口 (WebSocket) ---
        self.app.router.add_get("/v1/chat", self.handle_chat_ws)

    # --- 内部 RPC 处理 ---

    async def handle_rpc_execute(self, request: web.Request) -> web.Response:
        data = await request.json()
        from intentos.semantic_vm import SemanticProgram

        program = SemanticProgram.from_dict(data["program"])
        asyncio.create_task(self.os.vm.local_vm.execute_program(program.name, data.get("context")))
        return web.json_response({"status": "accepted"})

    async def handle_rpc_memory_set(self, request: web.Request) -> web.Response:
        data = await request.json()
        self.os.vm.local_vm.memory.set(data["store"], data["key"], data["value"])
        return web.json_response({"success": True})

    async def handle_node_status(self, request: web.Request) -> web.Response:
        status = self.os.vm.local_node.to_dict()
        status["paas"] = {
            "active": self.paas.is_active,
            "is_elected": self.paas_elector.is_elected,
            "paas_nodes": self.paas_elector.get_paas_nodes(),
            "primary_paas_node": self.paas_elector.get_primary_paas_node(),
        }
        if self.paas.is_active:
            status["paas"]["tenants_count"] = len(self.paas.tenant_manager.tenants)
            status["paas"]["active_sessions"] = len(self.paas.metering_service.meters)
        return web.json_response(status)

    async def handle_paas_elect(self, request: web.Request) -> web.Response:
        """选举节点成为 PaaS 层"""
        data = await request.json()
        target_node = data.get("node_id", self.node_id)
        self.paas_elector.elect_as_paas(target_node)
        if target_node == self.node_id:
            self.paas.activate()
        return web.json_response({
            "status": "elected",
            "node": target_node,
            "message": f"节点 {target_node} 已被选举为 PaaS 层",
        })

    async def handle_paas_remove(self, request: web.Request) -> web.Response:
        """罢免 PaaS 节点"""
        data = await request.json()
        target_node = data.get("node_id", self.node_id)
        self.paas_elector.remove_from_paas(target_node)
        if target_node == self.node_id:
            self.paas.deactivate()
        return web.json_response({
            "status": "removed",
            "node": target_node,
            "message": f"节点 {target_node} 已被罢免 PaaS 角色",
        })

    async def handle_paas_forward(self, request: web.Request) -> web.Response:
        """处理 PaaS 请求转发（普通节点转发到 PaaS 节点）"""
        if not self.paas.is_active:
            return web.json_response(
                {"error": "本节点 PaaS 服务未激活"},
                status=400,
            )
        
        # 转发请求到本地 PaaS 处理
        data = await request.json()
        action = data.get("action")
        params = data.get("params", {})
        
        # 根据 action 调用不同的 PaaS 方法
        result = await self._handle_paas_action(action, params)
        return web.json_response(result)

    async def _handle_paas_action(self, action: str, params: dict) -> dict:
        """处理 PaaS 动作"""
        if not self.paas.is_active:
            raise RuntimeError("本节点 PaaS 服务未激活")
        
        if action == "get_tenant":
            tenant = self.paas.tenant_manager.get_tenant(params["tenant_id"])
            return {"tenant": tenant.to_dict() if tenant else None}
        elif action == "get_usage":
            return {"usage": self.paas.get_usage_report(params["tenant_id"])}
        elif action == "get_wallet":
            wallet = self.paas.wallet_manager.get_wallet(params["user_id"])
            return {"wallet": wallet.to_dict() if wallet else None}
        elif action == "record_usage":
            await self.paas.record_usage(
                params["tenant_id"],
                params["user_id"],
                params["usage"],
            )
            return {"success": True}
        else:
            return {"error": f"未知 action: {action}"}

    # --- 对外 v1 API 处理 ---

    async def handle_v1_execute(self, request: web.Request) -> web.Response:
        """接收外部意图请求，利用分布式内核执行"""
        data = await request.json()
        intent_text = data.get("intent")
        tenant_id = data.get("tenant_id")
        user_id = data.get("user_id", "anonymous")

        # 租户验证和配额检查（转发到 PaaS 节点）
        if tenant_id and self.paas_elector.should_forward_paas_request():
            # 本节点不是 PaaS 节点，转发请求
            primary_node = self.paas_elector.get_primary_paas_node()
            if primary_node:
                # TODO: 实现跨节点转发
                logger.warning(f"PaaS 请求应转发到 {primary_node}，但暂未实现")

        # 调用 OS 接口层处理
        result = await self.os.execute(intent_text)
        
        # 记录用量（如果本节点 PaaS 已激活）
        if tenant_id and self.paas.is_active and result.get("usage"):
            await self.paas.record_usage(tenant_id, user_id, result["usage"])
        
        return web.json_response({"status": "success", "node": self.node_id, "result": result})

    async def handle_v1_status(self, request: web.Request) -> web.Response:
        """获取整个集群的视角状态"""
        status = await self.os.get_kernel_status()
        status["paas"] = {
            "type": "elected",
            "node_id": self.node_id,
            "active": self.paas.is_active,
            "is_elected": self.paas_elector.is_elected,
            "paas_nodes": self.paas_elector.get_paas_nodes(),
            "primary_paas_node": self.paas_elector.get_primary_paas_node(),
        }
        return web.json_response(status)

    async def handle_v1_nodes(self, request: web.Request) -> web.Response:
        """获取节点列表（含 PaaS 节点信息）"""
        nodes = await self.os.get_cluster_nodes()
        return web.json_response({
            "nodes": nodes,
            "paas_mode": "elected",
            "paas_nodes": self.paas_elector.get_paas_nodes(),
        })

    async def handle_v1_registry(self, request: web.Request) -> web.Response:
        return web.json_response(self.os.registry.introspect())

    # --- PaaS API 处理（PaaS 激活时可用，未激活返回 503）---

    async def _check_paas_active(self) -> Optional[web.Response]:
        """检查 PaaS 是否激活，未激活返回 503"""
        if not self.paas.is_active:
            return web.json_response(
                {"error": "本节点 PaaS 服务未激活，请先激活", "activate_endpoint": "/v1/paas/activate"},
                status=503,
            )
        return None

    async def handle_v1_tenant_get(self, request: web.Request) -> web.Response:
        """获取租户信息"""
        if err := await self._check_paas_active():
            return err
        tenant_id = request.match_info["tenant_id"]
        tenant = self.paas.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return web.json_response({"error": "租户不存在"}, status=404)
        return web.json_response(tenant.to_dict())

    async def handle_v1_tenant_usage(self, request: web.Request) -> web.Response:
        """获取租户用量"""
        if err := await self._check_paas_active():
            return err
        tenant_id = request.match_info["tenant_id"]
        usage = self.paas.get_usage_report(tenant_id)
        return web.json_response(usage)

    async def handle_v1_wallet_get(self, request: web.Request) -> web.Response:
        """获取钱包信息"""
        if err := await self._check_paas_active():
            return err
        user_id = request.match_info["user_id"]
        wallet = self.paas.wallet_manager.get_wallet(user_id)
        if not wallet:
            return web.json_response({"error": "钱包不存在"}, status=404)
        return web.json_response(wallet.to_dict())

    async def handle_v1_marketplace_install(self, request: web.Request) -> web.Response:
        """安装应用（分布式市场）"""
        if err := await self._check_paas_active():
            return err
        data = await request.json()
        app_id = data.get("app_id")
        tenant_id = data.get("tenant_id")
        
        if not app_id or not tenant_id:
            return web.json_response({"error": "缺少 app_id 或 tenant_id"}, status=400)
        
        try:
            app = await self.paas.marketplace.get_app(app_id)
            self.paas.tenant_manager.add_capability(tenant_id, app.to_capability())
            return web.json_response({"status": "installed", "app": app.to_dict()})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=404)

    async def handle_v1_tenant_create(self, request: web.Request) -> web.Response:
        """创建租户"""
        if err := await self._check_paas_active():
            return err
        data = await request.json()
        tenant_id = data.get("tenant_id")
        name = data.get("name")
        plan = data.get("plan", "free")
        
        if not tenant_id or not name:
            return web.json_response({"error": "缺少 tenant_id 或 name"}, status=400)
        
        try:
            tenant = self.paas.tenant_manager.create_tenant(tenant_id, name, plan)
            return web.json_response({"status": "created", "tenant": tenant.to_dict()})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)

    async def handle_v1_paas_nodes(self, request: web.Request) -> web.Response:
        """获取 PaaS 节点列表"""
        return web.json_response({
            "paas_nodes": self.paas_elector.get_paas_nodes(),
            "primary_paas_node": self.paas_elector.get_primary_paas_node(),
            "is_elected": self.paas_elector.is_elected,
            "is_active": self.paas.is_active,
        })

    async def handle_v1_paas_elect(self, request: web.Request) -> web.Response:
        """选举节点成为 PaaS 层（v1 API）"""
        data = await request.json()
        target_node = data.get("node_id", self.node_id)
        self.paas_elector.elect_as_paas(target_node)
        if target_node == self.node_id:
            self.paas.activate()
        return web.json_response({
            "status": "elected",
            "node": target_node,
            "message": f"节点 {target_node} 已被选举为 PaaS 层",
        })

    async def handle_v1_paas_remove(self, request: web.Request) -> web.Response:
        """罢免 PaaS 节点（v1 API）"""
        data = await request.json()
        target_node = data.get("node_id", self.node_id)
        self.paas_elector.remove_from_paas(target_node)
        if target_node == self.node_id:
            self.paas.deactivate()
        return web.json_response({
            "status": "removed",
            "node": target_node,
            "message": f"节点 {target_node} 已被罢免 PaaS 角色",
        })

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

        # 如果不是种子节点，则需要连接并同步集群状态
        if not self.is_seed:
            logger.info("Connecting to cluster seed...")
            # 同步 PaaS 节点信息
            # await self.sync_paas_nodes()

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        paas_status = "PaaS 已激活 (被选举)" if self.paas.is_active else "普通节点 (未被选举)"
        logger.info(f"✅ Full-Service Node {self.node_id} active at http://{self.host}:{self.port}")
        logger.info(f"   状态：{paas_status}")
        if self.paas.is_active:
            logger.info(f"   PaaS 能力：多租户、计量、计费、市场")

        # 保持运行
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            self.os.shutdown()


if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="IntentOS Runtime Agent")
    parser.add_argument("port", nargs="?", type=int, default=8000, help="端口号")
    parser.add_argument("--elected-paas", action="store_true", help="是否被选举为 PaaS 节点")
    parser.add_argument("--is-seed", action="store_true", help="是否为种子节点")
    args = parser.parse_args()

    agent = RuntimeAgent(port=args.port, is_elected_paas=args.elected_paas, is_seed=args.is_seed)
    asyncio.run(agent.start())
