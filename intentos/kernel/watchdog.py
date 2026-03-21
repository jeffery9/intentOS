"""
语义自愈监视器 (Semantic Watchdog)

核心职责：
1. 监控处理器健康度 (Processor Health)
2. 检查内存一致性 (Memory Consistency)
3. 自动修复损坏的系统 Prompt (Self-Healing)
4. 资源配额与熔断 (Gas & Resource Guard)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    is_healthy: bool
    last_check: datetime = field(default_factory=datetime.now)
    issues: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

class SemanticWatchdog:
    """
    语义自愈监视器
    """

    def __init__(self, vm: Any):
        self.vm = vm
        self.status = HealthStatus(is_healthy=True)
        self._running = False
        self._check_interval = 30  # 秒
        self._known_good_prompt: Optional[str] = None
        self._lock = asyncio.Lock()

    async def start(self):
        """启动监视器"""
        self._running = True
        # 记录初始的已知良好 Prompt
        if self.vm.processor:
            self._known_good_prompt = self.vm.processor.processor_prompt

        logger.info("Semantic Watchdog started")
        asyncio.create_task(self._monitoring_loop())

    def stop(self):
        """停止监视器"""
        self._running = False

    async def _monitoring_loop(self):
        while self._running:
            try:
                await self.check_system_health()
                if not self.status.is_healthy:
                    await self.perform_self_healing()
            except Exception as e:
                logger.error(f"Watchdog monitoring error: {e}")

            await asyncio.sleep(self._check_interval)

    async def check_system_health(self) -> HealthStatus:
        """全面健康检查"""
        issues = []
        metrics = {}

        # 1. 检查 VM 是否存活
        if not self.vm:
            issues.append("VM instance is missing")

        # 2. 检查处理器 Prompt 是否为空或过短 (疑似损坏)
        if self.vm.processor:
            current_prompt = self.vm.processor.processor_prompt
            metrics["prompt_length"] = len(current_prompt)
            if len(current_prompt) < 100:
                issues.append("System processor prompt is suspiciously short or corrupted")

        # 3. 检查内存状态
        memory_state = self.vm.memory.get_state()
        metrics.update(memory_state)

        # 审计日志过大警告
        if memory_state.get("audit_log_count", 0) > 10000:
            issues.append("Audit log exceeds safety threshold")

        # 4. 检查是否有僵尸进程
        if hasattr(self.vm, 'coordinator'):
            processes = await self.vm.coordinator.get_process_list()
            metrics["active_processes"] = len(processes)
            zombies = [p for p in processes if p.state.value == "zombie"]
            if zombies:
                issues.append(f"Detected {len(zombies)} zombie processes")

        self.status = HealthStatus(
            is_healthy=len(issues) == 0,
            last_check=datetime.now(),
            issues=issues,
            metrics=metrics
        )
        return self.status

    async def perform_self_healing(self):
        """执行自愈"""
        async with self._lock:
            logger.warning(f"Starting self-healing for issues: {self.status.issues}")

            for issue in self.status.issues:
                # 修复 Prompt 损坏
                if "prompt" in issue.lower() and self._known_good_prompt:
                    logger.info("Restoring processor prompt to known good state")
                    self.vm.processor.update_processor_prompt(self._known_good_prompt)

                # 清理审计日志
                if "audit log" in issue.lower():
                    logger.info("Truncating audit logs")
                    self.vm.memory.audit_log = self.vm.memory.audit_log[-1000:]

                # 清理僵尸进程
                if "zombie" in issue.lower() and hasattr(self.vm, 'coordinator'):
                    logger.info("Cleaning up zombie processes")
                    for pid in list(self.vm.coordinator.processes.keys()):
                        if self.vm.coordinator.processes[pid].state.value == "zombie":
                            del self.vm.coordinator.processes[pid]

            # 修复完成后重新检查
            await self.check_system_health()
            if self.status.is_healthy:
                logger.info("System successfully self-healed")

    def get_report(self) -> dict:
        """获取监视报告"""
        return {
            "is_healthy": self.status.is_healthy,
            "last_check": self.status.last_check.isoformat(),
            "issues": self.status.issues,
            "metrics": self.status.metrics
        }
