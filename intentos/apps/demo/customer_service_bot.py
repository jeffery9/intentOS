# -*- coding: utf-8 -*-
"""
Customer Service Bot Demo App

智能客服机器人 - 自动回答用户问题，处理客户支持请求。
计费模式：按对话次数 $0.01/次
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from intentos.agent.submission import IntentOSConnector, LocalAppBuilder

logger: logging.Logger = logging.getLogger(__name__)


class CustomerServiceBotApp:
    """
    智能客服机器人 App

    功能：
    - 自动回答常见问题
    - 订单查询
    - 投诉处理
    - 转人工客服

    计费：$0.01/次对话
    """

    def __init__(self) -> None:
        self.name: str = "customer_service_bot"
        self.version: str = "1.0.0"
        self.description: str = "智能客服机器人"
        self.icon: str = "🤖"
        self.pricing: dict[str, Any] = {
            "model": "pay_per_call",
            "price_per_call": 0.01,  # $0.01/次
        }
        logger.info(f"客服机器人 App 初始化：{self.name}")

    def build_package(self) -> LocalAppBuilder:
        """构建意图包"""
        builder = LocalAppBuilder()

        builder.create_package(
            name=self.name,
            version=self.version,
            description=self.description,
            author="IntentOS Team",
        )

        # 添加意图
        builder.add_intent(
            intent_id="faq_query",
            name="常见问题查询",
            description="回答用户常见问题",
            patterns=[
                ".*怎么.*",
                ".*如何.*",
                ".*为什么.*",
                ".*是什么.*",
            ],
            required_capabilities=["knowledge_base_search", "response_generator"],
            pricing=self.pricing,
        )

        builder.add_intent(
            intent_id="order_lookup",
            name="订单查询",
            description="查询订单状态",
            patterns=[
                ".*订单.*",
                ".*物流.*",
                ".*发货.*",
                "我的订单.*",
            ],
            required_capabilities=["order_api", "response_generator"],
            pricing=self.pricing,
        )

        builder.add_intent(
            intent_id="complaint_handling",
            name="投诉处理",
            description="处理用户投诉",
            patterns=[
                ".*投诉.*",
                ".*不满意.*",
                ".*太差.*",
                ".*退款.*",
            ],
            required_capabilities=["ticket_creation", "sentiment_analysis", "refund_api"],
            pricing={"model": "pay_per_call", "price_per_call": 0.02},  # 投诉处理更贵
        )

        builder.add_intent(
            intent_id="human_transfer",
            name="转人工客服",
            description="转接人工客服",
            patterns=[
                ".*人工.*",
                ".*客服.*",
                ".*真人.*",
                "转.*",
            ],
            required_capabilities=["ticket_creation", "agent_routing"],
            pricing={"model": "free"},  # 转人工免费
        )

        # 注册能力
        builder.register_capability(
            cap_id="knowledge_base_search",
            name="知识库搜索",
            description="搜索知识库获取答案",
            tags=["knowledge", "search"],
            pricing={"model": "free"},
        )

        builder.register_capability(
            cap_id="order_api",
            name="订单 API",
            description="查询订单信息",
            tags=["order", "api"],
            pricing={"model": "free"},
        )

        builder.register_capability(
            cap_id="ticket_creation",
            name="工单创建",
            description="创建客服工单",
            tags=["ticket", "support"],
            pricing={"model": "free"},
        )

        builder.register_capability(
            cap_id="sentiment_analysis",
            name="情感分析",
            description="分析用户情绪",
            tags=["nlp", "sentiment"],
            pricing={"model": "free"},
        )

        builder.register_capability(
            cap_id="response_generator",
            name="回复生成",
            description="生成客服回复",
            tags=["nlp", "generation"],
            pricing={"model": "free"},
        )

        builder.register_capability(
            cap_id="agent_routing",
            name="客服路由",
            description="分配给人工客服",
            tags=["routing", "support"],
            pricing={"model": "free"},
        )

        # 设置默认计费
        builder.set_pricing(**self.pricing)

        return builder

    async def handle_query(self, user_message: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        处理用户询问

        Args:
            user_message: 用户消息
            context: 上下文信息（用户 ID、历史对话等）

        Returns:
            回复结果
        """
        logger.info(f"处理用户消息：{user_message}")

        # 实际实现会调用 IntentOS 执行对应的意图
        # 这里模拟响应

        response = {
            "success": True,
            "message": self._generate_response(user_message),
            "suggested_actions": self._get_suggested_actions(user_message),
            "billing": {
                "amount": 0.01,
                "currency": "USD",
                "description": "客服对话",
            },
            "metadata": {
                "app_id": self.name,
                "version": self.version,
            },
        }

        return response

    def _generate_response(self, message: str) -> str:
        """生成回复（模拟）"""
        if "订单" in message or "物流" in message:
            return "您好，请提供您的订单号，我帮您查询订单状态。"
        elif "退款" in message or "退货" in message:
            return "很抱歉给您带来不便。请问您申请退款的原因是什么？"
        elif "人工" in message or "客服" in message:
            return "好的，正在为您转接人工客服，请稍候..."
        else:
            return "您好，我是智能客服助手，请问有什么可以帮您？"

    def _get_suggested_actions(self, message: str) -> list[str]:
        """获取建议操作"""
        if "订单" in message:
            return ["查询订单", "取消订单", "修改订单"]
        elif "退款" in message:
            return ["申请退款", "退货流程", "退款进度"]
        else:
            return ["常见问题", "订单查询", "转人工客服"]

    async def submit_to_intentos(
        self,
        intentos_url: str = "http://localhost:8080",
        api_key: Optional[str] = None
    ) -> dict[str, Any]:
        """提交到 IntentOS"""
        connector = IntentOSConnector(intentos_url, api_key)

        async with connector:
            builder = self.build_package()

            # 验证
            errors = builder.validate()
            if errors:
                raise ValueError(f"App 验证失败：{', '.join(errors)}")

            # 提交
            result = await connector.submit(wait_for_approval=False)

            logger.info(f"客服机器人 App 已提交：{result['app_id']}")

            return result


# 便捷创建函数
def create_customer_service_bot() -> CustomerServiceBotApp:
    """创建客服机器人 App"""
    return CustomerServiceBotApp()
