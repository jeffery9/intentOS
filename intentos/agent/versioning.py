# -*- coding: utf-8 -*-
"""
IntentOS App Versioning Module

App 版本管理模块，支持多版本共存、灰度发布、用户版本偏好。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


logger: logging.Logger = logging.getLogger(__name__)


class VersionStatus(Enum):
    """版本状态"""
    DRAFT = "draft"                  # 草稿
    BETA = "beta"                    # 测试版
    STABLE = "stable"                # 稳定版
    DEPRECATED = "deprecated"        # 已弃用
    ARCHIVED = "archived"            # 已归档


class ReleaseChannel(Enum):
    """发布渠道"""
    NIGHTLY = "nightly"              # 每夜构建
    BETA = "beta"                    # 测试渠道
    STABLE = "stable"                # 稳定渠道
    LTS = "lts"                      # 长期支持


@dataclass
class VersionInfo:
    """版本信息"""
    app_id: str                      # App ID
    version: str                     # 版本号 (语义化版本)
    status: VersionStatus            # 版本状态
    channel: ReleaseChannel          # 发布渠道
    manifest_hash: str               # manifest 哈希
    created_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    changelog: Optional[str] = None  # 变更日志
    breaking_changes: list[str] = field(default_factory=list)  # 破坏性变更
    migration_guide: Optional[str] = None  # 迁移指南
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "app_id": self.app_id,
            "version": self.version,
            "status": self.status.value,
            "channel": self.channel.value,
            "manifest_hash": self.manifest_hash,
            "created_at": self.created_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "changelog": self.changelog,
            "breaking_changes": self.breaking_changes,
            "migration_guide": self.migration_guide,
            "metadata": self.metadata,
        }


@dataclass
class UserVersionPreference:
    """用户版本偏好"""
    user_id: str                     # 用户 ID
    app_id: str                      # App ID
    version: str                     # 偏好的版本
    channel: ReleaseChannel = ReleaseChannel.STABLE  # 发布渠道
    auto_update: bool = False        # 是否自动更新
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "app_id": self.app_id,
            "version": self.version,
            "channel": self.channel.value,
            "auto_update": self.auto_update,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class RolloutConfig:
    """灰度发布配置"""
    app_id: str                      # App ID
    version: str                     # 目标版本
    percentage: float = 0.0          # 灰度百分比 (0-100)
    target_users: Optional[list[str]] = None  # 目标用户列表（可选）
    exclude_users: Optional[list[str]] = None  # 排除用户列表（可选）
    start_time: Optional[datetime] = None  # 开始时间
    end_time: Optional[datetime] = None    # 结束时间
    success_metrics: dict[str, Any] = field(default_factory=dict)  # 成功指标
    rollback_threshold: float = 0.05  # 回滚阈值（错误率）
    status: str = "pending"          # pending/active/paused/completed/rolled_back

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "app_id": self.app_id,
            "version": self.version,
            "percentage": self.percentage,
            "target_users": self.target_users,
            "exclude_users": self.exclude_users,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "success_metrics": self.success_metrics,
            "rollback_threshold": self.rollback_threshold,
            "status": self.status,
        }


class VersionManager:
    """
    版本管理器

    管理 App 版本的注册、查询、灰度发布。
    """

    def __init__(self) -> None:
        # app_id -> version -> VersionInfo
        self.versions: dict[str, dict[str, VersionInfo]] = {}
        # app_id -> VersionInfo (最新版)
        self.latest_versions: dict[str, VersionInfo] = {}
        # app_id -> VersionInfo (最新稳定版)
        self.stable_versions: dict[str, VersionInfo] = {}
        # user_id:app_id -> UserVersionPreference
        self.user_preferences: dict[str, UserVersionPreference] = {}
        # app_id -> RolloutConfig
        self.rollout_configs: dict[str, RolloutConfig] = {}
        logger.info("版本管理器初始化完成")

    def register_version(
        self,
        app_id: str,
        version: str,
        manifest: dict[str, Any],
        status: VersionStatus = VersionStatus.DRAFT,
        channel: ReleaseChannel = ReleaseChannel.NIGHTLY,
        changelog: Optional[str] = None
    ) -> VersionInfo:
        """注册版本"""
        import hashlib

        # 计算 manifest 哈希
        manifest_hash = hashlib.sha256(
            str(manifest).encode()
        ).hexdigest()[:16]

        # 检查版本是否已存在
        if app_id in self.versions and version in self.versions[app_id]:
            existing = self.versions[app_id][version]
            if existing.manifest_hash != manifest_hash:
                raise ValueError(f"版本已存在且 manifest 不同：{app_id} v{version}")
            return existing

        # 创建版本信息
        version_info = VersionInfo(
            app_id=app_id,
            version=version,
            status=status,
            channel=channel,
            manifest_hash=manifest_hash,
            changelog=changelog,
        )

        # 注册版本
        if app_id not in self.versions:
            self.versions[app_id] = {}
        self.versions[app_id][version] = version_info

        # 更新最新版
        if self._is_newer(version, self.latest_versions.get(app_id)):
            self.latest_versions[app_id] = version_info

        # 更新最新稳定版
        if status == VersionStatus.STABLE:
            if self._is_newer(version, self.stable_versions.get(app_id)):
                self.stable_versions[app_id] = version_info

        logger.info(f"注册版本：{app_id} v{version}")

        return version_info

    def publish_version(
        self,
        app_id: str,
        version: str,
        status: VersionStatus = VersionStatus.STABLE,
        channel: ReleaseChannel = ReleaseChannel.STABLE
    ) -> bool:
        """发布版本"""
        version_info = self.get_version(app_id, version)
        if not version_info:
            return False

        version_info.status = status
        version_info.channel = channel
        version_info.published_at = datetime.now()

        # 更新最新版
        if self._is_newer(version, self.latest_versions.get(app_id)):
            self.latest_versions[app_id] = version_info

        # 更新最新稳定版
        if status == VersionStatus.STABLE:
            if self._is_newer(version, self.stable_versions.get(app_id)):
                self.stable_versions[app_id] = version_info

        logger.info(f"发布版本：{app_id} v{version} -> {status.value}/{channel.value}")

        return True

    def deprecate_version(self, app_id: str, version: str) -> bool:
        """弃用版本"""
        version_info = self.get_version(app_id, version)
        if not version_info:
            return False

        version_info.status = VersionStatus.DEPRECATED
        version_info.deprecated_at = datetime.now()

        logger.info(f"弃用版本：{app_id} v{version}")

        return True

    def get_version(
        self,
        app_id: str,
        version: str
    ) -> Optional[VersionInfo]:
        """获取版本信息"""
        if app_id not in self.versions:
            return None
        return self.versions[app_id].get(version)

    def get_latest_version(self, app_id: str) -> Optional[VersionInfo]:
        """获取最新版"""
        return self.latest_versions.get(app_id)

    def get_stable_version(self, app_id: str) -> Optional[VersionInfo]:
        """获取最新稳定版"""
        return self.stable_versions.get(app_id)

    def list_versions(
        self,
        app_id: str,
        status: Optional[VersionStatus] = None,
        channel: Optional[ReleaseChannel] = None
    ) -> list[VersionInfo]:
        """列出版本"""
        if app_id not in self.versions:
            return []

        versions = list(self.versions[app_id].values())

        if status:
            versions = [v for v in versions if v.status == status]
        if channel:
            versions = [v for v in versions if v.channel == channel]

        # 按版本号排序（从新到旧）
        versions.sort(key=lambda v: v.created_at, reverse=True)

        return versions

    def set_user_version(
        self,
        user_id: str,
        app_id: str,
        version: str,
        channel: ReleaseChannel = ReleaseChannel.STABLE,
        auto_update: bool = False
    ) -> UserVersionPreference:
        """设置用户版本偏好"""
        key = f"{user_id}:{app_id}"

        # 检查版本是否存在
        if not self.get_version(app_id, version):
            raise ValueError(f"版本不存在：{app_id} v{version}")

        preference = UserVersionPreference(
            user_id=user_id,
            app_id=app_id,
            version=version,
            channel=channel,
            auto_update=auto_update,
        )

        self.user_preferences[key] = preference
        logger.info(f"设置用户版本偏好：{user_id} -> {app_id} v{version}")

        return preference

    def get_user_version(
        self,
        user_id: str,
        app_id: str
    ) -> str:
        """获取用户版本偏好"""
        key = f"{user_id}:{app_id}"
        preference = self.user_preferences.get(key)

        if preference:
            return preference.version

        # 没有偏好时返回最新稳定版
        stable = self.get_stable_version(app_id)
        if stable:
            return stable.version

        # 否则返回最新版
        latest = self.get_latest_version(app_id)
        if latest:
            return latest.version

        raise ValueError(f"App 没有可用版本：{app_id}")

    def create_rollout(
        self,
        app_id: str,
        version: str,
        percentage: float = 0.0,
        target_users: Optional[list[str]] = None
    ) -> RolloutConfig:
        """创建灰度发布"""
        # 检查版本是否存在
        if not self.get_version(app_id, version):
            raise ValueError(f"版本不存在：{app_id} v{version}")

        rollout = RolloutConfig(
            app_id=app_id,
            version=version,
            percentage=percentage,
            target_users=target_users,
        )

        self.rollout_configs[app_id] = rollout
        logger.info(f"创建灰度发布：{app_id} v{version} -> {percentage}%")

        return rollout

    def update_rollout(
        self,
        app_id: str,
        percentage: float,
        status: Optional[str] = None
    ) -> bool:
        """更新灰度发布"""
        rollout = self.rollout_configs.get(app_id)
        if not rollout:
            return False

        rollout.percentage = percentage
        if status:
            rollout.status = status

        logger.info(f"更新灰度发布：{app_id} -> {percentage}%")

        return True

    def get_rollout_for_user(
        self,
        user_id: str,
        app_id: str
    ) -> Optional[str]:
        """获取用户所在的灰度版本"""
        rollout = self.rollout_configs.get(app_id)
        if not rollout:
            return None

        # 检查是否在目标用户列表
        if rollout.target_users:
            if user_id in rollout.target_users:
                return rollout.version
            return None

        # 检查是否在排除列表
        if rollout.exclude_users:
            if user_id in rollout.exclude_users:
                return None

        # 基于用户 ID 哈希计算是否在灰度范围内
        import hashlib
        hash_value = int(
            hashlib.md5(f"{user_id}:{app_id}".encode()).hexdigest(),
            16
        ) % 100

        if hash_value < rollout.percentage:
            return rollout.version

        return None

    def _is_newer(
        self,
        version: str,
        existing: Optional[VersionInfo]
    ) -> bool:
        """检查版本是否更新"""
        if not existing:
            return True

        # 简单的语义化版本比较
        try:
            new_parts = [int(x) for x in version.split(".")]
            old_parts = [int(x) for x in existing.version.split(".")]

            return new_parts > old_parts
        except (ValueError, AttributeError):
            # 如果不是语义化版本，按创建时间比较
            return True


# 全局版本管理器实例
_global_version_manager: Optional[VersionManager] = None


def get_version_manager() -> VersionManager:
    """获取全局版本管理器"""
    global _global_version_manager
    if _global_version_manager is None:
        _global_version_manager = VersionManager()
    return _global_version_manager


def reset_version_manager() -> None:
    """重置版本管理器"""
    global _global_version_manager
    _global_version_manager = None
