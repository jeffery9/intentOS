"""
应用基类

定义应用开发的标准接口
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime


@dataclass
class AppContext:
    """应用上下文"""
    
    # 用户信息
    user_id: str = "anonymous"
    user_role: str = "user"
    permissions: list[str] = field(default_factory=list)
    
    # 会话信息
    session_id: str = ""
    conversation_history: list[dict] = field(default_factory=list)
    
    # 运行时信息
    app_id: str = ""
    request_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 自定义数据
    data: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "user_role": self.user_role,
            "session_id": self.session_id,
            "app_id": self.app_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }


@dataclass
class AppResult:
    """应用执行结果"""
    
    success: bool
    message: str
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # 可选的后续操作建议
    next_actions: list[str] = field(default_factory=list)
    
    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "next_actions": self.next_actions,
            "metadata": self.metadata,
        }


class AppBase(ABC):
    """
    应用基类
    
    所有应用必须继承此类并实现抽象方法
    """
    
    # ========== 应用元数据 (子类覆盖) ==========
    
    #: 应用 ID (唯一标识)
    APP_ID: str = "unknown"
    
    #: 应用名称
    APP_NAME: str = "Unknown App"
    
    #: 应用描述
    APP_DESCRIPTION: str = ""
    
    #: 应用版本
    APP_VERSION: str = "1.0.0"
    
    #: 应用分类
    APP_CATEGORY: str = "general"
    
    #: 应用图标
    APP_ICON: str = "📱"
    
    #: 作者信息
    APP_AUTHOR: str = ""
    
    # ========== 生命周期方法 (可选覆盖) ==========
    
    def __init__(self):
        """初始化应用"""
        self._initialized = False
        self._services: Optional[Any] = None
    
    async def initialize(self, services: Any = None) -> bool:
        """
        初始化应用
        
        Args:
            services: 应用服务
        
        Returns:
            是否成功
        """
        self._services = services
        self._initialized = True
        return True
    
    async def shutdown(self) -> None:
        """关闭应用"""
        self._initialized = False
    
    # ========== 抽象方法 (必须实现) ==========
    
    @abstractmethod
    async def execute(self, intent: str, context: AppContext) -> AppResult:
        """
        执行应用
        
        Args:
            intent: 用户意图
            context: 应用上下文
        
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """
        获取能力列表
        
        Returns:
            能力描述列表
        """
        pass
    
    # ========== 辅助方法 ==========
    
    def get_info(self) -> dict[str, Any]:
        """获取应用信息"""
        return {
            "id": self.APP_ID,
            "name": self.APP_NAME,
            "description": self.APP_DESCRIPTION,
            "version": self.APP_VERSION,
            "category": self.APP_CATEGORY,
            "icon": self.APP_ICON,
            "author": self.APP_AUTHOR,
        }
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    def log(self, level: str, message: str) -> None:
        """
        记录日志
        
        Args:
            level: 日志级别 (debug/info/warning/error)
            message: 日志内容
        """
        if self._services and hasattr(self._services, 'log'):
            self._services.log(level, f"[{self.APP_ID}] {message}")
    
    async def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        if self._services and hasattr(self._services, 'get_config'):
            return await self._services.get_config(self.APP_ID, key, default)
        return default
    
    async def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        if self._services and hasattr(self._services, 'set_config'):
            await self._services.set_config(self.APP_ID, key, value)
    
    async def get_storage(self, key: str, default: Any = None) -> Any:
        """获取存储"""
        if self._services and hasattr(self._services, 'get_storage'):
            return await self._services.get_storage(self.APP_ID, key, default)
        return default
    
    async def set_storage(self, key: str, value: Any) -> None:
        """设置存储"""
        if self._services and hasattr(self._services, 'set_storage'):
            await self._services.set_storage(self.APP_ID, key, value)


# ========== 装饰器 ==========

def app_metadata(
    app_id: str,
    name: str,
    description: str,
    version: str = "1.0.0",
    category: str = "general",
    icon: str = "📱",
    author: str = ""
):
    """
    应用元数据装饰器
    
    用法:
        @app_metadata(
            app_id="my_app",
            name="我的应用",
            description="应用描述"
        )
        class MyApp(AppBase):
            ...
    """
    def decorator(cls: type) -> type:
        cls.APP_ID = app_id
        cls.APP_NAME = name
        cls.APP_DESCRIPTION = description
        cls.APP_VERSION = version
        cls.APP_CATEGORY = category
        cls.APP_ICON = icon
        cls.APP_AUTHOR = author
        return cls
    return decorator
