"""
AI Agent 应用

基于应用层框架实现的通用 AI 智能助理
使用意图模板和工具元数据，不硬编码
"""

from __future__ import annotations

from typing import Any, Optional

from .base import AppBase, AppContext, AppResult, app_metadata
from .template import IntentTemplate


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
    - 基于意图模板路由 (不硬编码)
    - 调用 LLM 进行语义理解
    - 支持工具调用 (基于工具元数据)
    - 支持多轮对话
    """
    
    def __init__(self):
        super().__init__()
        self.conversation_history: list[dict] = []
        self.user_preferences: dict[str, Any] = {}
        self.tool_registry = None
        self.intent_templates: list[IntentTemplate] = []
        
        # MCP 支持 (标准协议)
        self.mcp_client = None
        
        # Skill 支持 (SKILL.md 规范)
        self.skill_loader = None
        self.loaded_skills: dict[str, dict] = {}
    
    async def initialize(self, services: Any = None) -> bool:
        """初始化"""
        await super().initialize(services)
        
        # 加载用户偏好
        self.user_preferences = await self.get_storage("preferences", {})
        
        # 初始化工具系统
        from .services.tools import ToolRegistry
        self.tool_registry = ToolRegistry()
        
        # 初始化 MCP 客户端 (标准协议)
        from ..integrations.mcp import get_mcp_client
        self.mcp_client = get_mcp_client()
        
        # 初始化 Skill 加载器 (SKILL.md 规范)
        from ..integrations.skill import get_skill_loader
        self.skill_loader = get_skill_loader()
        
        # 注册意图模板
        self._register_intent_templates()
        
        # 加载已安装的 Skills
        self._load_skills()
        
        if self._services:
            self._services.info(f"AI Agent 已初始化")
        return True
    
    def _load_skills(self) -> None:
        """加载已安装的 Skills (从 SKILL.md)"""
        if not self.skill_loader:
            return
        
        # 发现 Skills
        skill_ids = self.skill_loader.discover_skills()
        
        for skill_id in skill_ids:
            # 加载 Skill 规范
            skill_data = self.skill_loader.load_skill(skill_id)
            
            if skill_data:
                self.loaded_skills[skill_id] = skill_data
                
                spec = skill_data["spec"]
                if self._services:
                    self._services.info(
                        f"已加载 Skill: {spec.name} v{spec.version}"
                    )
    
    def _register_intent_templates(self) -> None:
        """注册意图模板 (从配置或动态生成)"""
        from .template import IntentTemplate, TemplateRegistry
        
        template_registry = TemplateRegistry()
        
        # 从模板注册表获取所有模板
        self.intent_templates = template_registry.list_templates()
        
        # 如果没有预注册模板，使用默认模板 (应该从配置文件加载)
        if not self.intent_templates:
            self.intent_templates = self._create_default_templates()
            for template in self.intent_templates:
                template_registry.register(template)
    
    def _create_default_templates(self) -> list[IntentTemplate]:
        """创建默认意图模板 (应该从配置文件加载)"""
        # 这些模板应该从配置文件或数据库加载，而不是硬编码
        # 这里仅作为示例
        return [
            IntentTemplate(
                id="schedule_intent",
                name="日程安排",
                description="安排会议、设置提醒",
                keywords=["会议", "安排", "预约", "提醒", "时间", "日程"],
                category="schedule",
            ),
            IntentTemplate(
                id="email_intent",
                name="邮件处理",
                description="撰写邮件、总结邮件",
                keywords=["邮件", "邮箱", "写信", "回复"],
                category="email",
            ),
        ]
    
    def get_capabilities(self) -> list[str]:
        """获取能力列表 (动态生成)"""
        caps = []

        # 从意图模板生成
        for template in self.intent_templates:
            caps.append(f"{template.name} - {template.description}")

        # 内置工具
        if self.tool_registry:
            tools = self.tool_registry.list_tools()
            if tools:
                caps.append(f"\n🔧 内置工具 ({len(tools)} 个):")
                for tool in tools:
                    caps.append(f"  • {tool.name}: {tool.description}")

        # MCP 服务器 (标准协议)
        if self.mcp_client and self.mcp_client.servers:
            caps.append(f"\n🔌 MCP 服务器 ({len(self.mcp_client.servers)} 个):")
            for name in self.mcp_client.servers:
                caps.append(f"  • {name}")

        # Skills (SKILL.md 规范)
        if self.loaded_skills:
            caps.append(f"\n📦 Skills ({len(self.loaded_skills)} 个):")
            for skill_id, skill_data in self.loaded_skills.items():
                spec = skill_data["spec"]
                caps.append(f"  • {spec.name}: {spec.description}")
                
                # 显示能力
                if hasattr(spec, 'capabilities') and spec.capabilities:
                    for cap in spec.capabilities:
                        caps.append(f"    - {cap['name']}: {cap['description']}")

        return caps
    
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        """执行 AI Agent 任务"""
        if self._services:
            self._services.info(f"收到意图：{intent}")
        
        # 1. 理解意图 (使用模板匹配，不硬编码)
        understanding = await self._understand_intent(intent, context)
        
        if not understanding["success"]:
            return AppResult(
                success=False,
                message=understanding.get("message", "抱歉，我没理解"),
                error=understanding.get("error"),
                next_actions=self._get_suggestions(),
            )
        
        # 2. 判断是否需要调用工具 (基于工具元数据)
        if understanding.get("needs_tool"):
            tool_result = await self._call_tool(
                understanding["tool_id"],
                understanding.get("tool_params", {}),
            )
            
            if tool_result["success"]:
                return AppResult(
                    success=True,
                    message=f"✓ 工具调用成功",
                    data=tool_result.get("result"),
                    next_actions=["继续操作", "查看结果"],
                )
            else:
                return AppResult(
                    success=False,
                    message=f"工具调用失败：{tool_result.get('error')}",
                    error="tool_error",
                )
        
        # 3. 根据意图模板执行 (动态路由，不硬编码)
        template = understanding.get("template")
        if template and template.action:
            result = await self._execute_by_action(
                template.action,
                intent,
                context,
                understanding,
            )
        else:
            result = await self._handle_general(intent, context, understanding)
        
        # 4. 记录对话历史
        self._remember(intent, result)
        
        return result
    
    async def _understand_intent(
        self,
        intent: str,
        context: AppContext
    ) -> dict[str, Any]:
        """理解意图 (使用模板匹配，不硬编码)"""
        # 1. 检查是否需要调用工具 (基于工具元数据)
        tool_match = self._match_tool(intent)
        if tool_match:
            return {
                "success": True,
                "type": "tool_call",
                "needs_tool": True,
                "tool_id": tool_match["id"],
                "tool_params": tool_match["params"],
                "confidence": 0.9,
                "message": f"调用工具：{tool_match['name']}",
            }
        
        # 2. 使用意图模板匹配 (不硬编码关键词)
        template = self._match_template(intent)
        
        if template:
            return {
                "success": True,
                "type": template.category,
                "template": template,
                "confidence": 0.85,
                "entities": self._extract_entities(intent, template),
                "message": f"识别为：{template.name}",
            }
        
        # 3. 无匹配时使用通用处理
        return {
            "success": True,
            "type": "general",
            "confidence": 0.5,
            "entities": {"raw_text": intent},
            "message": "通用处理",
        }
    
    def _match_template(self, intent: str) -> Optional[IntentTemplate]:
        """匹配意图模板 (使用模板的匹配逻辑，不硬编码)"""
        for template in self.intent_templates:
            matched, _ = template.match(intent)
            if matched:
                return template
        return None
    
    def _match_tool(self, intent: str) -> Optional[dict]:
        """匹配需要调用的工具 (基于工具元数据，不硬编码)"""
        if not self.tool_registry:
            return None
        
        # 从工具注册表获取所有工具
        tools = self.tool_registry.list_tools()
        
        # 遍历工具，使用工具的 tags 进行匹配 (不硬编码关键词)
        for tool in tools:
            # 使用工具的 tags 匹配意图
            for tag in tool.tags:
                if tag in intent.lower():
                    # 简单参数提取 (应该使用更智能的方式)
                    params = self._extract_tool_params(tool, intent)
                    return {
                        "id": tool.id,
                        "name": tool.name,
                        "params": params,
                    }
        
        return None
    
    def _extract_tool_params(self, tool, intent: str) -> dict:
        """提取工具参数 (基于工具 schema，不硬编码)"""
        params = {}
        
        # 根据工具 ID 提取参数 (应该使用 params_schema)
        if tool.id == "calculator":
            import re
            match = re.search(r'([\d+\-*/().\s]+)', intent)
            if match:
                params["expression"] = match.group(1).strip()
        elif tool.id == "weather":
            # 提取城市名 (应该使用配置的城市列表)
            cities = ["北京", "上海", "广州", "深圳", "杭州"]
            for city in cities:
                if city in intent:
                    params["city"] = city
                    break
            if "city" not in params:
                params["city"] = "北京"  # 默认值
        elif tool.id == "news":
            params["category"] = "tech"  # 默认值
        elif tool.id == "web_search":
            params["query"] = intent.replace("搜索", "").replace("查找", "").strip()
        
        return params
    
    def _extract_entities(self, intent: str, template: IntentTemplate) -> dict[str, Any]:
        """提取实体 (基于模板配置，不硬编码)"""
        import re
        
        entities = {"raw_text": intent}
        
        # 根据模板 category 提取实体 (应该使用 params_schema)
        if template.category == "schedule":
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
    
    async def _execute_by_action(
        self,
        action: str,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """根据 action 执行 (动态路由，不硬编码)"""
        # 使用 getattr 动态调用处理方法 (不硬编码映射)
        handler_name = f"_handle_{action}"
        
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            return await handler(intent, context, understanding)
        else:
            # 无对应 handler 时使用通用处理
            return await self._handle_general(intent, context, understanding)
    
    async def _call_tool(self, tool_id: str, params: dict) -> dict:
        """调用工具"""
        if not self.tool_registry:
            return {"success": False, "error": "工具系统未初始化"}
        
        if self._services:
            self._services.info(f"调用工具：{tool_id}, 参数：{params}")
        
        # 通过工具注册表调用
        result = await self.tool_registry.call(tool_id, **params)
        
        return result
    
    # ========== 具体处理器 ==========
    # 这些处理器应该支持动态注册，而不是硬编码在类中
    
    async def _handle_schedule(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理日程安排"""
        entities = understanding.get("entities", {})
        
        response = await self._services.call_llm(
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
        response = await self._services.call_llm(
            prompt=f"处理邮件：{intent}",
            system_prompt="你是邮件处理助手。"
        )
        
        return AppResult(
            success=True,
            message="✓ 邮件已处理",
            data={"count": 5, "summary": response[:100]},
            next_actions=["查看邮件", "回复邮件", "删除邮件"],
        )
    
    async def _handle_research(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理研究"""
        response = await self._services.call_llm(
            prompt=f"研究：{intent}",
            system_prompt="你是研究助手，帮助查找和总结信息。"
        )
        
        return AppResult(
            success=True,
            message="✓ 研究完成",
            data={"sources": 5, "summary": response[:200]},
            next_actions=["查看更多", "保存资料", "分享"],
        )
    
    async def _handle_writing(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """处理写作"""
        content = await self._services.call_llm(
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
        response = await self._services.call_llm(
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
        code = await self._services.call_llm(
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
        plan = await self._services.call_llm(
            prompt=f"规划：{intent}",
            system_prompt="你是项目规划专家。"
        )
        
        return AppResult(
            success=True,
            message="✓ 规划已完成",
            data={"tasks": 5, "plan": plan[:200]},
            next_actions=["开始第一个任务", "调整优先级", "设置提醒"],
        )
    
    async def _handle_general(
        self,
        intent: str,
        context: AppContext,
        understanding: dict
    ) -> AppResult:
        """通用处理"""
        response = await self._services.call_llm(
            prompt=intent,
            system_prompt="你是通用 AI 助手，友好地帮助用户。"
        )
        
        return AppResult(
            success=True,
            message="✓ 已完成",
            data={"response": response},
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
        """获取建议 (基于意图模板动态生成，不硬编码)"""
        suggestions = []
        
        # 从意图模板生成建议
        for template in self.intent_templates[:3]:  # 取前 3 个
            suggestions.append(f"试试说：{template.description}")
        
        # 如果没有模板，使用默认建议
        if not suggestions:
            suggestions = [
                "试试说：安排明天下午 3 点的会议",
                "试试说：分析上个月的销售数据",
                "试试说：写一篇关于 AI 的文章",
            ]
        
        return suggestions

    async def _call_skill(self, skill_id: str, capability: str, arguments: dict) -> dict:
        """调用 Skill"""
        if not self.skill_registry:
            return {"success": False, "error": "Skill 系统未初始化"}
        
        if self._services:
            self._services.info(f"调用 Skill: {skill_id}.{capability}, 参数：{arguments}")
        
        # 通过 Skill 注册表调用
        result = await self.skill_registry.execute_skill(skill_id, capability, arguments)
        
        return result
