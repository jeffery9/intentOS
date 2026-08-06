# -*- coding: utf-8 -*-
"""
Marketing Pipeline Module
"""
from __future__ import annotations
from .app import MarketingPipelineApp

def create_marketing_pipeline_app() -> MarketingPipelineApp:
    """创建 Marketing App 实例"""
    return MarketingPipelineApp()

__all__ = [
    "MarketingPipelineApp",
    "create_marketing_pipeline_app",
]
