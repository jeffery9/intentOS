# -*- coding: utf-8 -*-
"""
Meta-Capabilities for the Genesis App

These are the "tools" that the app-building app uses to construct other apps.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from .marketplace import get_marketplace
from .app_generator import AppConversationStudio # Temporarily used for session management

logger = logging.getLogger(__name__)

# --- Meta-Capability Handlers ---

async def create_app_spec(session_id: str, name: str, description: str) -> dict:
    """元能力：创建一个新的 App 规格草稿"""
    # In a real implementation, this would interact with a more robust
    # session manager, but for now we re-use the studio's session store.
    studio = AppConversationStudio(get_marketplace(), None) # Simplified
    if session_id not in studio.sessions:
        return {"success": False, "error": "Dev Session not found"}
    
    spec = {
        "name": name,
        "description": description,
        "intents": [],
        "logic": [],
        "permissions": []
    }
    studio.sessions[session_id].current_spec = spec
    return {"success": True, "spec": spec}

async def add_intent_template(session_id: str, intent_name: str, description: str) -> dict:
    """元能力：为当前 App 草稿增加一个意图模板"""
    studio = AppConversationStudio(get_marketplace(), None)
    if session_id not in studio.sessions:
        return {"success": False, "error": "Dev Session not found"}
    
    spec = studio.sessions[session_id].current_spec
    if "intents" not in spec:
        spec["intents"] = []
    
    spec["intents"].append({"name": intent_name, "description": description})
    return {"success": True, "spec": spec}

async def set_permission(session_id: str, permission: str) -> dict:
    """元能力：为当前 App 草稿声明所需权限"""
    studio = AppConversationStudio(get_marketplace(), None)
    if session_id not in studio.sessions:
        return {"success": False, "error": "Dev Session not found"}
        
    spec = studio.sessions[session_id].current_spec
    if "permissions" not in spec:
        spec["permissions"] = []
        
    if permission not in spec["permissions"]:
        spec["permissions"].append(permission)
    return {"success": True, "spec": spec}

async def publish_to_marketplace(session_id: str) -> dict:
    """元能力：将当前 App 草稿发布到市场"""
    studio = AppConversationStudio(get_marketplace(), None)
    if session_id not in studio.sessions:
        return {"success": False, "error": "Dev Session not found"}
        
    result = await studio.finalize_and_publish(session_id)
    return result

def register_meta_capabilities(registry: Any):
    """将所有元能力注册到内核"""
    registry.register(
        id="meta:create_spec", name="创建应用规格",
        description="创建一个新的 AI Native App 的基础规格文件",
        handler=create_app_spec
    )
    registry.register(
        id="meta:add_intent", name="添加意图模板",
        description="为一个 App 规格草稿添加新的用户意图模板",
        handler=add_intent_template
    )
    registry.register(
        id="meta:set_permission", name="设置所需权限",
        description="为一个 App 规格草稿声明一个所需的物理权限",
        handler=set_permission
    )
    registry.register(
        id="meta:publish", name="发布到市场",
        description="将一个完整的 App 规格草稿发布到应用市场",
        handler=publish_to_marketplace
    )
    logger.info("✅ Meta-Capabilities for Genesis App registered.")

