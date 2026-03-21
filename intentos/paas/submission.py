# -*- coding: utf-8 -*-
"""
IntentOS App Submission Module

本地 App 提交模块，实现 Mainframe 模式：
- 用户在本地开发 App（定义意图、注册能力）
- 连接到 IntentOS 时提交资源/能力
- IntentOS 使用语义 VM 机制执行
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional


logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class IntentPackage:
    """
    意图包

    包含意图定义、能力描述、计费规则等。
    这是 AI Native App 的基本单位。
    """
    name: str
    version: str
    description: str
    author: str
    intents: dict[str, Any] = field(default_factory=dict)  # intent_id -> intent_def
    capabilities: dict[str, Any] = field(default_factory=dict)  # cap_id -> cap_def
    pricing: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    manifest_hash: Optional[str] = None

    def compute_hash(self) -> str:
        """计算 manifest 哈希"""
        content = json.dumps({
            "name": self.name,
            "version": self.version,
            "intents": self.intents,
            "capabilities": self.capabilities,
            "pricing": self.pricing,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "intents": self.intents,
            "capabilities": self.capabilities,
            "pricing": self.pricing,
            "resources": self.resources,
            "manifest_hash": self.manifest_hash or self.compute_hash(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IntentPackage:
        """从字典创建"""
        pkg = cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            intents=data.get("intents", {}),
            capabilities=data.get("capabilities", {}),
            pricing=data.get("pricing", {}),
            resources=data.get("resources", {}),
        )
        pkg.manifest_hash = data.get("manifest_hash")
        return pkg


@dataclass
class CapabilityRegistration:
    """能力注册信息"""
    id: str
    name: str
    description: str
    handler: Optional[Callable] = None  # 本地处理函数（可选）
    tags: list[str] = field(default_factory=list)
    source: str = "local"  # local, mcp, skill
    pricing: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class LocalAppBuilder:
    """
    本地 App 构建器

    用于在本地开发、测试意图包，然后提交到 IntentOS。
    """

    def __init__(self, workspace: Optional[str] = None) -> None:
        self.workspace: Path = Path(workspace) if workspace else Path.cwd()
        self.package: Optional[IntentPackage] = None
        self.capabilities: dict[str, CapabilityRegistration] = {}
        logger.info(f"本地 App 构建器初始化：workspace={self.workspace}")

    def create_package(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        author: str = ""
    ) -> IntentPackage:
        """创建意图包"""
        self.package = IntentPackage(
            name=name,
            version=version,
            description=description,
            author=author,
        )
        logger.info(f"创建意图包：{name} v{version}")
        return self.package

    def add_intent(
        self,
        intent_id: str,
        name: str,
        description: str,
        patterns: list[str],
        required_capabilities: list[str],
        pricing: Optional[dict[str, Any]] = None
    ) -> IntentPackage:
        """添加意图"""
        if not self.package:
            raise RuntimeError("请先创建意图包")

        self.package.intents[intent_id] = {
            "id": intent_id,
            "name": name,
            "description": description,
            "patterns": patterns,
            "required_capabilities": required_capabilities,
            "pricing": pricing or {"model": "pay_per_use"},
        }
        logger.info(f"添加意图：{intent_id} - {name}")
        return self.package

    def register_capability(
        self,
        cap_id: str,
        name: str,
        description: str,
        handler: Optional[Callable] = None,
        tags: Optional[list[str]] = None,
        source: str = "local",
        pricing: Optional[dict[str, Any]] = None
    ) -> IntentPackage:
        """注册能力"""
        if not self.package:
            raise RuntimeError("请先创建意图包")

        cap = CapabilityRegistration(
            id=cap_id,
            name=name,
            description=description,
            handler=handler,
            tags=tags or [],
            source=source,
            pricing=pricing or {},
        )
        self.capabilities[cap_id] = cap

        self.package.capabilities[cap_id] = {
            "id": cap_id,
            "name": name,
            "description": description,
            "tags": cap.tags,
            "source": source,
            "pricing": cap.pricing,
        }
        logger.info(f"注册能力：{cap_id} - {name}")
        return self.package

    def set_pricing(
        self,
        model: str = "pay_per_use",
        **kwargs: Any
    ) -> IntentPackage:
        """设置计费规则"""
        if not self.package:
            raise RuntimeError("请先创建意图包")

        self.package.pricing = {
            "model": model,
            **kwargs,
        }
        logger.info(f"设置计费规则：{model}")
        return self.package

    def save(self, path: Optional[str] = None) -> Path:
        """保存意图包到本地"""
        if not self.package:
            raise RuntimeError("请先创建意图包")

        save_path = Path(path) if path else self.workspace / f"{self.package.name}.intent.json"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # 计算哈希
        self.package.manifest_hash = self.package.compute_hash()

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.package.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"意图包已保存：{save_path}")
        return save_path

    def load(self, path: str) -> IntentPackage:
        """从本地加载意图包"""
        load_path = Path(path)
        if not load_path.exists():
            raise FileNotFoundError(f"意图包不存在：{load_path}")

        with open(load_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.package = IntentPackage.from_dict(data)
        logger.info(f"意图包已加载：{load_path}")
        return self.package

    def validate(self) -> list[str]:
        """验证意图包"""
        if not self.package:
            return ["意图包未创建"]

        errors: list[str] = []

        # 检查必填字段
        if not self.package.name:
            errors.append("缺少 name")
        if not self.package.version:
            errors.append("缺少 version")

        # 检查意图
        for intent_id, intent in self.package.intents.items():
            if "name" not in intent:
                errors.append(f"意图 {intent_id} 缺少 name")
            if "patterns" not in intent:
                errors.append(f"意图 {intent_id} 缺少 patterns")

        # 检查能力
        for cap_id, cap in self.package.capabilities.items():
            if "name" not in cap:
                errors.append(f"能力 {cap_id} 缺少 name")
            if "description" not in cap:
                errors.append(f"能力 {cap_id} 缺少 description")

        # 检查计费
        if self.package.pricing and "model" not in self.package.pricing:
            errors.append("计费规则缺少 model")

        if errors:
            logger.warning(f"意图包验证失败：{len(errors)} 个错误")
        else:
            logger.info(f"意图包验证通过：{self.package.name}")

        return errors


class AppSubmissionClient:
    """
    App 提交客户端

    负责将本地意图包提交到 IntentOS。
    这是 Mainframe 模式的核心：用户本地开发，提交到中心执行。
    """

    def __init__(
        self,
        intentos_url: str = "http://localhost:8080",
        api_key: Optional[str] = None
    ) -> None:
        self.intentos_url = intentos_url
        self.api_key = api_key
        self.connected: bool = False
        self.session_id: Optional[str] = None
        logger.info(f"App 提交客户端初始化：url={intentos_url}")

    async def connect(self) -> bool:
        """连接到 IntentOS"""
        logger.info(f"连接到 IntentOS: {self.intentos_url}")

        # 实际实现会通过 HTTP 连接到 IntentOS API
        # 这里模拟连接过程
        self.connected = True
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        logger.info(f"IntentOS 连接成功：session={self.session_id}")
        return True

    async def disconnect(self) -> None:
        """断开连接"""
        if self.connected:
            logger.info(f"断开 IntentOS 连接：session={self.session_id}")
            self.connected = False
            self.session_id = None

    async def submit_package(
        self,
        package: IntentPackage,
        wait_for_approval: bool = False
    ) -> dict[str, Any]:
        """
        提交意图包到 IntentOS

        流程：
        1. 上传 manifest
        2. 注册能力
        3. 注册意图
        4. 等待审核（可选）
        5. 发布
        """
        if not self.connected:
            raise RuntimeError("未连接到 IntentOS，请先调用 connect()")

        logger.info(f"提交意图包：{package.name} v{package.version}")

        # 1. 验证意图包
        builder = LocalAppBuilder()
        builder.package = package
        errors = builder.validate()
        if errors:
            raise ValueError(f"意图包验证失败：{', '.join(errors)}")

        # 2. 计算哈希
        manifest_hash = package.compute_hash()

        # 3. 模拟上传（实际实现会调用 HTTP API）
        submission_result = {
            "status": "submitted",
            "app_id": f"app_{package.name}_{package.author}",
            "package": package.to_dict(),
            "manifest_hash": manifest_hash,
            "submitted_at": datetime.now().isoformat(),
            "session_id": self.session_id,
        }

        logger.info(f"意图包已提交：{package.name}, app_id={submission_result['app_id']}")

        # 4. 等待审核（可选）
        if wait_for_approval:
            logger.info("等待审核...")
            submission_result["status"] = "pending_review"

        return submission_result

    async def register_capability(
        self,
        app_id: str,
        capability: CapabilityRegistration
    ) -> bool:
        """注册能力到 IntentOS"""
        if not self.connected:
            raise RuntimeError("未连接到 IntentOS")

        logger.info(f"注册能力：{capability.id} -> IntentOS")

        # 实际实现会通过 HTTP API 注册
        # 这里模拟注册过程

        return True

    async def execute_intent(
        self,
        app_id: str,
        intent_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        在 IntentOS 中执行意图

        这是 Mainframe 模式的核心：
        - 用户在本地调用
        - IntentOS 在云端执行语义 VM
        """
        if not self.connected:
            raise RuntimeError("未连接到 IntentOS")

        logger.info(f"执行意图：{app_id}/{intent_id}")

        # 实际实现会调用 IntentOS 的执行 API
        # 这里模拟执行过程

        result = {
            "success": True,
            "intent_id": intent_id,
            "app_id": app_id,
            "result": {"message": f"意图 {intent_id} 执行成功"},
            "usage": {
                "cpu_time_ms": 150,
                "tokens_used": 250,
                "execution_time_sec": 1.2,
            },
            "billing": {
                "amount": 0.05,
                "currency": "USD",
            },
        }

        logger.info(f"意图执行完成：{intent_id}, cost=${result['billing']['amount']}")

        return result

    async def get_app_status(self, app_id: str) -> dict[str, Any]:
        """获取应用状态"""
        if not self.connected:
            raise RuntimeError("未连接到 IntentOS")

        # 实际实现会调用 HTTP API
        return {
            "app_id": app_id,
            "status": "published",
            "version": "1.0.0",
            "installed_users": 125,
            "total_revenue": 45.67,
        }

    async def get_usage_stats(self, app_id: str, period: str) -> dict[str, Any]:
        """获取用量统计"""
        if not self.connected:
            raise RuntimeError("未连接到 IntentOS")

        # 实际实现会调用 HTTP API
        return {
            "app_id": app_id,
            "period": period,
            "total_requests": 1500,
            "total_revenue": 75.00,
            "developer_earnings": 60.00,  # 80% 分成
        }


