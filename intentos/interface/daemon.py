"""
IntentOS 守护进程启动脚本

以后台服务模式运行 IntentOS，持续监听和处理请求
"""

import signal
import sys
import time
from datetime import datetime

from intentos.interface.interface import IntentOS


class IntentOSDaemon:
    """
    IntentOS 守护进程
    
    持续运行 OS 内核，提供后台服务
    """

    def __init__(self):
        self.os = IntentOS()
        self.start_time = None
        self._should_run = True

    def initialize(self) -> None:
        """初始化系统"""
        print("🚀 Initializing IntentOS...")
        self.os.initialize()
        self.start_time = datetime.now()
        print("✅ IntentOS initialized successfully")

    def _signal_handler(self, sig, frame):
        """处理中断信号"""
        print("\n🛑  Shutting down IntentOS...")
        self._should_run = False
        self.os.shutdown()
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

    def run(self) -> None:
        """
        运行守护进程
        
        持续运行直到接收到中断信号
        """
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 初始化
        self.initialize()

        # 打印状态
        print("\n" + "=" * 60)
        print("  IntentOS Daemon is running")
        print("=" * 60)
        print(f"  Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Mode: Daemon Process")
        print(f"  PID: {self.get_pid()}")
        print("=" * 60)
        print("\nPress Ctrl+C to stop\n")

        # 主循环 - 保持运行
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 启动后台服务
            async def background_monitor():
                """后台监控循环"""
                while self._should_run:
                    # 这里可以添加定期任务
                    # 例如：健康检查、内存清理、进程监控等
                    await asyncio.sleep(60)  # 每分钟检查一次
            
            # 启动监控任务
            monitor_task = loop.create_task(background_monitor())
            self.os._background_tasks.append(monitor_task)
            
            # 运行事件循环
            loop.run_forever()
        except KeyboardInterrupt:
            self._signal_handler(None, None)

    def get_pid(self) -> int:
        """获取进程 ID"""
        import os
        return os.getpid()


def start_daemon():
    """启动守护进程"""
    daemon = IntentOSDaemon()
    daemon.run()


if __name__ == "__main__":
    start_daemon()
