
import asyncio
import cmd
import json
import sys

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table

from intentos.interface.interface import IntentOS


class IntentShell(cmd.Cmd):
    intro = 'IntentOS Kernel Shell v8.1. Type /help for commands.\n'
    prompt = 'intentos> '

    def __init__(self):
        super().__init__()
        self.os = IntentOS()
        self.os.initialize()
        self.console = Console()
        self._print_banner()

    def _print_banner(self):
        self.console.print("\n" + "="*40, style="bold blue")
        self.console.print("       IntentOS Shell (v8.1)      ", style="bold blue")
        self.console.print("="*40 + "\n", style="bold blue")
        self.console.print("AI-Native Operating System Kernel", style="italic green")
        self.console.print("System commands: [bold cyan]/ps, /top, /df, /mem, /nodes, /history[/bold cyan]")
        self.console.print("Natural Language: [bold white]Just type your intent (e.g. Analyze sales data)[/bold white]\n")

    def onecmd(self, line):
        """
        拦截指令分发：
        1. 以 / 开头 -> 系统指令
        2. 其他 -> 自然语言意图
        """
        if not line.strip():
            return False

        if line.startswith('/'):
            # 去掉 / 后分发给 do_ 方法
            return super().onecmd(line[1:])
        else:
            # 视为自然语言意图
            asyncio.run(self._execute_intent(line))
            return False

    async def _execute_intent(self, text):
        with Live(Spinner("dots", text=f"Processing intent: {text}..."), refresh_per_second=10, console=self.console) as live:
            result = await self.os.execute(text)
            live.update(Panel(result, title="System Response", border_style="blue"))

    # =========================================================================
    # 内核管理指令 (Kernel Management Commands)
    # =========================================================================

    def do_ps(self, arg):
        """Show running semantic processes: /ps"""
        status = asyncio.run(self.os.get_kernel_status())
        processes = status.get("processes", [])

        table = Table(title="Semantic Process Table (Active)")
        table.add_column("PID", style="cyan", no_wrap=True)
        table.add_column("Program", style="green")
        table.add_column("Node", style="magenta")
        table.add_column("State", style="yellow")
        table.add_column("PC", style="white")
        table.add_column("Start Time", style="dim")

        for p in processes:
            table.add_row(
                p["pid"][:8],
                p["program_name"],
                p["node_id"][:8],
                p["state"],
                str(p["pc"]),
                p["start_time"]
            )
        self.console.print(table)

    def do_kill(self, arg):
        """Kill a semantic process: /kill <pid>"""
        if not arg:
            self.console.print("Usage: /kill <pid>", style="red")
            return

        success = asyncio.run(self.os.vm.kill(arg))
        if success:
            self.console.print(f"Signal SIGKILL sent to process {arg}", style="yellow")
        else:
            self.console.print(f"Process {arg} not found.", style="red")

    def do_top(self, arg):
        """Show cluster load and health: top"""
        status = asyncio.run(self.os.get_kernel_status())
        cluster = status["cluster"]
        table = Table(title="Cluster Resource Usage (Top)")
        table.add_column("Node ID", style="cyan")
        table.add_column("Host:Port", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Load", style="magenta")

        for node in cluster.get("nodes", []):
            table.add_row(
                node["node_id"][:8],
                f"{node['host']}:{node['port']}",
                node["status"],
                f"{node['load']*100:.1f}%"
            )
        self.console.print(table)

    def do_df(self, arg):
        """Show semantic storage usage: df"""
        status = asyncio.run(self.os.get_kernel_status())
        reg = status["registry"]
        mem = status["memory"]

        table = Table(title="Semantic Storage Usage (Disk)")
        table.add_column("Storage Type", style="cyan")
        table.add_column("Item Count", style="magenta")
        table.add_row("Intent Templates", str(len(reg.get("templates", []))))
        table.add_row("Capabilities", str(len(reg.get("capabilities", []))))
        table.add_row("Programs", str(mem.get("programs_count", 0)))
        table.add_row("Variables", str(mem.get("variables_count", 0)))
        self.console.print(table)

    def do_mem(self, arg):
        """Access semantic memory: mem [get|set|delete] store key [value]"""
        parts = arg.split()
        if not parts:
            status = asyncio.run(self.os.get_kernel_status())
            self.console.print(f"Memory Summary: {status['memory']}", style="cyan")
            return

        cmd_type = parts[0]
        try:
            if cmd_type == "get" and len(parts) >= 3:
                val = asyncio.run(self.os.vm.memory.get(parts[1], parts[2]))
                self.console.print(f"{parts[1]}:{parts[2]} = {val}")
            elif cmd_type == "set" and len(parts) >= 4:
                asyncio.run(self.os.vm.memory.set(parts[1], parts[2], parts[3]))
                self.console.print("Memory set successful.")
            elif cmd_type == "delete" and len(parts) >= 3:
                asyncio.run(self.os.vm.memory.delete(parts[1], parts[2]))
                self.console.print("Memory deleted.")
            else:
                self.console.print("Usage: mem [get|set|delete] store key [value]", style="red")
        except Exception as e:
            self.console.print(f"Memory error: {e}", style="red")

    def do_nodes(self, arg):
        """Manage nodes: nodes [add|remove] host port"""
        parts = arg.split()
        if not parts:
            self.do_top("")
            return

        action = parts[0]
        try:
            if action == "add" and len(parts) >= 3:
                node = asyncio.run(self.os.vm.add_node(parts[1], int(parts[2])))
                self.console.print(f"Node added: {node.node_id}", style="green")
            elif action == "remove" and len(parts) >= 2:
                asyncio.run(self.os.vm.remove_node(parts[1]))
                self.console.print("Node removed.", style="yellow")
        except Exception as e:
            self.console.print(f"Node management error: {e}", style="red")

    def do_history(self, arg):
        """Show self-bootstrap history (Kernel logs): history"""
        status = asyncio.run(self.os.get_kernel_status())
        history = status["bootstrap"]

        table = Table(title="Self-Bootstrap Audit History (Kernel Logs)")
        table.add_column("ID", style="dim")
        table.add_column("Action", style="cyan")
        table.add_column("Target", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Time", style="dim")

        for record in history:
            table.add_row(
                record["id"][:8],
                record["action"],
                record["target"],
                record["status"],
                record["timestamp"]
            )
        self.console.print(table)

    def do_ls(self, arg):
        """List available templates or capabilities: ls [templates|capabilities]"""
        info = asyncio.run(self.os.get_kernel_status())["registry"]
        if arg == "capabilities":
            items = info.get("capabilities", [])
            title = "Registered Capabilities"
        else:
            items = info.get("templates", [])
            title = "Available Intent Templates"

        table = Table(title=title)
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="green")

        for item in items:
            table.add_row(item["name"], item.get("description", "N/A"))

        self.console.print(table)

    def do_cat(self, arg):
        """View a specific template or program details: cat name"""
        if not arg:
            self.console.print("Usage: cat name", style="red")
            return

        # Check in templates
        status = asyncio.run(self.os.get_kernel_status())
        templates = status["registry"]["templates"]
        for t in templates:
            if t["name"] == arg:
                self.console.print(Panel(json.dumps(t, indent=2, ensure_ascii=False), title=f"Template: {arg}"))
                return

        self.console.print(f"Item {arg} not found.", style="red")

    def do_exit(self, arg):
        """Exit IntentOS Shell: exit"""
        self.console.print("Shutting down IntentOS Kernel...", style="bold red")
        return True

    def do_EOF(self, arg):
        print("")
        return True

def start_shell():
    try:
        IntentShell().cmdloop()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    start_shell()
