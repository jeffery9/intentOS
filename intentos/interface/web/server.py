#!/usr/bin/env python3
"""
IntentOS Web Console - 网页版交互界面 (参考 Codex / Cursor 的 UX)

功能:
- 在 `/` 提供单页 Web Console（意图对话 / 任务流 / 系统监控 / 检查器）
- 通过 `/web-api/*` 代理转发到 REST API Gateway（自动附加 Bearer Token），
  浏览器无需接触任何密钥
- 支持独立运行（客户端模式，自动拉起内核 daemon + API Gateway）
  或集成到 daemon（服务器模式，直接持有内核实例）

用法:
    python -m intentos web [--host 0.0.0.0] [--port 8000]
"""

import argparse
from pathlib import Path

from aiohttp import web

STATIC_DIR = Path(__file__).parent / "static"


class IntentOSWebConsole:
    """IntentOS Web Console HTTP 服务"""

    def __init__(self, gateway=None, host="localhost", port=8000):
        """
        Args:
            gateway: 可选的 IntentOSGateway 实例（服务器模式，复用其 app/aiohttp 服务）。
                     为 None 时以客户端模式独立启动一个站点。
            host: 监听地址
            port: 监听端口
        """
        self.gateway = gateway
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()

    # ---------- routes ----------
    def _setup_routes(self):
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_get("/index.html", self.handle_index)
        self.app.router.add_static("/assets/", STATIC_DIR, show_fallback=False)
        # Web 专用 API 代理（服务端注入 Token，浏览器零密钥）
        self.app.router.add_post("/web-api/execute", self.handle_execute)
        self.app.router.add_get("/web-api/status", self.handle_status)
        self.app.router.add_get("/web-api/health", self.handle_health)
        self.app.router.add_get("/web-api/nodes", self.handle_nodes)

    # ---------- static ----------
    async def handle_index(self, request):
        index_file = STATIC_DIR / "index.html"
        if not index_file.exists():
            return web.Response(text="Web Console assets missing", status=500)
        return web.FileResponse(index_file)

    # ---------- api proxy ----------
    async def _call_gateway(self, coro_factory):
        """统一调用网关处理器并返回 JSON"""
        try:
            resp = await coro_factory()
            body = await resp.json()
            return web.json_response(body, status=resp.status)
        except Exception as e:
            return web.json_response(
                {"status": "error", "error": f"Gateway unreachable: {e}"}, status=502
            )

    async def handle_execute(self, request):
        """POST /web-api/execute -> 网关 /v1/execute"""
        data = await request.json()
        if self.gateway is not None:
            return await self._call_gateway(
                lambda: self.gateway.handle_execute(
                    _FakeRequest(json_data=data, headers={})
                )
            )
        return await self._rpc_call("execute", {"text": data.get("intent", "")})

    async def handle_status(self, request):
        if self.gateway is not None:
            return await self._call_gateway(lambda: self.gateway.handle_status(_FakeRequest()))
        return await self._rpc_call("get_kernel_status", {})

    async def handle_health(self, request):
        if self.gateway is not None:
            return await self._call_gateway(lambda: self.gateway.handle_health(_FakeRequest()))
        return await self._rpc_call("ping", {})

    async def handle_nodes(self, request):
        if self.gateway is not None:
            return await self._call_gateway(lambda: self.gateway.handle_list_nodes(_FakeRequest()))
        return await self._rpc_call("get_kernel_status", {})

    async def _rpc_call(self, method: str, params: dict):
        """独立运行且无网关实例时，直接走 IPC RPC"""
        from intentos.interface.ipc import RPCClient

        client = RPCClient()
        try:
            await client.connect()
            fn = getattr(client, method, None)
            if fn is None:
                return web.json_response({"status": "error", "error": f"no method {method}"}, status=500)
            result = await fn(**params) if params else await fn()
            return web.json_response({"status": "success", "result": result})
        except Exception as e:
            return web.json_response({"status": "error", "error": str(e)}, status=503)
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

    # ---------- lifecycle ----------
    async def start_server(self):
        """异步启动（供 daemon 集成使用）"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"🖥️  Web Console listening on http://{self.host}:{self.port}")
        return runner

    def run(self):
        """阻塞运行（独立模式）"""
        print(f"IntentOS Web Console starting on http://{self.host}:{self.port}")
        web.run_app(self.app, host=self.host, port=self.port, print=None)


class _FakeRequest:
    """适配 IntentOSGateway 处理器所需的极简 request 对象"""

    def __init__(self, json_data=None, headers=None):
        self._json_data = json_data or {}
        self.headers = headers or {}

    async def json(self):
        return self._json_data


def start_web(args=None):
    """启动 Web Console（独立运行，客户端模式）"""
    import subprocess
    import sys

    from intentos.interface.ipc import check_kernel_running, wait_for_kernel

    host = args.host if args else "localhost"
    port = args.port if args else 8000
    api_port = args.api_port if args else 8080

    # 确保内核与 API Gateway 可用
    if not check_kernel_running():
        print("\n⚠️  IntentOS 内核未运行，正在自动启动 daemon --api ...", flush=True)
        subprocess.Popen(
            [sys.executable, "-m", "intentos", "daemon", "--api",
             "--api-host", "localhost", "--api-port", str(api_port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        if not wait_for_kernel(timeout=15.0):
            print("❌ 内核启动超时，请手动运行: python -m intentos daemon --api", flush=True)
            sys.exit(1)
        print("✅ 内核已启动", flush=True)

    console = IntentOSWebConsole(host=host, port=port)
    console.run()


def main():
    parser = argparse.ArgumentParser(description="IntentOS Web Console")
    parser.add_argument("--host", default="localhost", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="Web 端口")
    parser.add_argument("--api-port", type=int, default=8080, help="API Gateway 端口")
    args = parser.parse_args()
    start_web(args)


if __name__ == "__main__":
    main()
