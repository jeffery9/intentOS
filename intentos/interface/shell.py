#!/usr/bin/env python3
"""
IntentOS 交互式 Shell - 客户端模式

连接到运行中的 IntentOS 内核
"""

import asyncio
import cmd
import sys

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table


class IntentShell(cmd.Cmd):
    """
    IntentOS 交互式 Shell - 客户端
    """

    intro = "IntentOS Shell. Type /help for commands.\n"
    prompt = "intentos> "

    def __init__(self, client, loop):
        super().__init__()
        self.client = client
        self.loop = loop
        self.console = Console()
        self._print_banner()

    def _print_banner(self):
        self.console.print("\n" + "=" * 50, style="bold blue")
        self.console.print("       IntentOS Shell (Client Mode)      ", style="bold blue")
        self.console.print("=" * 50 + "\n", style="bold blue")
        self.console.print("AI-Native Operating System", style="italic green")
        self.console.print("System: [bold cyan]/ps, /top, /df, /status, /exit[/bold cyan]")
        self.console.print("Natural Language: [bold white]Just type your intent[/bold white]\n")

    def onecmd(self, line):
        """
        拦截指令分发：
        1. 以 / 开头 -> 系统指令
        2. 其他 -> 自然语言意图
        """
        if not line.strip():
            return False

        if line.startswith("/"):
            return super().onecmd(line[1:])
        else:
            # 在已有的事件循环中运行
            self.loop.run_until_complete(self._execute_intent(line))
            return False

    async def _execute_intent(self, text):
        with Live(
            Spinner("dots", text=f"Executing: {text}..."),
            refresh_per_second=10,
            console=self.console,
        ) as live:
            try:
                result = await self.client.execute(text)
                live.update(Panel(result, title="Response", border_style="blue"))
            except Exception as e:
                live.update(Panel(f"❌ Error: {e}", title="Error", border_style="red"))

    def do_status(self, arg):
        """Show kernel status: /status"""
        try:
            status = self.loop.run_until_complete(self.client.get_status())
            table = Table(title="Kernel Status")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Running", str(status.get("running", False)))
            table.add_row("Initialized", str(status.get("initialized", False)))
            self.console.print(table)
        except Exception as e:
            self.console.print(f"❌ Error: {e}", style="red")

    def do_top(self, arg):
        """Show cluster load: /top"""
        try:
            status = self.loop.run_until_complete(self.client.get_kernel_status())
            cluster = status.get("cluster", {})

            table = Table(title="Cluster Resource Usage")
            table.add_column("Node ID", style="cyan")
            table.add_column("Host:Port", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Load", style="magenta")

            for node in cluster.get("nodes", []):
                table.add_row(
                    node["node_id"][:8],
                    f"{node['host']}:{node['port']}",
                    node["status"],
                    f"{node['load']*100:.1f}%",
                )
            self.console.print(table)
        except Exception as e:
            self.console.print(f"❌ Error: {e}", style="red")

    def do_df(self, arg):
        """Show storage usage: /df"""
        try:
            status = self.loop.run_until_complete(self.client.get_kernel_status())
            reg = status.get("registry", {})

            table = Table(title="Semantic Storage")
            table.add_column("Type", style="cyan")
            table.add_column("Count", style="magenta")
            table.add_row("Intent Templates", str(len(reg.get("templates", []))))
            table.add_row("Capabilities", str(len(reg.get("capabilities", []))))
            self.console.print(table)
        except Exception as e:
            self.console.print(f"❌ Error: {e}", style="red")

    def do_ls(self, arg):
        """List templates or capabilities: /ls [templates|capabilities]"""
        try:
            status = self.loop.run_until_complete(self.client.get_kernel_status())
            info = status.get("registry", {})
            if arg == "capabilities":
                items = info.get("capabilities", [])
                title = "Capabilities"
            else:
                items = info.get("templates", [])
                title = "Intent Templates"

            table = Table(title=title)
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="green")

            for item in items:
                table.add_row(item["name"], item.get("description", "N/A"))
            self.console.print(table)
        except Exception as e:
            self.console.print(f"❌ Error: {e}", style="red")

    def do_ping(self, arg):
        """Ping kernel: /ping"""
        try:
            result = self.loop.run_until_complete(self.client.ping())
            self.console.print(f"✅ Pong! {result}", style="green")
        except Exception as e:
            self.console.print(f"❌ Error: {e}", style="red")

    def do_exit(self, arg):
        """Exit: /exit"""
        self.console.print("\n👋 Goodbye!", style="bold yellow")
        self.loop.run_until_complete(self.client.disconnect())
        return True

    def do_EOF(self, arg):
        print("")
        return self.do_exit(arg)


async def check_connection(client):
    """检查连接"""
    await client.connect()
    status = await client.get_status()
    return True, status


def start_shell(args):
    """启动交互式 Shell"""
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
            start_new_session=True,  # 创建新会话，独立运行
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
    client = RPCClient()

    try:
        # 连接
        connected, result = loop.run_until_complete(check_connection(client))
        if not connected:
            console.print(f"❌ 连接失败：{result}", style="red")
            sys.exit(1)

        console.print("✅ 已连接到 IntentOS 内核", style="green")

        # 启动 Shell（传入事件循环）
        shell = IntentShell(client, loop)
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            print("\nInterrupted")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    finally:
        loop.close()


if __name__ == "__main__":
    start_shell(None)
