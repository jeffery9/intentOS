#!/usr/bin/env python3
"""
IntentOS REST API 网关 - 客户端模式

提供 HTTP API 接口，转发请求到运行中的 IntentOS 内核
"""

import argparse
import os
from datetime import datetime

from aiohttp import web


class IntentOSGateway:
    """
    IntentOS REST API Gateway

    支持两种模式：
    1. 服务器模式：直接使用内核实例（集成到 daemon）
    2. 客户端模式：通过 RPC 连接到内核（独立运行）
    """

    def __init__(self, os_instance=None, host="localhost", port=8080):
        self.os = os_instance  # 服务器模式使用
        self.host = host
        self.port = port
        self._client = None  # 客户端模式使用

        # 延迟导入
        try:
            from aiohttp import web
            self.web = web
        except ImportError:
            print("❌ 错误：需要安装 aiohttp")
            print("   运行：pip install aiohttp")
            import sys
            sys.exit(1)

        self.app = web.Application(middlewares=[self.auth_middleware])
        self._setup_routes()

    @web.middleware
    async def auth_middleware(self, request, handler):
        """Token 认证中间件"""
        token = os.environ.get("INTENTOS_API_TOKEN", "intentos-secret-token")
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != f"Bearer {token}":
            return self.web.json_response(
                {
                    "status": "error",
                    "timestamp": datetime.now().isoformat(),
                    "error": "Unauthorized: Invalid or missing API Token"
                },
                status=401
            )
        return await handler(request)

    def _setup_routes(self):
        self.app.router.add_post("/v1/execute", self.handle_execute)
        self.app.router.add_get("/v1/status", self.handle_status)
        self.app.router.add_get("/v1/health", self.handle_health)
        self.app.router.add_get("/v1/nodes", self.handle_list_nodes)

    async def _get_client(self):
        """获取 RPC 客户端"""
        if self._client is None:
            from intentos.interface.ipc import RPCClient
            self._client = RPCClient(socket_path=self.socket_path)
            await self._client.connect()
        return self._client

    async def handle_execute(self, request):
        """执行自然语言意图"""
        try:
            data = await request.json()
            intent = data.get("intent")
            if not intent:
                return self._error_response("Missing 'intent' field", 400)

            if self.os:
                # 服务器模式：直接使用内核
                result = await self.os.execute(intent)
            else:
                # 客户端模式：通过 RPC
                client = await self._get_client()
                result = await client.execute(intent)
            
            return self._success_response({"result": result})
        except Exception as e:
            return self._error_response(str(e))

    async def handle_status(self, request):
        """获取内核状态"""
        try:
            if self.os:
                # 服务器模式
                status = await self.os.get_kernel_status()
            else:
                # 客户端模式
                client = await self._get_client()
                status = await client.get_kernel_status()
            
            return self._success_response({
                "kernel_version": "16.0.0",
                "data": status,
            })
        except Exception as e:
            return self._error_response(str(e))

    async def handle_health(self, request):
        """健康检查"""
        try:
            if self.os:
                # 服务器模式
                result = {"healthy": True, "kernel": "running"}
            else:
                # 客户端模式
                client = await self._get_client()
                result = await client.ping()
            
            return self._success_response(result)
        except Exception as e:
            return self._error_response(str(e), 503)

    async def handle_list_nodes(self, request):
        """列出集群节点"""
        try:
            if self.os:
                # 服务器模式
                status = await self.os.get_kernel_status()
                nodes = status.get("cluster", {}).get("nodes", [])
            else:
                # 客户端模式
                client = await self._get_client()
                status = await client.get_kernel_status()
                nodes = status.get("cluster", {}).get("nodes", [])
            
            return self._success_response({"nodes": nodes})
        except Exception as e:
            return self._error_response(str(e))

    def _success_response(self, data):
        return self.web.json_response({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **data
        })

    def _error_response(self, message, status=500):
        return self.web.json_response({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "error": message
        }, status=status)

    async def cleanup(self):
        """清理资源"""
        if self._client:
            await self._client.disconnect()
            self._client = None

    async def start_server(self):
        """启动 API 服务器（异步）"""
        runner = self.web.AppRunner(self.app)
        await runner.setup()
        site = self.web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"✅ API Gateway listening on http://{self.host}:{self.port}")
        return runner

    def run(self):
        """运行 API 服务器（阻塞模式，独立运行时使用）"""
        print(f"IntentOS API Gateway starting on http://{self.host}:{self.port}")
        self.web.run_app(self.app, host=self.host, port=self.port)


def start_api(args=None):
    """启动 REST API 服务器（独立运行，客户端模式）"""
    from intentos.interface.ipc import check_kernel_running, wait_for_kernel
    import subprocess
    import sys

    console_print = print

    # 检查内核是否运行
    if not check_kernel_running():
        console_print("\n⚠️  IntentOS 内核未运行", flush=True)
        console_print("正在自动启动内核进程...", flush=True)

        # 在后台启动 daemon 进程
        subprocess.Popen(
            [sys.executable, "-m", "intentos", "daemon", "--api"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # 等待内核启动
        console_print("等待内核初始化...", flush=True)
        if not wait_for_kernel(timeout=10.0):
            console_print("\n❌ 内核启动超时", flush=True)
            console_print("请手动启动内核：python -m intentos daemon", flush=True)
            sys.exit(1)

        console_print("✅ 内核已启动", flush=True)

    # 客户端模式：创建网关（不传 os_instance）
    gateway = IntentOSGateway(host=args.host if args else "localhost", port=args.port if args else 8080)
    gateway.run()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="IntentOS API Gateway")
    parser.add_argument("--host", default="localhost", help="监听地址")
    parser.add_argument("--port", type=int, default=8080, help="监听端口")
    args = parser.parse_args()
    start_api(args)
