"""
应用注册表

管理应用的注册、发现、生命周期
"""

from __future__ import annotations

from typing import Any, Optional, Type
from .base import AppBase


class AppRegistry:
    """
    应用注册表
    
    单例模式，全局唯一
    """
    
    _instance: Optional["AppRegistry"] = None
    _apps: dict[str, AppBase] = {}
    _app_classes: dict[str, Type[AppBase]] = {}
    
    def __new__(cls) -> "AppRegistry":
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_class(self, app_class: Type[AppBase]) -> bool:
        """
        注册应用类
        
        Args:
            app_class: 应用类
        
        Returns:
            是否成功
        """
        app_id = app_class.APP_ID
        
        if app_id in self._app_classes:
            return False
        
        self._app_classes[app_id] = app_class
        return True
    
    def register_instance(self, app: AppBase) -> bool:
        """
        注册应用实例
        
        Args:
            app: 应用实例
        
        Returns:
            是否成功
        """
        app_id = app.APP_ID
        
        if app_id in self._apps:
            return False
        
        self._apps[app_id] = app
        return True
    
    def unregister(self, app_id: str) -> bool:
        """注销应用"""
        if app_id in self._apps:
            del self._apps[app_id]
            return True
        return False
    
    def get_app(self, app_id: str) -> Optional[AppBase]:
        """获取应用实例"""
        if app_id in self._apps:
            return self._apps[app_id]
        
        # 如果实例不存在，尝试创建
        if app_id in self._app_classes:
            app_class = self._app_classes[app_id]
            app = app_class()
            self._apps[app_id] = app
            return app
        
        return None
    
    def list_apps(self, category: Optional[str] = None) -> list[AppBase]:
        """列出应用"""
        apps = list(self._apps.values())
        
        if category:
            apps = [a for a in apps if a.APP_CATEGORY == category]
        
        return [a for a in apps if hasattr(a, '_initialized') and a._initialized]
    
    def list_all_apps(self) -> list[dict[str, Any]]:
        """列出所有应用信息"""
        result = []
        
        # 已实例化的应用
        for app in self._apps.values():
            result.append(app.get_info())
        
        # 未实例化的类
        for app_class in self._app_classes.values():
            if app_class.APP_ID not in self._apps:
                result.append({
                    "id": app_class.APP_ID,
                    "name": app_class.APP_NAME,
                    "description": app_class.APP_DESCRIPTION,
                    "version": app_class.APP_VERSION,
                    "category": app_class.APP_CATEGORY,
                    "icon": app_class.APP_ICON,
                    "author": app_class.APP_AUTHOR,
                    "status": "not_initialized",
                })
        
        return result
    
    def search_apps(self, query: str) -> list[dict[str, Any]]:
        """搜索应用"""
        query_lower = query.lower()
        
        result = []
        for app_info in self.list_all_apps():
            if (query_lower in app_info["name"].lower() or
                query_lower in app_info["description"].lower() or
                query_lower in app_info["category"].lower()):
                result.append(app_info)
        
        return result
    
    def get_app_count(self) -> int:
        """获取应用数量"""
        return len(self._apps) + len(self._app_classes)
    
    def clear(self) -> None:
        """清空注册表"""
        # 关闭所有应用
        for app in self._apps.values():
            if hasattr(app, 'shutdown'):
                app.shutdown()
        
        self._apps.clear()
        self._app_classes.clear()


# ========== 便捷函数 ==========

def register_app(app_class: Type[AppBase]) -> Type[AppBase]:
    """
    注册应用装饰器
    
    用法:
        @register_app
        class MyApp(AppBase):
            ...
    """
    registry = AppRegistry()
    registry.register_class(app_class)
    return app_class


def get_app(app_id: str) -> Optional[AppBase]:
    """获取应用实例"""
    registry = AppRegistry()
    return registry.get_app(app_id)


def list_apps(category: Optional[str] = None) -> list[AppBase]:
    """列出应用"""
    registry = AppRegistry()
    return registry.list_apps(category)