class IntentOSConnector:
    """
    IntentOS 连接器（高级 API）

    简化本地 App 与 IntentOS 的连接和提交流程。
    """

    def __init__(
        self,
        intentos_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        workspace: Optional[str] = None
    ) -> None:
        self.client = AppSubmissionClient(intentos_url, api_key)
        self.builder = LocalAppBuilder(workspace)
        self.current_app_id: Optional[str] = None
        logger.info("IntentOS 连接器初始化完成")

    async def connect(self) -> bool:
        """连接到 IntentOS"""
        return await self.client.connect()

    async def disconnect(self) -> None:
        """断开连接"""
        await self.client.disconnect()

    def create_app(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        author: str = ""
    ) -> LocalAppBuilder:
        """创建 App"""
        return self.builder.create_package(name, version, description, author)

    def add_intent(
        self,
        intent_id: str,
        name: str,
        description: str,
        patterns: list[str],
        required_capabilities: list[str],
        pricing: Optional[dict[str, Any]] = None
    ) -> LocalAppBuilder:
        """添加意图"""
        return self.builder.add_intent(
            intent_id, name, description, patterns,
            required_capabilities, pricing
        )

    def register_capability(
        self,
        cap_id: str,
        name: str,
        description: str,
        handler: Optional[Callable] = None,
        tags: Optional[list[str]] = None,
        pricing: Optional[dict[str, Any]] = None
    ) -> LocalAppBuilder:
        """注册能力"""
        return self.builder.register_capability(
            cap_id, name, description, handler, tags, "local", pricing
        )

    async def submit(self, wait_for_approval: bool = False) -> dict[str, Any]:
        """提交 App 到 IntentOS"""
        if not self.builder.package:
            raise RuntimeError("请先创建 App")

        # 验证
        errors = self.builder.validate()
        if errors:
            raise ValueError(f"App 验证失败：{', '.join(errors)}")

        # 提交
        result = await self.client.submit_package(
            self.builder.package,
            wait_for_approval
        )

        self.current_app_id = result["app_id"]
        return result

    async def execute(
        self,
        intent_id: str,
        input_data: dict[str, Any],
        context: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """执行意图"""
        if not self.current_app_id:
            raise RuntimeError("请先提交 App")

        return await self.client.execute_intent(
            self.current_app_id,
            intent_id,
            input_data,
            context
        )

    async def __aenter__(self) -> IntentOSConnector:
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.disconnect()


# 便捷函数

def create_app(
    name: str,
    version: str = "1.0.0",
    description: str = "",
    author: str = ""
) -> LocalAppBuilder:
    """快速创建 App"""
    builder = LocalAppBuilder()
    builder.create_package(name, version, description, author)
    return builder


def register_capability(
    cap_id: str,
    name: str,
    description: str,
    tags: Optional[list[str]] = None
) -> Callable:
    """
    装饰器方式注册能力

    示例:
        @register_capability("my_cap", "我的能力", "描述")
        def my_capability(param: str) -> dict:
            return {"result": param}
    """
    def decorator(handler: Callable) -> Callable:
        # 实际实现会注册到全局能力注册表
        logger.info(f"注册能力：{cap_id} - {name}")
        return handler
    return decorator


# 全局连接器实例
_global_connector: Optional[IntentOSConnector] = None


def get_connector() -> IntentOSConnector:
    """获取全局连接器"""
    global _global_connector
    if _global_connector is None:
        _global_connector = IntentOSConnector()
    return _global_connector


def reset_connector() -> None:
    """重置连接器"""
    global _global_connector
    _global_connector = None
