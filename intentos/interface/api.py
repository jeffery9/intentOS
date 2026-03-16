import os
from datetime import datetime

from aiohttp import web

from intentos.interface.interface import IntentOS


class IntentOSGateway:
    """
    IntentOS REST API Gateway (v1.0)

    内核与外部系统的统一 API 接口
    """

    def __init__(self, host="localhost", port=8080):
        self.os = IntentOS()
        self.os.initialize()
        self.host = host
        self.port = port
        self.app = web.Application(middlewares=[self.auth_middleware])
        self._setup_routes()

    @web.middleware
    async def auth_middleware(self, request, handler):
        """Token 认证中间件"""
        # 从环境变量获取 Token，默认为 intentos-secret-token
        token = os.environ.get("INTENTOS_API_TOKEN", "intentos-secret-token")
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {token}":
            return web.json_response(
                {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": "Unauthorized: Invalid or missing API Token"
                },
                status=401
            )
        
        return await handler(request)

    def _setup_routes(self):
        # 1. 执行层 (Execution)
        self.app.router.add_post("/v1/execute", self.handle_execute)

        # 2. 状态层 (Status & Health)
        self.app.router.add_get("/v1/status", self.handle_status)

        # 3. 存储层 (Storage & Memory)
        self.app.router.add_get("/v1/memory/{store}/{key}", self.handle_get_memory)
        self.app.router.add_post("/v1/memory", self.handle_set_memory)

        # 4. 资源层 (Registry)
        self.app.router.add_get("/v1/registry", self.handle_registry)

        # 5. 集群层 (Nodes)
        self.app.router.add_get("/v1/nodes", self.handle_list_nodes)
        self.app.router.add_post("/v1/nodes", self.handle_add_node)

        # 6. 审计层 (Audit)
        self.app.router.add_get("/v1/audit", self.handle_audit)

    # --- Handlers ---

    async def handle_execute(self, request):
        """执行自然语言意图"""
        try:
            data = await request.json()
            intent = data.get("intent")
            if not intent:
                return self._error_response("Missing 'intent' field", 400)

            result = await self.os.execute(intent)
            return self._success_response({"result": result})
        except Exception as e:
            return self._error_response(str(e))

    async def handle_status(self, request):
        """获取内核详细状态"""
        status = await self.os.get_kernel_status()
        return self._success_response(
            {
                "kernel_version": "8.1",
                "uptime": "n/a",
                "cluster": status["cluster"],
                "memory_state": status["memory"],
            }
        )

    async def handle_get_memory(self, request):
        """读取语义内存"""
        store = request.match_info["store"].upper()
        key = request.match_info["key"]
        value = await self.os.vm.memory.get(store, key)
        return self._success_response({"store": store, "key": key, "value": value})

    async def handle_set_memory(self, request):
        """写入语义内存"""
        try:
            data = await request.json()
            store = data.get("store", "").upper()
            key = data.get("key")
            value = data.get("value")
            if not all([store, key, value is not None]):
                return self._error_response("Missing required fields", 400)

            await self.os.vm.memory.set(store, key, value)
            return self._success_response({"message": "Memory updated"})
        except Exception as e:
            return self._error_response(str(e))

    async def handle_registry(self, request):
        """获取资源注册信息"""
        reg = self.os.registry.introspect()
        return self._success_response(reg)

    async def handle_list_nodes(self, request):
        """列出集群节点"""
        nodes = self.os.vm.memory.get_nodes()
        return self._success_response([n.to_dict() for n in nodes])

    async def handle_add_node(self, request):
        """添加新节点"""
        try:
            data = await request.json()
            host, port = data.get("host"), data.get("port")
            if not host or not port:
                return self._error_response("Missing host/port", 400)

            node = await self.os.vm.add_node(host, int(port))
            return self._success_response(node.to_dict())
        except Exception as e:
            return self._error_response(str(e))

    async def handle_audit(self, request):
        """获取自举审计历史"""
        history = self.os.bootstrap.get_bootstrap_history(limit=50)
        return self._success_response([r.to_dict() for r in history])

    # --- Utils ---

    def _success_response(self, data):
        return web.json_response(
            {"status": "success", "timestamp": datetime.now().isoformat(), "data": data}
        )

    def _error_response(self, message, status=500):
        return web.json_response(
            {"status": "error", "timestamp": datetime.now().isoformat(), "error": message},
            status=status,
        )

    def run(self):
        print(f"IntentOS Gateway starting on http://{self.host}:{self.port}")
        web.run_app(self.app, host=self.host, port=self.port)


if __name__ == "__main__":
    gateway = IntentOSGateway()
    gateway.run()
