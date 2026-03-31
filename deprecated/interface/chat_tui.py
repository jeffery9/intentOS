#!/usr/bin/env python3
"""
AI Agent Chat TUI

TUI 仅仅是 UI 层，AI Agent 通过 IntentOS 内核运行
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

from intentos.core import Context
from intentos.kernel.engine import (
    ExecutionRequest,
    ExecutionResponse,
    initialize_kernel,
)


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
    Chat TUI

    UI 层，通过内核执行 AI Agent
    """

    def __init__(self):
        self.console = Console()
        self.kernel = None
        self.context: Optional[Context] = None
        self.messages: list[ChatMessage] = []
        self.running = True
        self.width = 80

    async def initialize(self) -> None:
        """初始化"""
        self.console.print("[bold cyan]正在启动 IntentOS 内核...[/bold cyan]\n")

        # 初始化内核
        self.kernel = await initialize_kernel()

        # 创建上下文
        self.context = Context(user_id="default")

        status = self.kernel.get_status()
        self.console.print("[bold green]✓ 内核已就绪[/bold green]")
        self.console.print(f"  能力：{status['registry']['capabilities']} 个")
        self.console.print(f"  模板：{status['registry']['templates']} 个")
        self.console.print(f"  VM: {status['vm']['status']}\n")

    def show_banner(self) -> None:
        """显示横幅"""
        banner = """
╔════════════════════════════════════════════════════════╗
║           IntentOS AI Agent - 智能助理                  ║
║                                                        ║
║  通过 IntentOS 内核执行                                 ║
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
  `/quit` - 退出

**示例:**
  • 安排明天下午 3 点的会议
  • 分析销售数据
  • 写一篇关于 AI 的文章
"""
        self.console.print(Panel(help_text, title="帮助", border_style="cyan"))

    def show_status(self) -> None:
        """显示内核状态"""
        if not self.kernel:
            return

        status = self.kernel.get_status()

        table = Table(title="内核状态", border_style="cyan")
        table.add_column("组件", style="cyan")
        table.add_column("状态", style="white")

        table.add_row("内核", "✓ 运行中" if status["initialized"] else "✗ 未启动")
        table.add_row("能力", f"{status['registry']['capabilities']} 个")
        table.add_row("模板", f"{status['registry']['templates']} 个")
        table.add_row("语义 VM", status["vm"]["status"])

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
            request = ExecutionRequest(
                intent=user_input,
                context=self.context,
            )
            response: ExecutionResponse = await self.kernel.execute(request)

        # 显示结果
        ai_content = response.message

        if response.result:
            ai_content += "\n\n**结果:**\n"
            if isinstance(response.result, dict):
                for k, v in response.result.items():
                    ai_content += f"• {k}: {v}\n"

        if response.metadata:
            ai_content += f"\n**元数据:** {response.metadata}"

        ai_msg = ChatMessage("assistant", ai_content)
        self.messages.append(ai_msg)
        self.console.print(ai_msg.render(self.console, self.width))

    async def run(self) -> None:
        """运行 TUI"""
        await self.initialize()
        self.show_banner()

        while self.running:
            try:
                user_input = Prompt.ask(
                    "\n[bold blue]👤 你[/bold blue]",
                    default="",
                ).strip()

                if not user_input:
                    continue

                if user_input.startswith('/'):
                    await self._handle_command(user_input)
                else:
                    await self.process_message(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]输入 /quit 退出[/yellow]")
            except EOFError:
                self.running = False

    async def _handle_command(self, command: str) -> None:
        """处理命令"""
        cmd = command.lower().strip()

        if cmd == '/help':
            self.show_help()
        elif cmd == '/clear':
            self.messages.clear()
            self.console.print("[green]✓ 已清空[/green]")
        elif cmd == '/status':
            self.show_status()
        elif cmd in ['/quit', '/exit', '/q']:
            self.console.print("\n[green]👋 再见![/green]")
            self.running = False
        else:
            self.console.print(f"[red]❌ 未知命令：{command}[/red]")


async def main():
    """主函数"""
    try:
        tui = ChatTUI()
        await tui.run()
    except KeyboardInterrupt:
        print("\n\n👋 再见!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
