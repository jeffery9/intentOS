#!/usr/bin/env python3
"""
IntentOS Desktop Launcher - 桌面应用启动器

将 Web Console 打包为桌面体验：原生窗口标题、自动拉起内核与本地服务、
调用系统浏览器 App 模式（Chrome/Edge/Chromium），或可选 pywebview 原生窗口。

用法:
    python -m intentos desktop                 # 启动桌面模式（自动打开浏览器窗口）
    python -m intentos desktop --no-browser    # 仅启动本地服务（供 Electron/Tauri 壳连接）
    python -m intentos desktop --backend webview  # 使用 pywebview 原生窗口

桌面打包方案（见 desktop/ 目录与 docs/DESKTOP.md）:
    - Electron:  cd desktop && npm install && npm run build     -> dmg/exe/AppImage
    - PyInstaller: pip install pyinstaller && pyinstaller desktop/intentos-desktop.spec
    - Tauri:     复用同一本地服务，Rust 壳体积最小
"""

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time


def find_free_port(start: int = 8931) -> int:
    """寻找可用端口（避免与已有 daemon/web 冲突）"""
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("找不到可用端口")


# 常见支持 --app 模式的浏览器（macOS / Windows / Linux）
_BROWSER_CANDIDATES = [
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    # Linux
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "microsoft-edge", "brave-browser",
]


def find_app_mode_browser():
    """查找支持 --app= 模式（无地址栏的窗口化浏览）的浏览器可执行文件"""
    for cand in _BROWSER_CANDIDATES:
        path = cand if os.path.isabs(cand) else shutil.which(cand)
        if path and os.path.exists(path):
            return path
    return None


def open_browser_window(url: str) -> bool:
    """以 App 模式打开系统浏览器窗口；失败时回退到默认浏览器"""
    browser = find_app_mode_browser()
    profile = os.path.join(
        os.path.expanduser("~"), ".intentos", "desktop-profile"
    )
    os.makedirs(profile, exist_ok=True)
    try:
        if browser:
            subprocess.Popen(
                [browser, f"--app={url}", f"--user-data-dir={profile}",
                 "--window-size=1280,860", "--window-position=80,60"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        # 回退：系统默认方式打开
        import webbrowser
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"⚠️  无法打开浏览器窗口: {e}", file=sys.stderr)
        return False


def run_webview(url: str, title: str):
    """使用 pywebview 打开真正的原生窗口（需 pip install pywebview）"""
    try:
        import webview
    except ImportError:
        print(
            "❌ 未安装 pywebview。请执行: pip install pywebview\n"
            "   或去掉 --backend webview 使用系统浏览器窗口模式。",
            file=sys.stderr,
        )
        sys.exit(1)
    webview.create_window(title, url, width=1280, height=860)
    webview.start()


class DesktopServer:
    """桌面内嵌服务：在同一事件循环中运行 API Gateway + Web Console（服务器模式）

    不依赖 Unix socket daemon —— 单进程即可支撑整个桌面应用，
    这也是 Electron/Tauri 壳的后端（通过 INTENTOS_WEB_URL 环境变量通信）。
    """

    def __init__(self, host: str = "127.0.0.1", web_port: int = 0, api_port: int = 0):
        self.host = host
        self.web_port = web_port or find_free_port(8931)
        self.api_port = api_port or find_free_port(self.web_port + 1)
        self._runners = []

    async def start(self):
        import asyncio

        from intentos.interface.api import IntentOSGateway
        from intentos.interface.interface import IntentOS
        from intentos.interface.web.server import IntentOSWebConsole

        print("🚀 Initializing IntentOS kernel (embedded)...", flush=True)
        self.os = IntentOS()
        self.os.initialize()
        await self.os.start_background_services()
        print("✅ Kernel ready", flush=True)

        # 内部网关实例（不监听端口，直接由 Web Console 代理调用，零密钥）
        gateway = IntentOSGateway(self.os)

        console = IntentOSWebConsole(
            gateway=gateway, host=self.host, port=self.web_port
        )
        runner = await console.start_server()
        self._runners.append(runner)

        # 同时暴露 REST API（供外部工具/多窗口访问）
        api_runner = await gateway.start_server()
        self._runners.append(api_runner)

        return f"http://{self.host}:{self.web_port}"

    async def stop(self):
        for r in self._runners:
            await r.cleanup()
        if getattr(self, "os", None):
            self.os.shutdown()

    def run_forever(self, url: str, backend: str = "browser"):
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        stop_event = loop.create_future()

        def _sig(sig, frame):
            print("\n🛑 Shutting down IntentOS Desktop...", flush=True)
            if not stop_event.done():
                stop_event.set_result(None)

        signal_install(_sig)

        async def _serve():
            await loop.create_future()  # 阻塞直到被停止

        task = loop.create_task(_serve())

        # 打开窗口
        if backend == "webview":
            run_webview(url, "IntentOS")
            # webview 窗口关闭后返回，结束进程
        elif backend == "none":
            print(f"🖥️  Desktop backend ready at {url}")
            print("   （Electron/Tauri 壳可通过 INTENTOS_WEB_URL 读取该地址）")
        else:
            if open_browser_window(url):
                print(f"🖥️  IntentOS Desktop window opened: {url}")
            print("Press Ctrl+C to quit.")

        try:
            loop.run_until_complete(stop_event)
        except KeyboardInterrupt:
            pass
        finally:
            task.cancel()
            loop.run_until_complete(self.stop())
            loop.close()


def signal_install(handler):
    import signal

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="intentos desktop",
        description="IntentOS 桌面应用启动器（内嵌内核 + Web Console + 原生窗口）",
    )
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=0, help="Web 端口（0=自动）")
    parser.add_argument("--api-port", type=int, default=0, help="API 端口（0=自动）")
    parser.add_argument(
        "--backend",
        choices=["browser", "webview", "none"],
        default="browser",
        help="窗口后端: browser=系统浏览器App模式(默认), webview=pywebview原生窗口, none=仅服务(供Electron/Tauri)",
    )
    args = parser.parse_args(argv)

    server = DesktopServer(host=args.host, web_port=args.port, api_port=args.api_port)
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        url = loop.run_until_complete(server.start())
    except KeyboardInterrupt:
        loop.run_until_complete(server.stop())
        sys.exit(0)
    finally:
        loop.close()

    # 供子进程/Electron 壳读取
    os.environ["INTENTOS_WEB_URL"] = url
    server.run_forever(url, backend=args.backend)


if __name__ == "__main__":
    main()
