"""
应用层管理器

管理整个应用层的生命周期
"""

from __future__ import annotations

from typing import Any, Optional
from .base import AppBase, AppContext, AppResult
from .registry import AppRegistry
from .template import TemplateRegistry, IntentTemplate
from .router import IntentRouter
from .app_services import AppServices, get_services


class AppLayer:
    """
    应用层
    
    3 层 7 级架构的应用层 (Layer 1)
    """
    
    _instance: Optional["AppLayer"] = None
    
    def __new__(cls) -> "AppLayer":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.app_registry = AppRegistry()
        self.template_registry = TemplateRegistry()
        self.router = IntentRouter()
        self.services = get_services()
        self._initialized = True
    
    # ========== 应用管理 ==========
    
    def register_app(self, app: AppBase) -> bool:
        """注册应用"""
        success = self.app_registry.register_instance(app)
        if success:
            self.services.info(f"应用已注册：{app.APP_ID}")
        return success
    
    def register_app_class(self, app_class: type) -> bool:
        """注册应用类"""
        success = self.app_registry.register_class(app_class)
        if success:
            self.services.info(f"应用类已注册：{app_class.APP_ID}")
        return success
    
    def unregister_app(self, app_id: str) -> bool:
        """注销应用"""
        return self.app_registry.unregister(app_id)
    
    def get_app(self, app_id: str) -> Optional[AppBase]:
        """获取应用"""
        return self.app_registry.get_app(app_id)
    
    def list_apps(self) -> list[dict[str, Any]]:
        """列出应用"""
        return self.app_registry.list_all_apps()
    
    # ========== 模板管理 ==========
    
    def register_template(self, template: IntentTemplate) -> bool:
        """注册意图模板"""
        success = self.template_registry.register(template)
        if success:
            self.router.register_template(template)
            self.services.info(f"模板已注册：{template.id}")
        return success
    
    def list_templates(self) -> list[IntentTemplate]:
        """列出模板"""
        return self.template_registry.list_templates()
    
    # ========== 执行 ==========
    
    async def execute(
        self,
        intent: str,
        context: Optional[AppContext] = None
    ) -> AppResult:
        """执行意图"""
        return await self.router.route(intent, context)
    
    # ========== 状态 ==========
    
    def get_status(self) -> dict[str, Any]:
        """获取状态"""
        return {
            "apps": self.app_registry.get_app_count(),
            "templates": len(self.template_registry.get_all_templates()),
            "categories": self.template_registry.get_categories(),
        }


# ========== 便捷函数 ==========

_layer: Optional[AppLayer] = None


def get_app_layer() -> AppLayer:
    """获取应用层单例"""
    global _layer
    if _layer is None:
        _layer = AppLayer()
    return _layer


def register_app(app: AppBase) -> AppBase:
    """注册应用"""
    layer = get_app_layer()
    layer.register_app(app)
    return app


def register_template(template: IntentTemplate) -> IntentTemplate:
    """注册模板"""
    layer = get_app_layer()
    layer.register_template(template)
    return template


async def execute_intent(intent: str, context: Optional[AppContext] = None) -> AppResult:
    """执行意图"""
    layer = get_app_layer()
    return await layer.execute(intent, context)
