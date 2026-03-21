# -*- coding: utf-8 -*-
"""
Document Summarizer Demo App

文档总结服务 - 自动总结长文档、论文、报告等。
计费模式：按文档页数 $0.05/页
"""

from __future__ import annotations

import logging
from typing import Any, Optional


logger: logging.Logger = logging.getLogger(__name__)


class DocSummarizerApp:
    """
    文档总结服务 App

    功能：
    - 文档解析（PDF/Word/TXT/Markdown）
    - 提取式摘要
    - 生成式摘要
    - 关键点提取
    - 多语言支持

    计费：$0.05/页
    """

    def __init__(self) -> None:
        self.name: str = "doc_summarizer"
        self.version: str = "1.0.0"
        self.description: str = "文档总结服务"
        self.icon: str = "📝"
        self.pricing: dict[str, Any] = {
            "model": "pay_per_page",
            "price_per_page": 0.05,  # $0.05/页
            "minimum_charge": 0.05,
        }
        logger.info(f"文档总结服务 App 初始化：{self.name}")

    def build_package(self) -> dict[str, Any]:
        """构建意图包"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": "IntentOS Team",
            "icon": self.icon,
            "intents": {
                "document_parse": {
                    "id": "document_parse",
                    "name": "文档解析",
                    "description": "解析各种格式文档",
                    "patterns": [
                        ".*解析.*文档.*",
                        ".*读取.*PDF.*",
                        ".*打开.*文件.*",
                        ".*parse.*document.*",
                    ],
                    "required_capabilities": ["file_reader", "pdf_parser", "docx_parser"],
                    "pricing": {"model": "free"},  # 解析免费
                },
                "extractive_summary": {
                    "id": "extractive_summary",
                    "name": "提取式摘要",
                    "description": "抽取原文关键句子",
                    "patterns": [
                        ".*提取.*摘要.*",
                        ".*关键句.*",
                        ".*原文摘要.*",
                    ],
                    "required_capabilities": ["sentence_extractor", "importance_scorer"],
                    "pricing": self.pricing,
                },
                "abstractive_summary": {
                    "id": "abstractive_summary",
                    "name": "生成式摘要",
                    "description": "生成新的摘要文本",
                    "patterns": [
                        ".*总结.*",
                        ".*摘要.*",
                        ".*概括.*",
                        ".*summarize.*",
                    ],
                    "required_capabilities": ["text_generator", "comprehension_engine"],
                    "pricing": self.pricing,
                },
                "key_points": {
                    "id": "key_points",
                    "name": "关键点提取",
                    "description": "提取文档关键点",
                    "patterns": [
                        ".*关键点.*",
                        ".*要点.*",
                        ".*重点.*",
                        ".*key.*points.*",
                    ],
                    "required_capabilities": ["key_phrase_extractor", "topic_modeling"],
                    "pricing": self.pricing,
                },
                "multi_language": {
                    "id": "multi_language",
                    "name": "多语言总结",
                    "description": "跨语言文档总结",
                    "patterns": [
                        ".*翻译.*总结.*",
                        ".*英文.*摘要.*",
                        ".*中文.*总结.*",
                    ],
                    "required_capabilities": ["language_detector", "translator", "summarizer"],
                    "pricing": {"model": "pay_per_page", "price_per_page": 0.08},  # 多语言更贵
                },
            },
            "capabilities": {
                "file_reader": {
                    "id": "file_reader",
                    "name": "文件读取",
                    "description": "读取各种格式文件",
                    "tags": ["io", "file"],
                    "pricing": {"model": "free"},
                },
                "pdf_parser": {
                    "id": "pdf_parser",
                    "name": "PDF 解析",
                    "description": "解析 PDF 文档",
                    "tags": ["parser", "pdf"],
                    "pricing": {"model": "free"},
                },
                "docx_parser": {
                    "id": "docx_parser",
                    "name": "Word 解析",
                    "description": "解析 Word 文档",
                    "tags": ["parser", "docx"],
                    "pricing": {"model": "free"},
                },
                "sentence_extractor": {
                    "id": "sentence_extractor",
                    "name": "句子抽取",
                    "description": "抽取关键句子",
                    "tags": ["extraction", "nlp"],
                    "pricing": {"model": "included"},
                },
                "importance_scorer": {
                    "id": "importance_scorer",
                    "name": "重要性评分",
                    "description": "评估句子重要性",
                    "tags": ["scoring", "ml"],
                    "pricing": {"model": "included"},
                },
                "text_generator": {
                    "id": "text_generator",
                    "name": "文本生成",
                    "description": "生成摘要文本",
                    "tags": ["generation", "llm"],
                    "pricing": {"model": "included"},
                },
                "comprehension_engine": {
                    "id": "comprehension_engine",
                    "name": "理解引擎",
                    "description": "理解文档内容",
                    "tags": ["comprehension", "ai"],
                    "pricing": {"model": "included"},
                },
                "key_phrase_extractor": {
                    "id": "key_phrase_extractor",
                    "name": "关键短语抽取",
                    "description": "抽取关键短语",
                    "tags": ["extraction", "nlp"],
                    "pricing": {"model": "included"},
                },
                "topic_modeling": {
                    "id": "topic_modeling",
                    "name": "主题建模",
                    "description": "识别文档主题",
                    "tags": ["topic", "ml"],
                    "pricing": {"model": "included"},
                },
                "language_detector": {
                    "id": "language_detector",
                    "name": "语言检测",
                    "description": "检测文档语言",
                    "tags": ["detection", "language"],
                    "pricing": {"model": "free"},
                },
                "translator": {
                    "id": "translator",
                    "name": "翻译引擎",
                    "description": "多语言翻译",
                    "tags": ["translation", "language"],
                    "pricing": {"model": "included"},
                },
                "summarizer": {
                    "id": "summarizer",
                    "name": "总结引擎",
                    "description": "生成文档总结",
                    "tags": ["summarization", "nlp"],
                    "pricing": {"model": "included"},
                },
            },
            "pricing": self.pricing,
        }

    async def summarize(
        self,
        document_path: str,
        summary_type: str = "abstractive",
        max_length: int = 500,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        总结文档

        Args:
            document_path: 文档路径
            summary_type: 摘要类型 (extractive/abstractive)
            max_length: 最大长度（字）
            context: 上下文信息

        Returns:
            总结结果和计费信息
        """
        logger.info(f"总结文档：{document_path}, 类型：{summary_type}")

        # 模拟文档解析
        import time
        start_time = time.time()

        # 模拟处理
        await asyncio.sleep(0.5)

        # 模拟文档信息
        page_count = 10
        word_count = 5000

        cost = self._calculate_cost(page_count)

        response = {
            "success": True,
            "document_path": document_path,
            "document_info": {
                "page_count": page_count,
                "word_count": word_count,
                "language": "zh-CN",
            },
            "summary_type": summary_type,
            "summary": self._generate_summary(summary_type, max_length),
            "key_points": self._extract_key_points(),
            "billing": {
                "amount": cost,
                "currency": "USD",
                "description": f"文档总结 ({page_count}页)",
                "breakdown": {
                    "rate": "$0.05/页",
                    "pages_charged": page_count,
                },
            },
            "metadata": {
                "app_id": self.name,
                "version": self.version,
            },
        }

        return response

    def _calculate_cost(self, page_count: int) -> float:
        """计算费用"""
        cost = page_count * self.pricing["price_per_page"]
        return max(cost, self.pricing["minimum_charge"])

    def _generate_summary(self, summary_type: str, max_length: int) -> str:
        """生成摘要（模拟）"""
        if summary_type == "extractive":
            return """【提取式摘要】

本文档主要讨论了 IntentOS AI 原生操作系统的架构设计和实现方案。

核心观点：
1. IntentOS 采用语义虚拟机架构，将 LLM 作为处理器
2. 支持 Self-Bootstrap 机制，系统可以自我演进
3. 采用分布式设计，支持多节点集群
4. 提供 Shell 和 REST API 两种交互方式

关键数据：
- 核心代码约 12,000 行
- 测试覆盖率 99%+
- 支持 4 种 LLM 后端"""

        else:  # abstractive
            return """【生成式摘要】

IntentOS 是一个创新的 AI 原生操作系统，其核心理念是将自然语言作为"机器码"，LLM 作为处理器执行语义指令。

系统采用三层架构：应用层负责用户交互，意图层处理语义编译和执行规划，模型层调用 LLM 完成实际执行。这种设计使得应用可以通过定义意图而非编写代码来构建。

关键技术特性包括 Self-Bootstrap（系统自举）、分布式语义存储、以及多级缓存优化。系统支持多种 LLM 后端，包括 OpenAI、Anthropic 和本地 Ollama。

商业价值方面，IntentOS 提供了完整的 PaaS 平台，支持开发者发布应用、按使用计费、并通过数字钱包完成支付。"""

    def _extract_key_points(self) -> list[str]:
        """提取关键点（模拟）"""
        return [
            "语义 VM 是 IntentOS 的核心架构",
            "LLM 作为处理器执行语义指令",
            "支持 Self-Bootstrap 自我演进",
            "分布式设计支持多节点集群",
            "提供 PaaS 平台供开发者发布应用",
            "按量计费模式，支持多种支付方式",
        ]

    async def summarize_text(
        self,
        text: str,
        max_length: int = 200,
        language: str = "zh",
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        总结文本

        Args:
            text: 待总结的文本
            max_length: 最大长度
            language: 语言
            context: 上下文信息

        Returns:
            总结结果
        """
        logger.info(f"总结文本：{len(text)} 字符")

        # 估算页数（每页约 500 字）
        page_count = max(1, len(text) // 500)
        cost = self._calculate_cost(page_count)

        response = {
            "success": True,
            "input_length": len(text),
            "summary": self._generate_summary("abstractive", max_length),
            "key_points": self._extract_key_points(),
            "billing": {
                "amount": cost,
                "currency": "USD",
                "description": f"文本总结 (约{page_count}页)",
            },
            "metadata": {
                "app_id": self.name,
                "version": self.version,
            },
        }

        return response

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

            errors = builder.validate()
            if errors:
                raise ValueError(f"App 验证失败：{', '.join(errors)}")

            result = await connector.submit(wait_for_approval=False)
            logger.info(f"文档总结服务 App 已提交：{result['app_id']}")

            return result


# 需要导入 asyncio
import asyncio


# 便捷创建函数
def create_doc_summarizer() -> DocSummarizerApp:
    """创建文档总结服务 App"""
    return DocSummarizerApp()
