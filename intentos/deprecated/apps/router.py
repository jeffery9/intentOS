"""
意图路由器

将用户意图路由到对应的应用
"""

from __future__ import annotations

from typing import Any, Optional
from .base import AppContext, AppResult
from .template import IntentTemplate, TemplateRegistry
from .registry import AppRegistry


class IntentRouter:
    """
    意图路由器
    
    负责将用户输入路由到合适的应用处理
    """
    
    def __init__(self):
        self.template_registry = TemplateRegistry()
        self.app_registry = AppRegistry()
        
        # 路由缓存
        self._route_cache: dict[str, str] = {}  # intent_hash -> app_id
    
    def register_template(self, template: IntentTemplate) -> None:
        """注册意图模板"""
        self.template_registry.register(template)
    
    def match_app(self, intent: str) -> Optional[tuple[str, IntentTemplate]]:
        """
        匹配应用
        
        Args:
            intent: 用户意图
        
        Returns:
            (app_id, template) 或 None
        """
        # 1. 匹配模板
        template = self.template_registry.match_intent(intent)
        
        if not template:
            return None
        
        # 2. 获取处理应用
        if template.handler:
            # 直接绑定了处理函数
            app_id = self._find_app_by_handler(template.handler)
        elif template.handler_name:
            # 通过名称查找
            app_id = self._find_app_by_name(template.handler_name)
        else:
            # 默认按分类路由
            app_id = self._route_by_category(template.category)
        
        if app_id:
            return (app_id, template)
        
        return None
    
    async def route(
        self,
        intent: str,
        context: Optional[AppContext] = None
    ) -> AppResult:
        """
        路由并执行
        
        Args:
            intent: 用户意图
            context: 应用上下文
        
        Returns:
            执行结果
        """
        if context is None:
            context = AppContext()
        
        # 1. 匹配应用
        match = self.match_app(intent)
        
        if not match:
            return AppResult(
                success=False,
                message="抱歉，我还没学会这个技能",
                error="no_matching_app",
                next_actions=self._get_suggestions(),
            )
        
        app_id, template = match
        
        # 2. 获取应用
        app = self.app_registry.get_app(app_id)
        
        if not app:
            return AppResult(
                success=False,
                message=f"应用 {app_id} 未找到",
                error="app_not_found",
            )
        
        # 3. 执行应用
        context.app_id = app_id
        result = await app.execute(intent, context)
        
        return result
    
    def _find_app_by_handler(self, handler) -> Optional[str]:
        """通过处理函数查找应用"""
        for app in self.app_registry.list_apps():
            for attr_name in dir(app):
                attr = getattr(app, attr_name)
                if attr == handler:
                    return app.APP_ID
        return None
    
    def _find_app_by_name(self, handler_name: str) -> Optional[str]:
        """通过处理函数名称查找应用"""
        for app in self.app_registry.list_apps():
            if hasattr(app, handler_name):
                return app.APP_ID
        return None
    
    def _route_by_category(self, category: str) -> Optional[str]:
        """按分类路由"""
        apps = self.app_registry.list_apps(category)
        if apps:
            return apps[0].APP_ID
        return None
    
    def _get_suggestions(self) -> list[str]:
        """获取建议"""
        return [
            "试试说：安排明天下午 3 点的会议",
            "试试说：分析上个月的销售数据",
            "试试说：写一篇关于 AI 的文章",
        ]
