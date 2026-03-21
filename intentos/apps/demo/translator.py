# -*- coding: utf-8 -*-
"""
Translator Demo App

多语言翻译服务 - 支持 100+ 语言互译。
计费模式：按字数 $0.01/100 字
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

logger: logging.Logger = logging.getLogger(__name__)


class TranslatorApp:
    """
    多语言翻译服务 App

    功能：
    - 100+ 语言互译
    - 文档翻译
    - 实时翻译
    - 专业术语管理
    - 上下文感知翻译

    计费：$0.01/100 字
    """

    def __init__(self) -> None:
        self.name: str = "translator"
        self.version: str = "1.0.0"
        self.description: str = "多语言翻译服务"
        self.icon: str = "🌐"
        self.pricing: dict[str, Any] = {
            "model": "pay_per_word",
            "price_per_100_words": 0.01,  # $0.01/100 字
            "minimum_charge": 0.01,
        }
        self.supported_languages: list[dict[str, str]] = [
            {"code": "zh", "name": "中文"},
            {"code": "en", "name": "英语"},
            {"code": "ja", "name": "日语"},
            {"code": "ko", "name": "韩语"},
            {"code": "fr", "name": "法语"},
            {"code": "de", "name": "德语"},
            {"code": "es", "name": "西班牙语"},
            {"code": "pt", "name": "葡萄牙语"},
            {"code": "ru", "name": "俄语"},
            {"code": "ar", "name": "阿拉伯语"},
        ]
        logger.info(f"多语言翻译服务 App 初始化：{self.name}")

    def build_package(self) -> dict[str, Any]:
        """构建意图包"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": "IntentOS Team",
            "icon": self.icon,
            "intents": {
                "text_translation": {
                    "id": "text_translation",
                    "name": "文本翻译",
                    "description": "翻译文本内容",
                    "patterns": [
                        ".*翻译.*",
                        ".*translate.*",
                        ".*翻译成.*",
                        ".*用.*语怎么说.*",
                    ],
                    "required_capabilities": ["language_detector", "translator"],
                    "pricing": self.pricing,
                },
                "document_translation": {
                    "id": "document_translation",
                    "name": "文档翻译",
                    "description": "翻译整个文档",
                    "patterns": [
                        ".*翻译文档.*",
                        ".*翻译文件.*",
                        ".*translate.*document.*",
                    ],
                    "required_capabilities": ["file_reader", "document_translator"],
                    "pricing": {"model": "pay_per_word", "price_per_100_words": 0.02},
                },
                "realtime_translation": {
                    "id": "realtime_translation",
                    "name": "实时翻译",
                    "description": "实时对话翻译",
                    "patterns": [
                        ".*实时翻译.*",
                        ".*对话翻译.*",
                        ".*同声传译.*",
                    ],
                    "required_capabilities": ["streaming_translator"],
                    "pricing": {"model": "pay_per_minute", "price_per_minute": 0.10},
                },
                "terminology_lookup": {
                    "id": "terminology_lookup",
                    "name": "术语查询",
                    "description": "查询专业术语翻译",
                    "patterns": [
                        ".*术语.*",
                        ".*专业词汇.*",
                        ".*terminology.*",
                    ],
                    "required_capabilities": ["terminology_database"],
                    "pricing": {"model": "free"},  # 术语查询免费
                },
            },
            "capabilities": {
                "language_detector": {
                    "id": "language_detector",
                    "name": "语言检测",
                    "description": "自动检测输入语言",
                    "tags": ["detection", "language"],
                    "pricing": {"model": "free"},
                },
                "translator": {
                    "id": "translator",
                    "name": "翻译引擎",
                    "description": "神经机器翻译",
                    "tags": ["translation", "nlp"],
                    "pricing": {"model": "included"},
                },
                "file_reader": {
                    "id": "file_reader",
                    "name": "文件读取",
                    "description": "读取文档文件",
                    "tags": ["io", "file"],
                    "pricing": {"model": "free"},
                },
                "document_translator": {
                    "id": "document_translator",
                    "name": "文档翻译",
                    "description": "保持格式翻译文档",
                    "tags": ["translation", "document"],
                    "pricing": {"model": "included"},
                },
                "streaming_translator": {
                    "id": "streaming_translator",
                    "name": "流式翻译",
                    "description": "实时流式翻译",
                    "tags": ["translation", "streaming"],
                    "pricing": {"model": "included"},
                },
                "terminology_database": {
                    "id": "terminology_database",
                    "name": "术语库",
                    "description": "专业术语翻译库",
                    "tags": ["terminology", "database"],
                    "pricing": {"model": "free"},
                },
            },
            "pricing": self.pricing,
            "supported_languages": self.supported_languages,
        }

    async def translate(
        self,
        text: str,
        source_language: Optional[str] = None,
        target_language: str = "en",
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        翻译文本

        Args:
            text: 待翻译文本
            source_language: 源语言（可选，自动检测）
            target_language: 目标语言
            context: 上下文信息

        Returns:
            翻译结果和计费信息
        """
        logger.info(f"翻译：{len(text)} 字符，{source_language or 'auto'} -> {target_language}")

        # 检测源语言
        if not source_language or source_language == "auto":
            source_language = self._detect_language(text)

        # 计算字数
        word_count = self._count_words(text, source_language)
        cost = self._calculate_cost(word_count)

        # 模拟翻译
        translated_text = self._generate_translation(text, source_language, target_language)

        response = {
            "success": True,
            "original": {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "language": source_language,
                "word_count": word_count,
            },
            "translated": {
                "text": translated_text,
                "language": target_language,
            },
            "billing": {
                "amount": cost,
                "currency": "USD",
                "description": f"翻译 ({word_count}字)",
                "breakdown": {
                    "rate": "$0.01/100 字",
                    "words_charged": word_count,
                },
            },
            "metadata": {
                "app_id": self.name,
                "version": self.version,
            },
        }

        return response

    def _detect_language(self, text: str) -> str:
        """检测语言（模拟）"""
        # 简单启发式检测
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars > len(text) * 0.3:
            return "zh"
        return "en"  # 默认英语

    def _count_words(self, text: str, language: str) -> int:
        """计算字数"""
        if language == "zh":
            # 中文按字符数
            return len(text)
        else:
            # 英文按单词数
            return len(text.split())

    def _calculate_cost(self, word_count: int) -> float:
        """计算费用"""
        cost = (word_count / 100) * self.pricing["price_per_100_words"]
        return max(cost, self.pricing["minimum_charge"])

    def _generate_translation(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> str:
        """生成翻译（模拟）"""
        # 模拟翻译结果
        if source_language == "zh" and target_language == "en":
            return f"[English Translation] {text[:50]}..."
        elif source_language == "en" and target_language == "zh":
            return f"[中文翻译] {text[:50]}..."
        else:
            return f"[{target_language} Translation] {text[:50]}..."

    async def translate_document(
        self,
        document_path: str,
        source_language: Optional[str] = None,
        target_language: str = "en",
        preserve_format: bool = True,
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        翻译文档

        Args:
            document_path: 文档路径
            source_language: 源语言
            target_language: 目标语言
            preserve_format: 是否保持格式
            context: 上下文信息

        Returns:
            翻译结果
        """
        logger.info(f"翻译文档：{document_path}, {target_language}")

        # 模拟文档翻译
        import time
        start_time = time.time()

        # 模拟处理
        await asyncio.sleep(0.5)

        # 模拟文档信息
        page_count = 5
        word_count = 2500
        cost = self._calculate_cost(word_count) * 2  # 文档翻译更贵

        response = {
            "success": True,
            "document_path": document_path,
            "output_path": f"{document_path}.{target_language}",
            "document_info": {
                "page_count": page_count,
                "word_count": word_count,
                "format_preserved": preserve_format,
            },
            "translation": {
                "source_language": source_language or "auto",
                "target_language": target_language,
            },
            "billing": {
                "amount": cost,
                "currency": "USD",
                "description": f"文档翻译 ({word_count}字，{page_count}页)",
                "breakdown": {
                    "rate": "$0.02/100 字（文档）",
                    "words_charged": word_count,
                },
            },
            "metadata": {
                "app_id": self.name,
                "version": self.version,
            },
        }

        return response

    async def batch_translate(
        self,
        texts: list[str],
        source_language: Optional[str] = None,
        target_language: str = "en",
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        批量翻译

        Args:
            texts: 待翻译文本列表
            source_language: 源语言
            target_language: 目标语言
            context: 上下文信息

        Returns:
            翻译结果和总费用
        """
        logger.info(f"批量翻译：{len(texts)} 条文本")

        results = []
        total_cost = 0.0
        total_words = 0

        for text in texts:
            result = await self.translate(text, source_language, target_language)
            results.append(result["translated"]["text"])
            total_cost += result["billing"]["amount"]
            total_words += result["original"]["word_count"]

        response = {
            "success": True,
            "translations": results,
            "summary": {
                "text_count": len(texts),
                "total_words": total_words,
                "total_cost": total_cost,
            },
            "billing": {
                "amount": total_cost,
                "currency": "USD",
                "description": f"批量翻译 ({len(texts)}条，{total_words}字)",
            },
            "metadata": {
                "app_id": self.name,
                "version": self.version,
            },
        }

        return response

    def get_supported_languages(self) -> list[dict[str, str]]:
        """获取支持的语言列表"""
        return self.supported_languages

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
            logger.info(f"多语言翻译服务 App 已提交：{result['app_id']}")

            return result


# 便捷创建函数
def create_translator() -> TranslatorApp:
    """创建多语言翻译服务 App"""
    return TranslatorApp()
