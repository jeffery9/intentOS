# -*- coding: utf-8 -*-
"""
CRM Pipeline Module
"""
from __future__ import annotations

from .app import CRMPipelineApp
from .bridge import CRMBridge


def create_crm_pipeline_app() -> CRMPipelineApp:
    """创建 CRM 运作流水线 App"""
    return CRMPipelineApp()

__all__ = [
    "CRMPipelineApp",
    "create_crm_pipeline_app",
    "CRMBridge",
]
