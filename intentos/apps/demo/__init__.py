# -*- coding: utf-8 -*-
"""
IntentOS Demo Apps

示范 AI Native App，展示如何在 IntentOS 上开发和部署应用。
"""

from .customer_service_bot import CustomerServiceBotApp
from .data_analyst import DataAnalystApp
from .code_generator import CodeGeneratorApp
from .doc_summarizer import DocSummarizerApp
from .translator import TranslatorApp

__all__ = [
    "CustomerServiceBotApp",
    "DataAnalystApp",
    "CodeGeneratorApp",
    "DocSummarizerApp",
    "TranslatorApp",
]
