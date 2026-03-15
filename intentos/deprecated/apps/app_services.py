"""
应用服务

为应用提供通用服务：日志、配置、存储等
"""

from __future__ import annotations

import logging
from typing import Any, Optional


class AppServices:
    """
    应用服务
    
    为应用提供通用服务
    """
    
    def __init__(self):
        self._config: dict[str, dict[str, Any]] = {}
        self._storage: dict[str, dict[str, Any]] = {}
        self._logger = logging.getLogger("intentos.apps")
    
    # ========== 日志服务 ==========
    
    def log(self, level: str, message: str) -> None:
        """记录日志"""
        log_method = getattr(self._logger, level, self._logger.info)
        log_method(message)
    
    def debug(self, message: str) -> None:
        """调试日志"""
        self.log("debug", message)
    
    def info(self, message: str) -> None:
        """信息日志"""
        self.log("info", message)
    
    def warning(self, message: str) -> None:
        """警告日志"""
        self.log("warning", message)
    
    def error(self, message: str) -> None:
        """错误日志"""
        self.log("error", message)
    
    # ========== 配置服务 ==========
    
    async def get_config(self, app_id: str, key: str, default: Any = None) -> Any:
        """获取配置"""
        if app_id in self._config and key in self._config[app_id]:
            return self._config[app_id][key]
        return default
    
    async def set_config(self, app_id: str, key: str, value: Any) -> None:
        """设置配置"""
        if app_id not in self._config:
            self._config[app_id] = {}
        self._config[app_id][key] = value
    
    async def delete_config(self, app_id: str, key: str) -> bool:
        """删除配置"""
        if app_id in self._config and key in self._config[app_id]:
            del self._config[app_id][key]
            return True
        return False
    
    # ========== 存储服务 ==========
    
    async def get_storage(self, app_id: str, key: str, default: Any = None) -> Any:
        """获取存储"""
        if app_id in self._storage and key in self._storage[app_id]:
            return self._storage[app_id][key]
        return default
    
    async def set_storage(self, app_id: str, key: str, value: Any) -> None:
        """设置存储"""
        if app_id not in self._storage:
            self._storage[app_id] = {}
        self._storage[app_id][key] = value
    
    async def delete_storage(self, app_id: str, key: str) -> bool:
        """删除存储"""
        if app_id in self._storage and key in self._storage[app_id]:
            del self._storage[app_id][key]
            return True
        return False
    
    async def list_storage(self, app_id: str) -> dict[str, Any]:
        """列出存储"""
        return self._storage.get(app_id, {})
    
    # ========== LLM 服务 ==========
    
    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """调用 LLM"""
        # 实际实现会调用 LLM 后端
        # 这里返回占位符
        return f"[LLM Response for: {prompt[:50]}...]"
    
    # ========== 工具调用服务 ==========
    
    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """调用工具"""
        # 实际实现会调用工具注册表
        raise NotImplementedError("Tool calling not implemented")


# ========== 单例 ==========

_services: Optional[AppServices] = None


def get_services() -> AppServices:
    """获取应用服务单例"""
    global _services
    if _services is None:
        _services = AppServices()
    return _services
