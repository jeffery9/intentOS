# -*- coding: utf-8 -*-
"""
IntentOS Application Marketplace Module

应用市场模块，负责管理 AI Native App 的发布、发现、交易和收益分成。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


logger: logging.Logger = logging.getLogger(__name__)


class AppStatus(Enum):
    """应用状态"""
    DRAFT = "draft"              # 草稿
    PENDING_REVIEW = "pending_review"  # 待审核
    APPROVED = "approved"        # 已批准
    PUBLISHED = "published"      # 已发布
    SUSPENDED = "suspended"      # 已暂停
    REJECTED = "rejected"        # 已拒绝
    DEPRECATED = "deprecated"    # 已弃用


class AppCategory(Enum):
    """应用分类"""
    PRODUCTIVITY = "productivity"    # 生产力
    ANALYTICS = "analytics"          # 数据分析
    CUSTOMER_SERVICE = "customer_service"  # 客服
    DEVELOPMENT = "development"      # 开发工具
    LANGUAGE = "language"            # 语言翻译
    MARKETING = "marketing"          # 营销
    EDUCATION = "education"          # 教育
    ENTERTAINMENT = "entertainment"  # 娱乐
    FINANCE = "finance"              # 金融
    HEALTH = "health"                # 健康
    OTHER = "other"                  # 其他


@dataclass
class AppVersion:
    """应用版本"""
    version: str
    release_date: datetime = field(default_factory=datetime.now)
    changelog: Optional[str] = None
    manifest_hash: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "release_date": self.release_date.isoformat(),
            "changelog": self.changelog,
            "manifest_hash": self.manifest_hash,
        }


@dataclass
class AppMetadata:
    """应用元数据"""
    app_id: str
    name: str
    description: str
    category: AppCategory
    developer_id: str
    developer_name: str
    icon: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    pricing_model: str = "pay_per_use"  # pay_per_use, subscription, tiered
    pricing_config: dict[str, Any] = field(default_factory=dict)
    revenue_share: dict[str, float] = field(default_factory=lambda: {
        "developer": 0.80,  # 开发者 80%
        "platform": 0.15,   # 平台 15%
        "referrer": 0.05,   # 推荐者 5%
    })
    status: AppStatus = AppStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    versions: list[AppVersion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "app_id": self.app_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "developer_id": self.developer_id,
            "developer_name": self.developer_name,
            "icon": self.icon,
            "tags": self.tags,
            "pricing_model": self.pricing_model,
            "pricing_config": self.pricing_config,
            "revenue_share": self.revenue_share,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "versions": [v.to_dict() for v in self.versions],
        }


@dataclass
class AppReview:
    """应用评价"""
    id: str
    app_id: str
    user_id: str
    rating: int  # 1-5
    comment: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "app_id": self.app_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AppUsage:
    """应用用量统计"""
    app_id: str
    period: str  # YYYY-MM
    total_requests: int = 0
    total_revenue: float = 0.0
    developer_earnings: float = 0.0
    platform_fees: float = 0.0
    active_users: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "app_id": self.app_id,
            "period": self.period,
            "total_requests": self.total_requests,
            "total_revenue": round(self.total_revenue, 2),
            "developer_earnings": round(self.developer_earnings, 2),
            "platform_fees": round(self.platform_fees, 2),
            "active_users": self.active_users,
        }


class AppMarketplace:
    """
    应用市场

    管理 AI Native App 的发布、发现、交易和收益分成。
    """

    def __init__(self) -> None:
        self.apps: dict[str, AppMetadata] = {}
        self.reviews: dict[str, list[AppReview]] = {}  # app_id -> reviews
        self.usage_stats: dict[str, dict[str, AppUsage]] = {}  # app_id -> period -> stats
        self.installs: dict[str, set[str]] = {}  # app_id -> user_ids
        logger.info("应用市场初始化完成")

    def _generate_id(self, prefix: str) -> str:
        """生成 ID"""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    async def submit_app(
        self,
        name: str,
        description: str,
        category: AppCategory,
        developer_id: str,
        developer_name: str,
        manifest: dict[str, Any],
        tags: Optional[list[str]] = None
    ) -> AppMetadata:
        """提交应用"""
        app_id = f"app_{name.lower().replace(' ', '_')}_{developer_id}"

        # 检查是否已存在
        if app_id in self.apps:
            raise ValueError(f"应用已存在：{app_id}")

        app = AppMetadata(
            app_id=app_id,
            name=name,
            description=description,
            category=category,
            developer_id=developer_id,
            developer_name=developer_name,
            tags=tags or [],
            pricing_model=manifest.get("pricing", {}).get("model", "pay_per_use"),
            pricing_config=manifest.get("pricing", {}),
            revenue_share=manifest.get("revenue_share", {
                "developer": 0.80,
                "platform": 0.15,
                "referrer": 0.05,
            }),
            status=AppStatus.PENDING_REVIEW,
        )

        # 添加初始版本
        app.versions.append(AppVersion(
            version="1.0.0",
            manifest_hash=self._compute_manifest_hash(manifest),
        ))

        self.apps[app_id] = app
        self.installs[app_id] = set()
        logger.info(f"应用已提交：{app_id}, developer={developer_name}")

        return app

    async def review_app(
        self,
        app_id: str,
        approved: bool,
        reviewer_id: str,
        comments: Optional[str] = None
    ) -> bool:
        """审核应用"""
        if app_id not in self.apps:
            return False

        app = self.apps[app_id]
        if app.status != AppStatus.PENDING_REVIEW:
            raise ValueError(f"应用状态不允许审核：{app.status.value}")

        if approved:
            app.status = AppStatus.APPROVED
            logger.info(f"应用已批准：{app_id}, reviewer={reviewer_id}")
        else:
            app.status = AppStatus.REJECTED
            app.metadata = {"rejection_reason": comments or "未通过审核"}
            logger.warning(f"应用已拒绝：{app_id}, reason={comments}")

        app.updated_at = datetime.now()
        return True

    async def publish_app(self, app_id: str) -> bool:
        """发布应用"""
        if app_id not in self.apps:
            return False

        app = self.apps[app_id]
        if app.status != AppStatus.APPROVED:
            raise ValueError(f"应用未批准，无法发布：{app.status.value}")

        app.status = AppStatus.PUBLISHED
        app.updated_at = datetime.now()
        logger.info(f"应用已发布：{app_id}")

        return True

    async def install_app(self, app_id: str, user_id: str) -> bool:
        """安装/订阅应用"""
        if app_id not in self.apps:
            return False

        app = self.apps[app_id]
        if app.status != AppStatus.PUBLISHED:
            raise ValueError(f"应用未发布，无法安装：{app.status.value}")

        if app_id not in self.installs:
            self.installs[app_id] = set()

        self.installs[app_id].add(user_id)
        logger.info(f"应用已安装：{app_id}, user={user_id}")

        return True

    async def uninstall_app(self, app_id: str, user_id: str) -> bool:
        """卸载应用"""
        if app_id not in self.installs:
            return False

        if user_id in self.installs[app_id]:
            self.installs[app_id].remove(user_id)
            logger.info(f"应用已卸载：{app_id}, user={user_id}")
            return True

        return False

    async def add_review(
        self,
        app_id: str,
        user_id: str,
        rating: int,
        comment: Optional[str] = None
    ) -> AppReview:
        """添加评价"""
        if app_id not in self.apps:
            raise ValueError(f"应用不存在：{app_id}")

        if rating < 1 or rating > 5:
            raise ValueError(f"评分必须在 1-5 之间：{rating}")

        review = AppReview(
            id=self._generate_id("review"),
            app_id=app_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )

        if app_id not in self.reviews:
            self.reviews[app_id] = []
        self.reviews[app_id].append(review)

        logger.info(f"评价已添加：app={app_id}, user={user_id}, rating={rating}")

        return review

    def get_app(self, app_id: str) -> Optional[AppMetadata]:
        """获取应用详情"""
        return self.apps.get(app_id)

    def list_apps(
        self,
        category: Optional[AppCategory] = None,
        status: Optional[AppStatus] = None,
        search: Optional[str] = None,
        limit: int = 50
    ) -> list[AppMetadata]:
        """列出应用"""
        apps = list(self.apps.values())

        # 过滤
        if category:
            apps = [a for a in apps if a.category == category]
        if status:
            apps = [a for a in apps if a.status == status]
        if search:
            search_lower = search.lower()
            apps = [
                a for a in apps
                if search_lower in a.name.lower() or
                   search_lower in a.description.lower() or
                   any(search_lower in tag.lower() for tag in a.tags)
            ]

        # 只显示已发布的应用（除非指定状态）
        if not status:
            apps = [a for a in apps if a.status == AppStatus.PUBLISHED]

        # 按创建时间倒序
        apps.sort(key=lambda a: a.created_at, reverse=True)

        return apps[:limit]

    def get_app_reviews(self, app_id: str, limit: int = 20) -> list[AppReview]:
        """获取应用评价"""
        if app_id not in self.reviews:
            return []

        reviews = self.reviews[app_id]
        reviews.sort(key=lambda r: r.created_at, reverse=True)
        return reviews[:limit]

    def get_app_rating(self, app_id: str) -> dict[str, Any]:
        """获取应用评分"""
        if app_id not in self.reviews:
            return {"average": 0.0, "count": 0}

        reviews = self.reviews[app_id]
        if not reviews:
            return {"average": 0.0, "count": 0}

        average = sum(r.rating for r in reviews) / len(reviews)
        return {
            "average": round(average, 2),
            "count": len(reviews),
            "distribution": {
                str(i): sum(1 for r in reviews if r.rating == i)
                for i in range(1, 6)
            },
        }

    def get_install_count(self, app_id: str) -> int:
        """获取安装数"""
        if app_id not in self.installs:
            return 0
        return len(self.installs[app_id])

    def record_usage(
        self,
        app_id: str,
        period: str,
        requests: int,
        revenue: float
    ) -> None:
        """记录应用用量"""
        if app_id not in self.apps:
            return

        app = self.apps[app_id]

        if app_id not in self.usage_stats:
            self.usage_stats[app_id] = {}

        if period not in self.usage_stats[app_id]:
            self.usage_stats[app_id][period] = AppUsage(
                app_id=app_id,
                period=period,
            )

        stats = self.usage_stats[app_id][period]
        stats.total_requests += requests
        stats.total_revenue += revenue

        # 计算分成
        developer_share = app.revenue_share.get("developer", 0.80)
        platform_share = app.revenue_share.get("platform", 0.15)

        stats.developer_earnings = stats.total_revenue * developer_share
        stats.platform_fees = stats.total_revenue * platform_share

        logger.debug(f"记录用量：app={app_id}, period={period}, requests={requests}, revenue=${revenue}")

    def get_developer_earnings(
        self,
        developer_id: str,
        period: Optional[str] = None
    ) -> dict[str, Any]:
        """获取开发者收益"""
        apps = [a for a in self.apps.values() if a.developer_id == developer_id]
        app_ids = {a.app_id for a in apps}

        total_earnings = 0.0
        earnings_by_app: dict[str, float] = {}

        for app_id in app_ids:
            if app_id in self.usage_stats:
                for period_key, stats in self.usage_stats[app_id].items():
                    if period is None or period_key == period:
                        total_earnings += stats.developer_earnings
                        if app_id not in earnings_by_app:
                            earnings_by_app[app_id] = 0.0
                        earnings_by_app[app_id] += stats.developer_earnings

        return {
            "developer_id": developer_id,
            "period": period or "all",
            "total_earnings": round(total_earnings, 2),
            "earnings_by_app": {
                app_id: round(amount, 2)
                for app_id, amount in earnings_by_app.items()
            },
            "app_count": len(apps),
        }

    def _compute_manifest_hash(self, manifest: dict[str, Any]) -> str:
        """计算 manifest 哈希"""
        import hashlib
        import json
        content = json.dumps(manifest, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_marketplace_stats(self) -> dict[str, Any]:
        """获取市场统计"""
        published_apps = [a for a in self.apps.values() if a.status == AppStatus.PUBLISHED]
        total_installs = sum(len(users) for users in self.installs.values())
        total_revenue = sum(
            stats.total_revenue
            for app_stats in self.usage_stats.values()
            for stats in app_stats.values()
        )

        return {
            "total_apps": len(published_apps),
            "total_installs": total_installs,
            "total_revenue": round(total_revenue, 2),
            "categories": {
                cat.value: len([a for a in published_apps if a.category == cat])
                for cat in AppCategory
            },
        }


# 全局应用市场实例
_global_marketplace: Optional[AppMarketplace] = None


def get_marketplace() -> AppMarketplace:
    """获取全局应用市场"""
    global _global_marketplace
    if _global_marketplace is None:
        _global_marketplace = AppMarketplace()
    return _global_marketplace


def reset_marketplace() -> None:
    """重置应用市场"""
    global _global_marketplace
    _global_marketplace = None
