#!/usr/bin/env python3
"""
IntentOS CLI - 统一的命令行交互界面

整合了 Shell 和 Chat 功能，提供：
- 交互式对话（自然语言执行）
- 系统命令（/status, /ping 等）
- 图谱管理、验证等工具命令
"""

import argparse
import asyncio
import cmd
import json
import os
import signal
import subprocess
import sys
from datetime import datetime
from typing import Any, Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.table import Table


# =============================================================================
# IPC/RPC 通信层（简化版，内联到 CLI）
# =============================================================================


PROTOCOL_VERSION = 1
MAGIC_HEADER = b"INTENTOS"


def get_socket_path() -> str:
    """获取 Socket 文件路径"""
    # 优先检查 /tmp 目录（daemon 默认使用）
    tmp_socket = "/tmp/intentos.sock"
    if os.path.exists(tmp_socket):
        return tmp_socket
    
    # 否则使用环境变量或临时目录
    base_dir = os.environ.get("INTENTOS_RUNTIME_DIR", "/tmp")
    return os.path.join(base_dir, "intentos.sock")


def check_kernel_running() -> bool:
    """检查内核是否运行"""
    socket_path = get_socket_path()
    return os.path.exists(socket_path)


def wait_for_kernel(timeout: float = 10.0) -> bool:
    """等待内核启动"""
    import time
    start = time.time()
    while time.time() - start < timeout:
        if check_kernel_running():
            return True
        time.sleep(0.1)
    return False


# =============================================================================
# RPC 客户端
# =============================================================================


import struct
from dataclasses import dataclass, field


@dataclass
class RPCRequest:
    """RPC 请求"""
    method: str
    params: dict = field(default_factory=dict)
    request_id: str = ""

    def to_bytes(self) -> bytes:
        """序列化为字节"""
        data = json.dumps({
            "version": PROTOCOL_VERSION,
            "id": self.request_id or datetime.now().isoformat(),
            "method": self.method,
            "params": self.params,
        }, ensure_ascii=False).encode("utf-8")
        header = MAGIC_HEADER + struct.pack(">I", len(data))
        return header + data


@dataclass
class RPCResponse:
    """RPC 响应"""
    request_id: str
    result: Any = None
    error: Optional[str] = None

    @classmethod
    def from_bytes(cls, data: bytes) -> "RPCResponse":
        """从字节反序列化"""
        obj = json.loads(data.decode("utf-8"))
        return cls(
            request_id=obj["id"],
            result=obj.get("result"),
            error=obj.get("error"),
        )


class RPCClient:
    """
    RPC 客户端 - 连接到运行中的 IntentOS 内核
    """

    def __init__(self, socket_path: Optional[str] = None):
        self.socket_path = socket_path or get_socket_path()
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._connected = False

    async def connect(self) -> None:
        """连接到服务器"""
        try:
            self._reader, self._writer = await asyncio.open_unix_connection(self.socket_path)
            self._connected = True
        except FileNotFoundError:
            raise ConnectionError(
                f"无法连接到 IntentOS 内核。\n"
                f"Socket 文件不存在：{self.socket_path}\n"
                f"请先启动内核：intentos daemon"
            )
        except Exception as e:
            raise ConnectionError(f"连接失败：{e}")

    async def disconnect(self) -> None:
        """断开连接"""
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        self._connected = False

    async def _call(self, method: str, params: Optional[dict] = None) -> Any:
        """调用 RPC 方法"""
        if not self._connected:
            await self.connect()

        request = RPCRequest(method=method, params=params or {})
        self._writer.write(request.to_bytes())
        await self._writer.drain()

        # 读取响应
        header = await self._reader.readexactly(12)
        if header[:8] != MAGIC_HEADER:
            raise RuntimeError("Invalid response header")

        data_len = struct.unpack(">I", header[8:])[0]
        data = await self._reader.readexactly(data_len)
        response = RPCResponse.from_bytes(data)

        if response.error:
            raise RuntimeError(response.error)

        return response.result

    async def execute(self, text: str) -> str:
        """执行意图"""
        result = await self._call("execute", {"text": text})
        return result.get("result", "")

    async def get_status(self) -> dict:
        """获取状态"""
        return await self._call("get_status")

    async def get_kernel_status(self) -> dict:
        """获取内核详细状态"""
        return await self._call("get_kernel_status")

    async def ping(self) -> dict:
        """心跳检测"""
        return await self._call("ping")


# =============================================================================
# IntentOS CLI - 统一的交互界面
# =============================================================================


