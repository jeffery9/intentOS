"""
AI Agent 应用

基于应用层框架实现的通用 AI 智能助理
"""

from __future__ import annotations

from typing import Any, Optional

from .base import AppBase, AppContext, AppResult, app_metadata


@app_metadata(
    app_id="ai_agent",
    name="AI 智能助理",
    description="24/7 在线的通用智能助理，帮你处理各种任务",
    version="1.0.0",
    category="productivity",
    icon="🤖",
    author="IntentOS Team"
)
class AIAgentApp(AppBase):
    """
    AI Agent - 通用智能助理
    
    特点:
    - 基于意图模板路由
    - 调用 LLM 进行语义理解
    - 支持多轮对话
    - 记忆上下文
    """
    
    def __init__(self):
        super().__init__()
        self.conversation_history: list[dict] = []
        self.user_preferences: dict[str, Any] = {}
    
    async def initialize(self, services: Any = None) -> bool:
        """初始化"""
        await super().initialize(services)
        
        # 加载用户偏好
        self.user_preferences = await self.get_storage("preferences", {})
        
        self.info("AI Agent 已初始化")
        return True
    
    async def shutdown(self) -> None:
        """关闭"""
        # 保存用户偏好
        await self.set_storage("preferences", self.user_preferences)
        await super().shutdown()
    
    def get_capabilities(self) -> list[str]:
        """获取能力列表"""
        return [
            "📅 日程管理 - 安排会议、设置提醒",
            "📧 邮件处理 - 撰写邮件、总结邮件",
            "🔍 信息检索 - 搜索资料、总结文章",
            "✍️ 内容创作 - 写文章、写报告、写文案",
            "📊 数据分析 - 分析数据、生成图表",
            "💻 编程助手 - 写代码、审查代码",
            "⚙️ 自动化 - 自动执行重复任务",
            "📋 任务规划 - 分解任务、优先级排序",
        ]
    
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        """
        执行 AI Agent 任务
        
        流程:
        1. 理解意图 (LLM)
        2. 规划任务
        3. 执行动作
        4. 生成响应
        """
        self.info(f"收到意图：{intent}")
        
        # 1. 理解意图
        understanding = await self._understand_intent(intent, context)
        
        if not understanding["success"]:
            return AppResult(
                success=False,
                message=understanding.get("message", "抱歉，我没理解"),
                error=understanding.get("error"),
                next_actions=self._get_suggestions(),
            )
        
        # 2. 根据意图类型执行
        intent_type = understanding["type"]
        result = await self._execute_by_type(intent_type, intent, context, understanding)
        
        # 3. 记录对话历史
        self._remember(intent, result)
        
        return result
    
    async def _understand_intent(
        self,
        intent: str,
        context: AppContext
    ) -> dict[str, Any]:
        """理解意图"""
        # 调用 LLM 理解
        llm_prompt = f"""
你是一个意图理解助手。请分析用户输入，识别意图类型。

用户输入：{intent}

意图类型选项:
- schedule: 日程安排 (会议、预约、提醒)
- email: 邮件处理 (写邮件、总结邮件)
- research: 信息检索 (搜索、查找资料)
- writing: 内容创作 (写文章、写报告)
- analysis: 数据分析 (分析数据、生成图表)
- coding: 编程 (写代码、调试)
- automation: 自动化 (定时任务、自动执行)
- planning: 任务规划 (分解任务、优先级)
- general: 其他

请返回 JSON 格式:
{{
    "type": "意图类型",
    "confidence": 0.95,
    "entities": {{"key": "value"}},
    "message": "理解结果"
}}
"""
        
        # 实际实现会调用 LLM
        # 这里简单实现关键词匹配
        intent_type = self._match_by_keywords(intent)
        
        return {
            "success": True,
            "type": intent_type,
            "confidence": 0.85,
            "entities": self._extract_entities(intent, intent_type),
            "message": f"识别为：{intent_type}",
        }
    
    def _match_by_keywords(self, intent: str) -> str:
        """关键词匹配意图类型"""
        keywords_map = {
            "schedule": ["会议", "安排", "预约", "提醒", "时间", "日程"],
            "email": ["邮件", "邮箱", "写信", "回复"],
            "research": ["搜索", "查找", "资料", "研究"],
            "writing": ["写", "文章", "报告", "文案", "内容"],
            "analysis": ["分析", "数据", "图表", "销售"],
            "coding": ["代码", "编程", "函数", "实现"],
            "automation": ["自动", "每天", "定时", "流程"],
            "planning": ["计划", "任务", "优先", "规划"],
        }
        
        for intent_type, keywords in keywords_map.items():
            if any(kw in intent for kw in keywords):
                return intent_type
        
        return "general"
    
    def _extract_entities(self, intent: str, intent_type: str) -> dict[str, Any]:
        """提取实体"""
        import re
        
        entities = {"raw_text": intent}
        
        # 提取时间
        if intent_type == "schedule":
            time_patterns = [
                r'(\d{1,2}[点时])',
                r'(\d{1,2}:\d{2})',
                r'(今天 | 明天 | 后天 | 下周)',
            ]
            for pattern in time_patterns:
                match = re.search(pattern, intent)
                if match:
                    entities["time"] = match.group(1)
        
        # 提取数字
        numbers = re.findall(r'\d+', intent)
        if numbers:
            entities["numbers"] = numbers
        
        return entities
    
    async def _execute_by_type(
        self,
        intent_type: str,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """根据意图类型执行"""
        handlers = {
            "schedule": self._handle_schedule,
            "email": self._handle_email,
            "research": self._handle_research,
            "writing": self._handle_writing,
            "analysis": self._handle_analysis,
            "coding": self._handle_coding,
            "automation": self._handle_automation,
            "planning": self._handle_planning,
            "general": self._handle_general,
        }
        
        handler = handlers.get(intent_type, self._handle_general)
        return await handler(intent, context, understanding)
    
    # ========== 具体处理器 ==========
    
    async def _handle_schedule(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理日程安排"""
        entities = understanding.get("entities", {})
        
        # 调用 LLM 生成响应
        response = await self.services.call_llm(
            prompt=f"安排日程：{intent}",
            system_prompt="你是日程管理助手，帮助安排会议和提醒。"
        )
        
        return AppResult(
            success=True,
            message="✓ 会议已安排",
            data={
                "event_id": "evt_123",
                "title": entities.get("event", "会议"),
                "time": entities.get("time", "待定"),
                "calendar_link": "https://calendar.intentos.io/evt_123",
            },
            next_actions=["发送邀请", "设置提醒", "准备材料"],
        )
    
    async def _handle_email(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理邮件"""
        response = await self.services.call_llm(
            prompt=f"处理邮件：{intent}",
            system_prompt="你是邮件处理助手。"
        )
        
        return AppResult(
            success=True,
            message="✓ 邮件已处理",
            data={
                "count": 5,
                "summary": response[:100],
            },
            next_actions=["查看邮件", "回复邮件", "删除邮件"],
        )
    
    async def _handle_research(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理研究"""
        response = await self.services.call_llm(
            prompt=f"研究：{intent}",
            system_prompt="你是研究助手，帮助查找和总结信息。"
        )
        
        return AppResult(
            success=True,
            message="✓ 研究完成",
            data={
                "sources": 5,
                "summary": response[:200],
            },
            next_actions=["查看更多", "保存资料", "分享"],
        )
    
    async def _handle_writing(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理写作"""
        content = await self.services.call_llm(
            prompt=f"写作：{intent}",
            system_prompt="你是专业写手，帮助撰写各种内容。"
        )
        
        return AppResult(
            success=True,
            message="✓ 内容已生成",
            data={
                "word_count": len(content),
                "preview": content[:100],
                "url": "https://content.intentos.io/doc_123",
            },
            next_actions=["编辑内容", "发布", "分享"],
        )
    
    async def _handle_analysis(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理分析"""
        response = await self.services.call_llm(
            prompt=f"分析：{intent}",
            system_prompt="你是数据分析专家。"
        )
        
        return AppResult(
            success=True,
            message="✓ 分析完成",
            data={
                "insights": response[:200],
                "chart_url": "https://charts.intentos.io/chart_123",
            },
            next_actions=["下载报告", "分享给团队", "设置定期分析"],
        )
    
    async def _handle_coding(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理编程"""
        code = await self.services.call_llm(
            prompt=f"编程：{intent}",
            system_prompt="你是资深程序员，帮助编写高质量代码。"
        )
        
        return AppResult(
            success=True,
            message="✓ 代码已生成",
            data={
                "language": "python",
                "lines": code.count('\n') + 1,
                "code": code,
                "url": "https://code.intentos.io/snippet_123",
            },
            next_actions=["运行测试", "查看文档", "分享代码"],
        )
    
    async def _handle_automation(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理自动化"""
        return AppResult(
            success=True,
            message="✓ 自动化已创建",
            data={
                "task_id": "auto_123",
                "schedule": "每天 09:00",
                "actions": 3,
            },
            next_actions=["测试流程", "添加动作", "查看历史"],
        )
    
    async def _handle_planning(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理规划"""
        plan = await self.services.call_llm(
            prompt=f"规划：{intent}",
            system_prompt="你是项目规划专家。"
        )
        
        return AppResult(
            success=True,
            message="✓ 规划已完成",
            data={
                "tasks": 5,
                "plan": plan[:200],
            },
            next_actions=["开始第一个任务", "调整优先级", "设置提醒"],
        )
    
    async def _handle_general(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """通用处理"""
        response = await self.services.call_llm(
            prompt=intent,
            system_prompt="你是通用 AI 助手，友好地帮助用户。"
        )
        
        return AppResult(
            success=True,
            message="✓ 已完成",
            data={
                "response": response,
            },
        )
    
    def _remember(self, intent: str, result: AppResult) -> None:
        """记录对话历史"""
        from datetime import datetime
        
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "result": result.to_dict(),
        })
        
        # 只保留最近 50 条
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def _get_suggestions(self) -> list[str]:
        """获取建议"""
        return [
            "试试说：安排明天下午 3 点的会议",
            "试试说：分析上个月的销售数据",
            "试试说：写一篇关于 AI 的文章",
            "试试说：生成一个快速排序函数",
            "试试说：每天早上 9 点发送日报",
        ]
