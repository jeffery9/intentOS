# -*- coding: utf-8 -*-
"""
Data Analyst Demo App

数据分析助手 - 用自然语言分析数据，生成洞察和报告。
计费模式：按分析时长 $0.10/分钟
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

logger: logging.Logger = logging.getLogger(__name__)


class DataAnalystApp:
    """
    数据分析助手 App

    功能：
    - 数据加载（CSV/Excel/数据库）
    - 统计分析
    - 可视化生成
    - 洞察报告

    计费：$0.10/分钟
    """

    def __init__(self) -> None:
        self.name: str = "data_analyst"
        self.version: str = "1.0.0"
        self.description: str = "数据分析助手"
        self.icon: str = "📊"
        self.pricing: dict[str, Any] = {
            "model": "pay_per_minute",
            "price_per_minute": 0.10,  # $0.10/分钟
            "minimum_charge": 0.01,
        }
        logger.info(f"数据分析助手 App 初始化：{self.name}")

    def build_package(self) -> dict[str, Any]:
        """构建意图包"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": "IntentOS Team",
            "icon": self.icon,
            "intents": {
                "data_load": {
                    "id": "data_load",
                    "name": "数据加载",
                    "description": "从文件加载数据",
                    "patterns": [
                        ".*加载.*数据.*",
                        ".*导入.*数据.*",
                        ".*读取.*文件.*",
                    ],
                    "required_capabilities": ["file_reader", "data_parser"],
                    "pricing": {"model": "free"},
                },
                "statistical_analysis": {
                    "id": "statistical_analysis",
                    "name": "统计分析",
                    "description": "执行统计分析",
                    "patterns": [
                        ".*分析.*",
                        ".*统计.*",
                        ".*趋势.*",
                        ".*对比.*",
                    ],
                    "required_capabilities": ["stats_engine", "data_processor"],
                    "pricing": self.pricing,
                },
                "visualization": {
                    "id": "visualization",
                    "name": "可视化生成",
                    "description": "生成图表",
                    "patterns": [
                        ".*图表.*",
                        ".*可视化.*",
                        ".*画图.*",
                        ".*plot.*",
                    ],
                    "required_capabilities": ["chart_generator", "data_processor"],
                    "pricing": self.pricing,
                },
                "insight_report": {
                    "id": "insight_report",
                    "name": "洞察报告",
                    "description": "生成分析报告",
                    "patterns": [
                        ".*报告.*",
                        ".*洞察.*",
                        ".*总结.*",
                        ".*结论.*",
                    ],
                    "required_capabilities": ["report_generator", "insight_engine"],
                    "pricing": self.pricing,
                },
            },
            "capabilities": {
                "file_reader": {
                    "id": "file_reader",
                    "name": "文件读取",
                    "description": "读取 CSV/Excel 文件",
                    "tags": ["io", "file"],
                    "pricing": {"model": "free"},
                },
                "data_parser": {
                    "id": "data_parser",
                    "name": "数据解析",
                    "description": "解析数据格式",
                    "tags": ["parser", "data"],
                    "pricing": {"model": "free"},
                },
                "stats_engine": {
                    "id": "stats_engine",
                    "name": "统计引擎",
                    "description": "统计分析计算",
                    "tags": ["stats", "math"],
                    "pricing": {"model": "included"},
                },
                "data_processor": {
                    "id": "data_processor",
                    "name": "数据处理",
                    "description": "数据清洗转换",
                    "tags": ["processing", "data"],
                    "pricing": {"model": "included"},
                },
                "chart_generator": {
                    "id": "chart_generator",
                    "name": "图表生成",
                    "description": "生成可视化图表",
                    "tags": ["visualization", "chart"],
                    "pricing": {"model": "included"},
                },
                "report_generator": {
                    "id": "report_generator",
                    "name": "报告生成",
                    "description": "生成分析报告",
                    "tags": ["report", "generation"],
                    "pricing": {"model": "included"},
                },
                "insight_engine": {
                    "id": "insight_engine",
                    "name": "洞察引擎",
                    "description": "生成业务洞察",
                    "tags": ["insight", "ai"],
                    "pricing": {"model": "included"},
                },
            },
            "pricing": self.pricing,
        }

    async def analyze(
        self,
        data_source: str,
        query: str,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        执行数据分析

        Args:
            data_source: 数据源（文件路径或数据库连接）
            query: 分析查询（自然语言）
            context: 上下文信息

        Returns:
            分析结果
        """
        logger.info(f"执行分析：{query}, 数据源：{data_source}")

        # 模拟分析过程
        import time
        start_time = time.time()

        # 模拟处理
        await asyncio.sleep(0.5)

        exec_time = time.time() - start_time
        cost = self._calculate_cost(exec_time)

        response = {
            "success": True,
            "query": query,
            "data_source": data_source,
            "summary": self._generate_summary(query),
            "insights": self._generate_insights(query),
            "recommendations": self._generate_recommendations(query),
            "execution_time_sec": round(exec_time, 2),
            "billing": {
                "amount": cost,
                "currency": "USD",
                "description": f"数据分析 ({exec_time:.1f}秒)",
                "breakdown": {
                    "rate": "$0.10/分钟",
                    "time_charged": f"{exec_time:.1f}秒",
                },
            },
            "metadata": {
                "app_id": self.name,
                "version": self.version,
            },
        }

        return response

    def _calculate_cost(self, exec_time_sec: float) -> float:
        """计算费用"""
        cost = (exec_time_sec / 60) * self.pricing["price_per_minute"]
        return max(cost, self.pricing["minimum_charge"])

    def _generate_summary(self, query: str) -> str:
        """生成摘要（模拟）"""
        return f"已完成分析：{query}。数据加载成功，共处理 10,000 条记录。"

    def _generate_insights(self, query: str) -> list[str]:
        """生成洞察（模拟）"""
        return [
            "Q3 销售额同比增长 28%，主要得益于新产品线表现优异",
            "华东地区贡献了总销售额的 45%，是最主要的收入来源",
            "客户留存率达到 85%，较上季度提升 5 个百分点",
        ]

    def _generate_recommendations(self, query: str) -> list[str]:
        """生成建议（模拟）"""
        return [
            "建议加大华东地区的市场投入，进一步扩大优势",
            "关注华北地区的下滑趋势，及时采取补救措施",
            "新产品线的成功模式可以复制到其他产品线",
        ]

    async def submit_to_intentos(
        self,
        intentos_url: str = "http://localhost:8080",
        api_key: Optional[str] = None
    ) -> dict[str, Any]:
        """提交到 IntentOS"""
        from intentos.agent.submission import IntentOSConnector

        connector = IntentOSConnector(intentos_url, api_key)

        async with connector:
            builder = connector.builder
            pkg = self.build_package()

            builder.create_package(
                name=pkg["name"],
                version=pkg["version"],
                description=pkg["description"],
                author=pkg["author"],
            )

            # 添加意图
            for intent_id, intent in pkg["intents"].items():
                builder.add_intent(
                    intent_id=intent_id,
                    name=intent["name"],
                    description=intent["description"],
                    patterns=intent["patterns"],
                    required_capabilities=intent["required_capabilities"],
                    pricing=intent["pricing"],
                )

            # 注册能力
            for cap_id, cap in pkg["capabilities"].items():
                builder.register_capability(
                    cap_id=cap_id,
                    name=cap["name"],
                    description=cap["description"],
                    tags=cap["tags"],
                    pricing=cap["pricing"],
                )

            # 验证并提交
            errors = builder.validate()
            if errors:
                raise ValueError(f"App 验证失败：{', '.join(errors)}")

            result = await connector.submit(wait_for_approval=False)
            logger.info(f"数据分析助手 App 已提交：{result['app_id']}")

            return result


# 便捷创建函数
def create_data_analyst() -> DataAnalystApp:
    """创建数据分析助手 App"""
    return DataAnalystApp()
