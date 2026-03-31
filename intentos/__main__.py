#!/usr/bin/env python3
"""
IntentOS 统一启动入口

用法:
    python -m intentos daemon     # 启动内核守护进程（服务器）
    python -m intentos cli        # 命令行工具（包含 shell、chat 等）
"""

import argparse
import sys


def start_daemon(args):
    """启动守护进程（服务器）"""
    from intentos.interface.daemon import start_daemon

    start_daemon(args)


def run_cli(args):
    """运行命令行工具"""
    from intentos.cli.cli import main

    main()


def main():
    parser = argparse.ArgumentParser(
        prog="intentos",
        description="IntentOS - AI 原生操作系统",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 16.0.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="启动模式")

    # daemon 命令
    p_daemon = subparsers.add_parser(
        "daemon",
        help="启动内核守护进程（服务器模式）",
        description="启动 IntentOS 内核并监听 RPC 请求",
    )
    p_daemon.add_argument("--api", action="store_true", help="同时启动 API 网关")
    p_daemon.add_argument("--api-host", default="localhost", help="API 监听地址 (默认：localhost)")
    p_daemon.add_argument("--api-port", type=int, default=8080, help="API 监听端口 (默认：8080)")
    p_daemon.set_defaults(func=start_daemon)

    # cli 命令（包含 shell、chat 等）
    p_cli = subparsers.add_parser(
        "cli", help="命令行工具", description="提供 shell、chat、图谱管理、验证、轨迹等工具命令"
    )
    p_cli.set_defaults(func=run_cli)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        print("\n" + "=" * 60)
        print("快速开始:")
        print("=" * 60)
        print("1. 启动内核（必须先执行）:")
        print("   intentos daemon              # 仅内核")
        print("   intentos daemon --api        # 内核 + API 网关")
        print()
        print("2. 访问内核（使用 CLI）:")
        print("   intentos cli                 # 进入 CLI 主界面")
        print("   intentos cli shell           # 交互式 Shell")
        print("   intentos cli chat            # Chat TUI 界面")
        print("   intentos cli status          # 系统状态")
        print()
        print("3. API 访问:")
        print("   # 方式 1：集成到 daemon（推荐）")
        print("   intentos daemon --api")
        print()
        print("   curl http://localhost:8080/v1/status")
        print("=" * 60)
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
