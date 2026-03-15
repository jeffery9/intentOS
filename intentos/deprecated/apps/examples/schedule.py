"""
示例应用 - 日程管理

演示如何基于 AppBase 开发应用
"""

from __future__ import annotations

from typing import Any
from ..base import AppBase, AppContext, AppResult, app_metadata


@app_metadata(
    app_id="schedule_manager",
    name="日程管理",
    description="安排会议、设置提醒、管理日程",
    version="1.0.0",
    category="productivity",
    icon="📅",
    author="IntentOS Team"
)
class ScheduleManagerApp(AppBase):
    """
    日程管理应用
    
    使用方法:
    1. 继承 AppBase
    2. 使用 @app_metadata 装饰器
    3. 实现 execute() 和 get_capabilities()
    """
    
    async def initialize(self, services: Any = None) -> bool:
        """初始化"""
        await super().initialize(services)
        
        # 加载配置
        self.default_reminder = await self.get_config("default_reminder", 15)
        
        return True
    
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        """执行日程管理任务"""
        self.log("info", f"执行日程管理：{intent}")
        
        # 简单实现，实际应该用 LLM 解析意图
        if any(kw in intent for kw in ["会议", "预约", "提醒"]):
            return await self._handle_schedule(intent, context)
        elif "日历" in intent:
            return await self._handle_calendar(intent, context)
        else:
            return AppResult(
                success=False,
                message="抱歉，我无法处理这个请求",
                error="unsupported_intent",
            )
    
    def get_capabilities(self) -> list[str]:
        """获取能力列表"""
        return [
            "安排会议",
            "设置提醒",
            "查看日历",
            "修改日程",
            "取消日程",
        ]
    
    async def _handle_schedule(
        self,
        intent: str,
        context: AppContext
    ) -> AppResult:
        """处理日程安排"""
        # 实际实现会调用 LLM 解析时间、参与者等
        return AppResult(
            success=True,
            message="✓ 会议已安排",
            data={
                "event_id": "evt_123",
                "title": "会议",
                "time": "2026-03-16 15:00",
                "reminder": f"提前{self.default_reminder}分钟",
            },
            next_actions=["发送邀请", "设置提醒", "准备材料"],
        )
    
    async def _handle_calendar(
        self,
        intent: str,
        context: AppContext
    ) -> AppResult:
        """处理日历查询"""
        return AppResult(
            success=True,
            message="✓ 日历已获取",
            data={
                "today_events": 3,
                "week_events": 10,
            },
        )
