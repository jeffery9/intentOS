# -*- coding: utf-8 -*-
"""
IntentOS Runtime - The "Run" Daemon & Event-Driven Engine

常驻运行引擎：
- UNIX 哲学的物理载体 (Run is Delivery)
- 挂载事件触发器 (Webhook, Cron, FileWatch)
- 打包人类第一因 IntentSingularity，并注入 SemanticVM 执行 Pipeline 串联。
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional

from ..core.singularity import IntentSingularity
from ..semantic_vm.vm import SemanticVM

logger = logging.getLogger(__name__)


@dataclass
class EventTrigger:
    """事件触发器描述"""
    trigger_id: str
    trigger_type: str  # cron, file_watch, webhook, etc.
    config: dict[str, Any]
    target_program: str
    last_triggered: float = 0.0
    active: bool = True


class DaemonRunner:
    """
    事件驱动常驻运行守护进程 (The Run Daemon)
    
    事件源 ➔ 激活 ➔ 组装 IntentSingularity ➔ 激活 SemanticVM Pipeline ➔ 产出输出。
    """
    
    def __init__(self, vm: SemanticVM):
        """
        初始化守护进程
        
        Args:
            vm: 绑定的语义虚拟机实例 (大脑)
        """
        self.vm = vm
        self.triggers: dict[str, EventTrigger] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info("[Daemon] 意图事件守护进程初始化完成，准备注入生命心跳...")

    def register_trigger(
        self,
        trigger_id: str,
        trigger_type: str,
        config: dict[str, Any],
        target_program: str,
    ) -> None:
        """注册一个物理事件触发器"""
        trigger = EventTrigger(
            trigger_id=trigger_id,
            trigger_type=trigger_type,
            config=config,
            target_program=target_program,
        )
        self.triggers[trigger_id] = trigger
        logger.info(f"[Daemon] 成功注册触发器 '{trigger_id}' ({trigger_type}) ➔ 联动程序 '{target_program}'")

    async def start(self) -> None:
        """开启常驻事件循环"""
        if self._running:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._main_loop())
        logger.info("[Daemon] 守护守护进程已成功启动，进入物理现实观测态...")

    async def stop(self) -> None:
        """安全停止守护进程"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[Daemon] 守护进程已安全休眠。")

    async def _main_loop(self) -> None:
        """主事件扫描环"""
        while self._running:
            current_time = time.time()
            
            # 扫描所有激活的触发器
            for trigger_id, trigger in list(self.triggers.items()):
                if not trigger.active:
                    continue
                    
                # 评估是否触发
                should_fire, payload = await self._evaluate_trigger(trigger, current_time)
                if should_fire:
                    trigger.last_triggered = current_time
                    # 触发后台异步 Pipeline
                    asyncio.create_task(self._fire_pipeline(trigger, payload))
                    
            # 基础观测心跳周期
            await asyncio.sleep(0.5)

    async def _evaluate_trigger(self, trigger: EventTrigger, current_time: float) -> tuple[bool, dict[str, Any]]:
        """评估触发器条件是否满足"""
        
        # 1. 定时触发器 (Cron / Interval)
        if trigger.trigger_type == "cron":
            interval = trigger.config.get("interval_seconds", 60)
            if current_time - trigger.last_triggered >= interval:
                return True, {"timestamp": current_time, "reason": f"定时周期触发 ({interval}s)"}
                
        # 2. 物理文件监控触发器 (File Watcher)
        elif trigger.trigger_type == "file_watch":
            watch_dir = trigger.config.get("directory")
            if watch_dir and os.path.exists(watch_dir):
                files = os.listdir(watch_dir)
                # 过滤出未处理的新文件
                unprocessed_files = [
                    f for f in files 
                    if not f.startswith(".") and os.path.getmtime(os.path.join(watch_dir, f)) > trigger.last_triggered
                ]
                if unprocessed_files:
                    return True, {
                        "files": unprocessed_files, 
                        "directory": watch_dir,
                        "reason": f"监测到目录新文件: {unprocessed_files}"
                    }
                    
        # 3. Webhook 触发器 (Webhook - 模拟网口数据)
        elif trigger.trigger_type == "webhook":
            # 实际场景可与 RuntimeAgent /v1/api 联动，此处提供轮询网卡队列的机制
            queue = trigger.config.get("_mock_webhook_queue")
            if queue and len(queue) > 0:
                data = queue.pop(0)
                return True, {"payload": data, "reason": "Webhook 外部语义请求注入"}

        return False, {}

    async def _fire_pipeline(self, trigger: EventTrigger, payload: dict[str, Any]) -> None:
        """
        [关键步骤] 激发语义管道
        
        将物理事件 Payload 打包，加签不可篡改的人类“意图奇点”第一因，
        强行注入虚拟机并以“顾问路由策略”执行连续的语义管道。
        """
        logger.info(f"\n[Daemon] 🚀 触发器 '{trigger.trigger_id}' 暴走！物理事件源就位。")
        logger.info(f"[Daemon] 原始物理 Payload: {payload}")
        
        # ① 组装 IntentSingularity (第一因)
        raw_intent = f"物理事件触发 {trigger.target_program}，环境上下文: {payload.get('reason', '无')}"
        singularity = IntentSingularity(
            singularity_id=f"singularity_{trigger.trigger_id}_{int(time.time())}",
            raw_intent=raw_intent,
            context_metadata=payload,
            assertions=trigger.config.get("assertions", []),
            gas_limit=trigger.config.get("gas_limit", 1000)
        )
        
        logger.info(f"[Daemon] ⛓️ 组装只读人类意图奇点: {singularity.singularity_id}")
        
        # ② 注入 VM 变量，作为第一级 STDIN
        # 我们将整个 Payload 与 Singularity 作为第一节管道的输入注入
        program = self.vm.memory.get("PROGRAM", trigger.target_program)
        if not program:
            logger.error(f"[Daemon] 执行失败：联动程序 '{trigger.target_program}' 不在语义内存中")
            return
            
        program.variables["_last_result"] = f"事件元数据: {payload}"
        
        # ③ 激活动态 Pipeline 执行 (开启高精度专家护航)
        logger.info(f"[Daemon] 运转语义 VM，执行管道程序 '{trigger.target_program}' (策略: consultant)...")
        pipeline_result = await self.vm.execute_program(
            program_name=trigger.target_program,
            context={"gas_limit": singularity.gas_limit},
            strategy="consultant"
        )
        
        # ④ 产出交付 (Run is Delivery)
        if pipeline_result.get("success", False):
            # 获取终阶管道标准 STDOUT
            final_output = program.variables.get("_last_result")
            logger.info(f"[Daemon] ✓ 管道成功交付！终态 Standard Output:")
            logger.info(f"--------------------------------------------------")
            logger.info(f"{final_output}")
            logger.info(f"--------------------------------------------------")
        else:
            logger.error(f"[Daemon] ❌ 管道执行崩溃：{pipeline_result.get('error', '未知错误')}")
