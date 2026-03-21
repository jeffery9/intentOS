# -*- coding: utf-8 -*-
"""
IntentOS Personalization Module

个性化配置模块，管理用户的个性化偏好和设置。
支持应用级配置、全局配置、配置继承。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class UserAppConfig:
    """用户应用配置"""
    user_id: str                     # 用户 ID
    app_id: str                      # App ID
    config: dict[str, Any]           # 配置内容
    version: str = "1.0"             # 配置版本
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "app_id": self.app_id,
            "config": self.config,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config[key] = value
        self.updated_at = datetime.now()


@dataclass
class UserGlobalConfig:
    """用户全局配置"""
    user_id: str                     # 用户 ID
    config: dict[str, Any]           # 配置内容
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class ConfigSchema:
    """配置 Schema"""
    app_id: str                      # App ID
    schema: dict[str, Any]           # JSON Schema
    defaults: dict[str, Any]         # 默认值
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "app_id": self.app_id,
            "schema": self.schema,
            "defaults": self.defaults,
            "version": self.version,
        }


class PersonalizationManager:
    """
    个性化管理器

    管理用户的个性化配置。
    """

    def __init__(self) -> None:
        # user_id:app_id -> UserAppConfig
        self.app_configs: dict[str, UserAppConfig] = {}
        # user_id -> UserGlobalConfig
        self.global_configs: dict[str, UserGlobalConfig] = {}
        # app_id -> ConfigSchema
        self.config_schemas: dict[str, ConfigSchema] = {}
        logger.info("个性化管理器初始化完成")

    def register_config_schema(
        self,
        app_id: str,
        schema: dict[str, Any],
        defaults: Optional[dict[str, Any]] = None
    ) -> ConfigSchema:
        """注册配置 Schema"""
        config_schema = ConfigSchema(
            app_id=app_id,
            schema=schema,
            defaults=defaults or {},
        )
        self.config_schemas[app_id] = config_schema
        logger.info(f"注册配置 Schema: {app_id}")
        return config_schema

    def get_config_schema(self, app_id: str) -> Optional[ConfigSchema]:
        """获取配置 Schema"""
        return self.config_schemas.get(app_id)

    def set_app_config(
        self,
        user_id: str,
        app_id: str,
        config: dict[str, Any],
        validate: bool = True
    ) -> UserAppConfig:
        """设置应用配置"""
        key = f"{user_id}:{app_id}"

        # 验证配置
        if validate:
            schema = self.get_config_schema(app_id)
            if schema:
                config = self._validate_config(config, schema)

        # 检查是否已存在
        existing = self.app_configs.get(key)
        if existing:
            existing.config.update(config)
            existing.updated_at = datetime.now()
            logger.info(f"更新应用配置：{user_id} -> {app_id}")
            return existing

        # 创建新配置
        app_config = UserAppConfig(
            user_id=user_id,
            app_id=app_id,
            config=config,
        )
        self.app_configs[key] = app_config
        logger.info(f"设置应用配置：{user_id} -> {app_id}")
        return app_config

    def get_app_config(
        self,
        user_id: str,
        app_id: str
    ) -> dict[str, Any]:
        """获取应用配置（合并默认值）"""
        key = f"{user_id}:{app_id}"
        user_config = self.app_configs.get(key)

        # 获取默认配置
        schema = self.get_config_schema(app_id)
        defaults = schema.defaults if schema else {}

        # 合并配置
        merged = {}
        merged.update(defaults)
        if user_config:
            merged.update(user_config.config)

        return merged

    def set_global_config(
        self,
        user_id: str,
        config: dict[str, Any]
    ) -> UserGlobalConfig:
        """设置全局配置"""
        existing = self.global_configs.get(user_id)
        if existing:
            existing.config.update(config)
            existing.updated_at = datetime.now()
            logger.info(f"更新全局配置：{user_id}")
            return existing

        global_config = UserGlobalConfig(
            user_id=user_id,
            config=config,
        )
        self.global_configs[user_id] = global_config
        logger.info(f"设置全局配置：{user_id}")
        return global_config

    def get_global_config(self, user_id: str) -> dict[str, Any]:
        """获取全局配置"""
        global_config = self.global_configs.get(user_id)
        return global_config.config if global_config else {}

    def delete_app_config(self, user_id: str, app_id: str) -> bool:
        """删除应用配置"""
        key = f"{user_id}:{app_id}"
        if key in self.app_configs:
            del self.app_configs[key]
            logger.info(f"删除应用配置：{user_id} -> {app_id}")
            return True
        return False

    def delete_global_config(self, user_id: str) -> bool:
        """删除全局配置"""
        if user_id in self.global_configs:
            del self.global_configs[user_id]
            logger.info(f"删除全局配置：{user_id}")
            return True
        return False

    def list_app_configs(self, user_id: str) -> dict[str, dict[str, Any]]:
        """列出用户的所有应用配置"""
        configs = {}
        prefix = f"{user_id}:"
        for key, config in self.app_configs.items():
            if key.startswith(prefix):
                app_id = key[len(prefix):]
                configs[app_id] = config.to_dict()
        return configs

    def _validate_config(
        self,
        config: dict[str, Any],
        schema: ConfigSchema
    ) -> dict[str, Any]:
        """验证配置"""
        # 简单的类型验证
        validated = {}
        properties = schema.schema.get("properties", {})

        for key, value in config.items():
            if key in properties:
                prop_schema = properties[key]
                expected_type = prop_schema.get("type")

                # 类型检查
                if expected_type:
                    if not self._check_type(value, expected_type):
                        logger.warning(
                            f"配置类型不匹配：{key}, expected={expected_type}, got={type(value)}"
                        )
                        continue

                validated[key] = value
            else:
                # 允许额外配置
                validated[key] = value

        return validated

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查类型"""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected = type_map.get(expected_type)
        if not expected:
            return True

        return isinstance(value, expected)

    def merge_configs(
        self,
        *configs: dict[str, Any]
    ) -> dict[str, Any]:
        """合并多个配置（后覆盖前）"""
        merged = {}
        for config in configs:
            merged.update(config)
        return merged

    def get_effective_config(
        self,
        user_id: str,
        app_id: str,
        app_defaults: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        获取有效配置

        优先级：用户应用配置 > 用户全局配置 > 应用默认配置
        """
        # 1. 应用默认配置
        config = app_defaults or {}

        # 2. 用户全局配置
        global_config = self.get_global_config(user_id)
        if global_config:
            # 可能有 app-specific 的全局配置
            app_global = global_config.get("apps", {}).get(app_id, {})
            config = self.merge_configs(config, app_global)

        # 3. 用户应用配置
        app_config = self.get_app_config(user_id, app_id)
        config = self.merge_configs(config, app_config)

        return config


class PreferenceManager:
    """
    偏好管理器

    管理用户的 UI 偏好、使用习惯等。
    """

    def __init__(self) -> None:
        # user_id -> preferences
        self.preferences: dict[str, dict[str, Any]] = {}
        logger.info("偏好管理器初始化完成")

    def set_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ) -> None:
        """设置偏好"""
        if user_id not in self.preferences:
            self.preferences[user_id] = {}

        self.preferences[user_id][key] = value
        logger.info(f"设置偏好：{user_id}.{key} = {value}")

    def get_preference(
        self,
        user_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """获取偏好"""
        user_prefs = self.preferences.get(user_id, {})
        return user_prefs.get(key, default)

    def delete_preference(self, user_id: str, key: str) -> bool:
        """删除偏好"""
        if user_id in self.preferences:
            if key in self.preferences[user_id]:
                del self.preferences[user_id][key]
                logger.info(f"删除偏好：{user_id}.{key}")
                return True
        return False

    def get_all_preferences(self, user_id: str) -> dict[str, Any]:
        """获取所有偏好"""
        return self.preferences.get(user_id, {})


# 预定义的 UI 偏好

UI_PREFERENCES = {
    "theme": {
        "type": "string",
        "enum": ["light", "dark", "auto"],
        "default": "light",
        "description": "界面主题",
    },
    "language": {
        "type": "string",
        "default": "zh-CN",
        "description": "界面语言",
    },
    "font_size": {
        "type": "integer",
        "default": 14,
        "min": 10,
        "max": 24,
        "description": "字体大小",
    },
    "compact_mode": {
        "type": "boolean",
        "default": False,
        "description": "紧凑模式",
    },
    "show_tips": {
        "type": "boolean",
        "default": True,
        "description": "显示提示",
    },
}


# 全局个性化管理器实例
_global_personalization_manager: Optional[PersonalizationManager] = None
_global_preference_manager: Optional[PreferenceManager] = None


def get_personalization_manager() -> PersonalizationManager:
    """获取全局个性化管理器"""
    global _global_personalization_manager
    if _global_personalization_manager is None:
        _global_personalization_manager = PersonalizationManager()
        # 注册预定义的 UI 配置 Schema
        _global_personalization_manager.register_config_schema(
            "ui",
            schema={
                "type": "object",
                "properties": UI_PREFERENCES,
            },
            defaults={
                k: v["default"] for k, v in UI_PREFERENCES.items()
            }
        )
    return _global_personalization_manager


def get_preference_manager() -> PreferenceManager:
    """获取全局偏好管理器"""
    global _global_preference_manager
    if _global_preference_manager is None:
        _global_preference_manager = PreferenceManager()
    return _global_preference_manager


def reset_personalization_services() -> None:
    """重置个性化服务"""
    global _global_personalization_manager, _global_preference_manager
    _global_personalization_manager = None
    _global_preference_manager = None
