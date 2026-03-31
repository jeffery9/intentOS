#!/usr/bin/env python3
"""
IntentOS Chat TUI - 客户端模式

连接到运行中的 IntentOS 内核，提供聊天界面
"""

import asyncio
import sys
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.spinner import Spinner
from rich.table import Table


class ChatMessage:
    """聊天消息"""

    def __init__(self, role: str, content: str, timestamp: Optional[str] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")

    def render(self, console: Console, width: int) -> Panel:
        """渲染消息"""
        if self.role == "user":
            style = "bold blue"
            title = f"👤 你 • {self.timestamp}"
        else:
            style = "bold green"
            title = f"🤖 AI • {self.timestamp}"

        return Panel(
            self.content,
            title=title,
            border_style=style,
            width=width,
        )


class ChatTUI:
    """
    Chat TUI - 客户端模式

    通过 RPC 连接到运行中的 IntentOS 内核
    """

    def __init__(self, client, loop):
        self.console = Console()
        self.client = client
        self.loop = loop
        self.messages: list[ChatMessage] = []
        self.running = True
        self.width = 80

    def show_banner(self) -> None:
        """显示横幅"""
        banner = """
╔════════════════════════════════════════════════════════╗
║           IntentOS AI Agent - 智能助理                  ║
║                                                        ║
║  已连接到 IntentOS 内核                                 ║
║  输入 /help 查看帮助，/quit 退出                       ║
╚════════════════════════════════════════════════════════╝
        """
        self.console.print(Panel(banner, border_style="bold cyan"))

    def show_help(self) -> None:
        """显示帮助"""
        help_text = """
**命令:**
  `/help` - 帮助
  `/clear` - 清空历史
  `/status` - 内核状态
  `/ping` - 心跳检测
  `/quit` - 退出

**示例:**
  • 安排明天下午 3 点的会议
  • 分析销售数据
  • 写一篇关于 AI 的文章
"""
        self.console.print(Panel(help_text, title="帮助", border_style="cyan"))

    def show_status(self) -> None:
        """显示内核状态"""
        try:
            status = self.loop.run_until_complete(self.client.get_status())
            kernel_status = self.loop.run_until_complete(self.client.get_kernel_status())
        except Exception as e:
            self.console.print(f"[red]❌ 获取状态失败：{e}[/red]")
            return

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

    async def process_message(self, user_input: str) -> None:
        """处理消息"""
        # 显示用户消息
        user_msg = ChatMessage("user", user_input)
        self.messages.append(user_msg)
        self.console.print(user_msg.render(self.console, self.width))

        # 通过内核执行
        with Live(
            Spinner("dots", text="内核执行中...", style="cyan"),
            console=self.console,
            transient=True,
        ):
            result = await self.client.execute(user_input)

        # 显示结果
        ai_content = result

        ai_msg = ChatMessage("assistant", ai_content)
        self.messages.append(ai_msg)
        self.console.print(ai_msg.render(self.console, self.width))

    def run(self) -> None:
        """运行 TUI"""
        self.show_banner()

        while self.running:
            try:
                user_input = Prompt.ask(
                    "\n[bold blue]👤 你[/bold blue]",
                    default="",
                ).strip()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    self._handle_command(user_input)
                else:
                    self.loop.run_until_complete(self.process_message(user_input))

            except KeyboardInterrupt:
                self.console.print("\n[yellow]输入 /quit 退出[/yellow]")
            except EOFError:
                self.running = False

    def _handle_command(self, command: str) -> None:
        """处理命令"""
        cmd = command.lower().strip()

        if cmd == "/help":
            self.show_help()
        elif cmd == "/clear":
            self.messages.clear()
            self.console.print("[green]✓ 已清空[/green]")
        elif cmd == "/status":
            self.show_status()
        elif cmd == "/ping":
            try:
                result = self.loop.run_until_complete(self.client.ping())
                self.console.print(f"[green]✓ 心跳正常：{result}[/green]")
            except Exception as e:
                self.console.print(f"[red]❌ 心跳失败：{e}[/red]")
        elif cmd in ["/quit", "/exit", "/q"]:
            self.console.print("\n[green]👋 再见![/green]")
            self.running = False
        else:
            self.console.print(f"[red]❌ 未知命令：{command}[/red]")


async def check_connection(client):
    """检查连接"""
    await client.connect()
    status = await client.get_status()
    return True, status


def start_chat_tui(args):
    """启动 Chat TUI"""
    import subprocess

    from intentos.interface.ipc import RPCClient, check_kernel_running, wait_for_kernel

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
        if not wait_for_kernel(timeout=10.0):
            console.print("\n❌ 内核启动超时", style="red")
            console.print("请手动启动内核：[bold]python -m intentos daemon[/bold]", style="red")
            sys.exit(1)

        console.print("✅ 内核已启动", style="green")

    # 创建事件循环和客户端
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = None

    try:
        # 连接
        client = RPCClient()
        connected, result = loop.run_until_complete(check_connection(client))
        if not connected:
            console.print(f"❌ 连接失败：{result}", style="red")
            sys.exit(1)

        console.print("✅ 已连接到 IntentOS 内核", style="green")

        # 启动 TUI（传入事件循环）
        tui = ChatTUI(client, loop)
        tui.run()

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    finally:
        if client:
            try:
                loop.run_until_complete(client.disconnect())
            except Exception:
                pass
        loop.close()


if __name__ == "__main__":
    start_chat_tui(None)