class IntentOSCLI(cmd.Cmd):
    """
    IntentOS 统一命令行界面
    
    整合了 Shell 和 Chat 功能：
    - 直接输入自然语言执行意图
    - 使用 / 开头的系统命令
    """
    
    intro = "IntentOS CLI. Type /help for commands.\n"
    prompt = "intentos> "

    def __init__(self, client: RPCClient, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.client = client
        self.loop = loop
        self.console = Console()
        self._print_banner()

    def _print_banner(self):
        """打印欢迎横幅"""
        self.console.print("\n" + "=" * 60, style="bold blue")
        self.console.print("       IntentOS CLI - AI Native Operating System      ", style="bold blue")
        self.console.print("=" * 60 + "\n", style="bold blue")
        self.console.print("AI 原生操作系统 - 统一命令行界面", style="italic green")
        self.console.print("\n使用方式:")
        self.console.print("  • 直接输入自然语言执行意图")
        self.console.print("  • 使用 / 开头的系统命令 (/help 查看帮助)")
        self.console.print("  • 输入 /quit 退出\n")

    def onecmd(self, line):
        """拦截指令分发"""
        if not line.strip():
            return False

        if line.startswith("/"):
            return super().onecmd(line[1:])
        else:
            # 自然语言意图
            self.loop.run_until_complete(self._execute_intent(line))
            return False

    async def _execute_intent(self, text: str):
        """执行自然语言意图"""
        with Live(
            Spinner("dots", text=f"Executing: {text}..."),
            refresh_per_second=10,
            console=self.console,
            transient=True,
        ) as live:
            try:
                result = await self.client.execute(text)
                self.console.print(Panel(result, title="Response", border_style="blue"))
            except Exception as e:
                self.console.print(Panel(f"❌ Error: {e}", title="Error", border_style="red"))

    # -------------------------------------------------------------------------
    # 系统命令
    # -------------------------------------------------------------------------

    def do_help(self, arg):
        """显示帮助：/help"""
        help_text = """
**IntentOS CLI 命令**

系统命令:
  `/help` - 显示此帮助信息
  `/clear` - 清空屏幕
  `/status` - 查看内核状态
  `/ping` - 心跳检测
  `/quit` - 退出 CLI

自然语言:
  直接输入自然语言即可执行意图，例如:
  - "分析销售数据"
  - "生成报告"
  - "查询用户信息"
"""
        self.console.print(Panel(help_text, title="帮助", border_style="cyan"))

    def do_clear(self, arg):
        """清空屏幕：/clear"""
        os.system('cls' if os.name == 'nt' else 'clear')
        self._print_banner()

    def do_status(self, arg):
        """查看内核状态：/status"""
        try:
            status = self.loop.run_until_complete(self.client.get_status())
            kernel_status = self.loop.run_until_complete(self.client.get_kernel_status())
            
            table = Table(title="内核状态", border_style="cyan")
            table.add_column("组件", style="cyan")
            table.add_column("状态", style="white")

            table.add_row("内核", "✓ 运行中" if status.get("running") else "✗ 未启动")
            table.add_row("初始化", "✓ 已就绪" if status.get("initialized") else "✗ 未就绪")

            reg = kernel_status.get("registry", {})
            table.add_row("能力", f"{len(reg.get('capabilities', []))} 个")
            table.add_row("模板", f"{len(reg.get('templates', []))} 个")

            cluster = kernel_status.get("cluster", {})
            nodes = cluster.get("nodes", [])
            table.add_row("节点", f"{len(nodes)} 个")

            self.console.print(table)
        except Exception as e:
            self.console.print(f"❌ Error: {e}", style="red")

    def do_ping(self, arg):
        """心跳检测：/ping"""
        try:
            result = self.loop.run_until_complete(self.client.ping())
            self.console.print(f"✅ Pong! {result}", style="green")
        except Exception as e:
            self.console.print(f"❌ Error: {e}", style="red")

    def do_quit(self, arg):
        """退出：/quit"""
        self.console.print("\n👋 Goodbye!", style="bold yellow")
        self.loop.run_until_complete(self.client.disconnect())
        return True

    def do_exit(self, arg):
        """退出：/exit"""
        return self.do_quit(arg)

    def do_EOF(self, arg):
        """EOF 处理"""
        print("")
        return self.do_quit(arg)


# =============================================================================
# 启动函数
# =============================================================================


def start_cli(args=None):
    """启动 IntentOS CLI"""
    console = Console()

    # 检查内核是否运行
    if not check_kernel_running():
        console.print("\n⚠️  IntentOS 内核未运行", style="yellow")
        console.print("正在自动启动内核进程...", style="dim")

        # 在后台启动 daemon 进程
        subprocess.Popen(
            [sys.executable, "-m", "intentos", "daemon"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # 等待内核启动
        console.print("等待内核初始化...", style="dim")
        if not wait_for_kernel(timeout=15.0):
            console.print("\n❌ 内核启动超时", style="red")
            console.print("请手动启动内核：[bold]intentos daemon[/bold]", style="red")
            sys.exit(1)

        console.print("✅ 内核已启动", style="green")

    # 创建事件循环和客户端
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = None

    try:
        # 连接
        client = RPCClient()
        loop.run_until_complete(client.connect())
        console.print(f"✅ 已连接到 IntentOS 内核", style="green")

        # 启动 CLI
        cli = IntentOSCLI(client, loop)
        cli.cmdloop()

    except KeyboardInterrupt:
        console.print("\nInterrupted", style="yellow")
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    finally:
        if client:
            try:
                loop.run_until_complete(client.disconnect())
            except:
                pass
        loop.close()


# =============================================================================
# 主入口
# =============================================================================


def main():
    """CLI 主函数"""
    # 检查是否是子命令调用
    if len(sys.argv) > 1 and sys.argv[1] in ["shell", "chat", "tui"]:
        # 启动交互式 CLI
        start_cli()
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        # 查看状态
        console = Console()
        if not check_kernel_running():
            console.print("❌ 内核未运行", style="red")
            sys.exit(1)
        
        loop = asyncio.new_event_loop()
        client = RPCClient()
        try:
            loop.run_until_complete(client.connect())
            status = loop.run_until_complete(client.get_status())
            kernel_status = loop.run_until_complete(client.get_kernel_status())
            
            console.print("\n[bold blue]IntentOS 内核状态[/bold blue]")
            console.print(f"运行状态：{'✓' if status.get('running') else '✗'}")
            console.print(f"初始化：{'✓' if status.get('initialized') else '✗'}")
            
            reg = kernel_status.get("registry", {})
            console.print(f"能力数：{len(reg.get('capabilities', []))}")
            console.print(f"模板数：{len(reg.get('templates', []))}")
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
            sys.exit(1)
        finally:
            if client:
                loop.run_until_complete(client.disconnect())
            loop.close()
    else:
        # 默认启动交互式 CLI
        start_cli()


if __name__ == "__main__":
    main()
