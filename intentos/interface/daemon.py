#!/usr/bin/env python3
"""
IntentOS 守护进程 - 服务器模式

启动 IntentOS 内核并监听 RPC 请求，可选择启动 API 网关
"""

import argparse
import asyncio
import os
import signal
import sys
from datetime import datetime


def get_socket_path() -> str:
    """获取 Socket 文件路径"""
    # 使用固定的 /tmp 目录，方便客户端查找
    return "/tmp/intentos.sock"


class IntentOSDaemon:
    """
    IntentOS 守护进程 - 服务器模式

    运行内核并提供 RPC 服务，可选择启动 API 网关
    """

    def __init__(self, enable_api=False, api_host="localhost", api_port=8080):
        self.os = None
        self.rpc_server = None
        self.api_gateway = None
        self.enable_api = enable_api
        self.api_host = api_host
        self.api_port = api_port
        self.start_time = None
        self._should_run = True
        self._background_tasks = []

    def initialize(self) -> None:
        """初始化系统"""
        from intentos.interface.interface import IntentOS

        print("🚀 Initializing IntentOS...")
        self.os = IntentOS()
        self.os.initialize()
        self.start_time = datetime.now()
        print("✅ IntentOS initialized")

    async def start_services(self) -> None:
        """启动服务"""
        from intentos.interface.ipc import RPCServer

        # 启动后台服务
        await self.os.start_background_services()

        # 启动 RPC 服务器
        self.rpc_server = RPCServer(self.os)
        await self.rpc_server.start()

        # 可选：启动 API 网关
        if self.enable_api:
            await self._start_api_gateway()

    async def _start_api_gateway(self) -> None:
        """启动 API 网关"""
        from intentos.interface.api import IntentOSGateway

        print(f"🌐 Starting API Gateway on http://{self.api_host}:{self.api_port}")
        self.api_gateway = IntentOSGateway(self.os, self.api_host, self.api_port)
        # 异步启动 API 服务器
        self.api_runner = await self.api_gateway.start_server()

    def _signal_handler(self, sig, frame):
        """处理中断信号"""
        print("\n🛑 Shutting down IntentOS...")
        self._should_run = False
        self.shutdown()
        print(f"👋 IntentOS stopped. Uptime: {self.get_uptime()}")
        sys.exit(0)

    def get_uptime(self) -> str:
        """获取运行时间"""
        if not self.start_time:
            return "0s"
        delta = datetime.now() - self.start_time
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours}h {minutes}m {seconds}s"

    def shutdown(self) -> None:
        """关闭系统"""
        # 关闭 OS
        if self.os:
            self.os.shutdown()

        # 停止 API 网关
        if hasattr(self, "api_runner") and self.api_runner:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.api_runner.cleanup())
            loop.close()

        # 停止 RPC 服务器
        if self.rpc_server:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.rpc_server.stop())
            loop.close()

    def run(self) -> None:
        """运行守护进程"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 初始化
        self.initialize()

        # 启动服务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.start_services())

        # 打印状态
        socket_path = get_socket_path()
        print("\n" + "=" * 60)
        print("  IntentOS Daemon is running")
        print("=" * 60)
        print(f"  Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Socket: {socket_path}")
        print(f"  PID: {os.getpid()}")
        if self.enable_api:
            print(f"  API: http://{self.api_host}:{self.api_port}")
        print("=" * 60)
        print("\nPress Ctrl+C to stop\n")
        print("连接方式:")
        print("  python -m intentos shell    # 交互式 Shell")
        print("  python -m intentos chat     # Chat TUI")
        if not self.enable_api:
            print("  python -m intentos api      # REST API 网关（需先启动 daemon --api）")
        print("")

        # 运行事件循环
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self._signal_handler(None, None)


def start_daemon(args):
    """启动守护进程"""
    daemon = IntentOSDaemon(
        enable_api=args.api,
        api_host=args.api_host,
        api_port=args.api_port,
    )
    daemon.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IntentOS Daemon")
    parser.add_argument("--api", action="store_true", help="启动 API 网关")
    parser.add_argument("--api-host", default="localhost", help="API 监听地址")
    parser.add_argument("--api-port", type=int, default=8080, help="API 监听端口")
    args = parser.parse_args()
    start_daemon(args)
