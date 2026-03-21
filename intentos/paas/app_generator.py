# -*- coding: utf-8 -*-
"""
IntentOS App Generator Module

App 生成器模块，根据租户资源和用户身份即时生成 App 实例。
支持版本管理、个性化配置、能力绑定。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class GeneratedApp:
    """生成的 App 实例 (运行时实体)"""
    id: str                          # 实例 ID (通常是 hash(app_id+tenant_id+user_id))
    app_id: str                      # 指向市场中的 App 定义 ID
    tenant_id: str
    user_id: str
    version: str
    name: str
    description: str
    intents: dict[str, Any]
    capabilities: dict[str, Any]
    config: dict[str, Any]
    resources: dict[str, Any]

    # --- 运行时追踪 (对齐内核) ---
    active_pids: list[str] = field(default_factory=list) # 该实例正在运行的内核进程 PID
    status: str = "idle"             # idle, running, suspended

    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_context(self) -> dict[str, Any]:
        """生成符合内核隔离要求的上下文令牌"""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "app_instance_id": self.id,
            "permissions": self.metadata.get("permissions", []),
            "gas_limit": self.config.get("gas_limit", 5000)
        }

    def to_dict(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "app_id": self.app_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "active_pids": self.active_pids,
            "status": self.status,
            # ... 保持其他原有字段
            "created_at": self.created_at.isoformat(),
        }
        # 补全其他元数据
        data.update({
            "name": self.name,
            "description": self.description,
            "config": self.config,
        })
        return data

    def get_capability(self, capability_id: str) -> Optional[Any]:
        """获取能力"""
        return self.capabilities.get(capability_id)

    def get_intent(self, intent_id: str) -> Optional[dict[str, Any]]:
        """获取意图"""
        return self.intents.get(intent_id)


@dataclass
class AppGenerationRequest:
    """App 生成请求 (恢复原有设计)"""
    app_id: str                      # App 定义 ID
    tenant_id: str                   # 租户 ID
    user_id: str                     # 用户 ID
    version: Optional[str] = None    # 指定版本（可选）
    context: Optional[dict[str, Any]] = None  # 额外上下文

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_id": self.app_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "version": self.version,
            "context": self.context,
        }

# --- Genesis App Definition (The first Self-Bootstrapped App) ---

def get_genesis_app_program() -> Any:
    """
    定义“创世 App”的语义程序

    第一性原理：这个程序是系统内置的、用于创造其他程序的“元程序”。
    它不被创造，而是随系统一同诞生。
    """
    from intentos.semantic_vm import SemanticProgram, SemanticInstruction, SemanticOpcode

    prog = SemanticProgram(
        name="genesis-app",
        description="The AI Native App for building other AI Native Apps."
    )

    prog.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE,
        parameters={
            "intent": """你是一个 AI Native App 架构师。根据开发者的描述，调用元能力（meta-capabilities）来生成或更新 App 的语义定义。

            ## 可用元能力
            - meta:create_spec(session_id, name, description)
            - meta:add_intent(session_id, intent_name, description)
            - meta:set_permission(session_id, permission)
            - meta:publish(session_id)

            ## 对话历史
            {history}

            ## 当前规格
            {current_spec}

            ## 开发者最新要求
            {latest_message}

            请分析开发者的要求并决定调用哪个元能力。
            如果开发者想要发布，请调用 meta:publish。
            """
        }
    ))
    return prog

# 模拟系统启动时加载 Genesis App
GENESIS_APP_PROGRAM = get_genesis_app_program()


@dataclass
class DevSession:
    """开发者会话"""
    session_id: str
    developer_id: str
    current_spec: dict[str, Any] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    status: str = "ideation" # ideation, drafting, testing, finalized

class AppConversationStudio:
    """
    Conversational IDE for AI Native Apps (driven by the Genesis App)
    """

    def __init__(self, marketplace: Any, llm_executor: Any):
        self.marketplace = marketplace
        self.llm_executor = llm_executor # Retained for potential future use
        self.sessions: dict[str, DevSession] = {}

    async def chat_build_step(self, session_id: str, developer_id: str, message: str) -> str:
        """
        交互式构建步骤 (调用内置的创世 App)
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = DevSession(session_id, developer_id)

        session = self.sessions[session_id]
        session.history.append({"role": "user", "content": message})

        # 1. 准备执行上下文
        context = {
            "history": session.history,
            "current_spec": session.current_spec,
            "latest_message": message,
            "session_id": session_id,
        }

        # 2. 在内核中执行预加载的“创世 App”
        from intentos.interface.interface import IntentOS
        os_instance = IntentOS()
        os_instance.vm.local_vm.load_program(GENESIS_APP_PROGRAM) # Ensure it's loaded
        result = await os_instance.vm.local_vm.execute_program("genesis-app", context)

        # 3. 根据执行结果更新会话状态
        if result.get("success"):
            final_data = result["results"][-1].get("result", {})
            if final_data.get("spec"):
                session.current_spec = final_data["spec"]

            if "app_id" in final_data:
                return f"🚀 App 已成功发布！ID: {final_data['app_id']}"
            else:
                 return f"✅ 规格已更新。\n\n您可继续提出修改建议，或回复 '发布应用'。"
        else:
            return f"❌ 执行创世 App 失败: {result.get('error')}"

    async def finalize_and_publish(self, session_id: str) -> dict[str, Any]:
        """一键发布到市场"""
        session = self.sessions.get(session_id)
        if not session or not session.current_spec:
            return {"success": False, "error": "No active session"}

        spec = session.current_spec
        # 转换 spec 为 marketplace 格式
        app_metadata = await self.marketplace.submit_app(
            name=spec["name"],
            description=spec["description"],
            category=spec.get("category", "other"),
            developer_id=session.developer_id,
            developer_name=f"Dev_{session.developer_id}",
            manifest={
                "pricing": {"model": "pay_per_use"},
                "permissions": spec.get("permissions", []),
                "logic": spec.get("logic", [])
            }
        )

        # 模拟自动通过审核并发布
        await self.marketplace.review_app(app_metadata.app_id, True, "auto_system")
        await self.marketplace.publish_app(app_metadata.app_id)

        session.status = "finalized"
        return {"success": True, "app_id": app_metadata.app_id}


class AppGenerator:
    """
    App 生成器

    根据租户资源和用户身份即时生成 App 实例。
    """

    def __init__(
        self,
        tenant_manager: Any,
        capability_binder: Any,
        personalization_manager: Any,
        version_manager: Any
    ) -> None:
        self.tenant_manager = tenant_manager
        self.capability_binder = capability_binder
        self.personalization_manager = personalization_manager
        self.version_manager = version_manager
        self.generated_apps: dict[str, GeneratedApp] = {}  # app_instance_id -> GeneratedApp
        logger.info("App 生成器初始化完成")

    def generate(
        self,
        request: AppGenerationRequest
    ) -> GeneratedApp:
        """
        生成 App 实例 (完善权限合成逻辑)

        第一性原理：实例化是“代码+资源+权限”的聚合过程。
        """
        # 1. 获取租户信息 (原有逻辑)
        tenant = self.tenant_manager.get_tenant(request.tenant_id)
        if not tenant:
            raise ValueError(f"租户不存在：{request.tenant_id}")

        # 2. 获取 App 定义
        version = request.version or self.version_manager.get_user_version(
            request.user_id, request.app_id
        )
        app_package = self.version_manager.get_version(request.app_id, version)
        if not app_package:
            raise ValueError(f"App 不存在：{request.app_id} v{version}")

        # 3. 【关键对齐】合成权限 (RoleManager + Capability Alignment)
        from .tenant import get_role_manager
        role_manager = get_role_manager()

        # 创建用户上下文，内部会自动扫描该租户绑定的私有能力并注入权限令牌
        user_context = role_manager.create_user_context(
            tenant_id=request.tenant_id,
            user_id=request.user_id
        )

        # 4. 绑定能力并注入租户资源
        merged_config = self._merge_config(
            app_package.config.get("defaults", {}),
            tenant.config,
            self.personalization_manager.get_config(request.user_id, request.app_id)
        )

        bound_capabilities = self._bind_capabilities(
            app_package.capabilities,
            tenant,
            merged_config,
            request.user_id
        )

        # 5. 生成 App 实例 ID
        instance_id = self._generate_instance_id(
            request.app_id, request.tenant_id, request.user_id, version
        )

        # 6. 创建具备完整上下文的实例
        generated_app = GeneratedApp(
            id=instance_id,
            app_id=request.app_id,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            version=version,
            name=app_package.name,
            description=app_package.description,
            intents=app_package.intents,
            capabilities=bound_capabilities,
            config=merged_config,
            resources={k: v for k, v in tenant.resources.items()},
            metadata={
                "generated_at": datetime.now().isoformat(),
                "permissions": user_context.permissions, # 注入合成后的权限
                "roles": user_context.roles,
                "tenant_config": tenant.config,
            },
        )

        # 7. 缓存 App 实例
        self.generated_apps[instance_id] = generated_app
        logger.info(f"🚀 App Instance generated with {len(user_context.permissions)} permissions: {instance_id}")

        return generated_app

    def get_app(self, instance_id: str) -> Optional[GeneratedApp]:
        """获取生成的 App 实例"""
        return self.generated_apps.get(instance_id)

    def invalidate(self, instance_id: str) -> bool:
        """使 App 实例失效"""
        if instance_id in self.generated_apps:
            del self.generated_apps[instance_id]
            logger.info(f"App 实例已失效：{instance_id}")
            return True
        return False

    def invalidate_user_apps(self, user_id: str) -> int:
        """使指定用户的所有 App 实例失效"""
        count = 0
        to_remove = [
            instance_id for instance_id, app in self.generated_apps.items()
            if app.user_id == user_id
        ]
        for instance_id in to_remove:
            self.invalidate(instance_id)
            count += 1
        return count

    def _merge_config(
        self,
        defaults: dict[str, Any],
        tenant_config: dict[str, Any],
        user_config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        合并配置

        优先级：user_config > tenant_config > defaults
        """
        merged = {}

        # 1. 应用默认配置
        merged.update(defaults)

        # 2. 应用租户配置
        merged.update(tenant_config)

        # 3. 应用用户配置（优先级最高）
        merged.update(user_config)

        return merged

    def _bind_capabilities(
        self,
        capabilities: dict[str, Any],
        tenant: Any,
        config: dict[str, Any],
        user_id: str
    ) -> dict[str, Any]:
        """绑定能力"""
        bound = {}

        for cap_id, cap_def in capabilities.items():
            template_id = cap_def.get("template_id", cap_id)

            try:
                # 使用能力绑定器绑定能力
                bound_cap = self.capability_binder.bind(
                    template_id=template_id,
                    tenant_id=tenant.id,
                    resources=tenant.resources,
                    config={**cap_def.get("config", {}), **config},
                    user_context=type("UserContext", (), {"user_id": user_id})()
                )
                bound[cap_id] = bound_cap
            except Exception as e:
                logger.warning(f"能力绑定失败：{cap_id}, error={e}")
                # 绑定失败时，保留原始定义
                bound[cap_id] = cap_def

        return bound

    def _generate_instance_id(
        self,
        app_id: str,
        tenant_id: str,
        user_id: str,
        version: str
    ) -> str:
        """生成 App 实例 ID"""
        import hashlib
        content = f"{app_id}:{tenant_id}:{user_id}:{version}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"app_{app_id}_{hash_value}"


class AppInstanceCache:
    """
    App 实例缓存

    缓存生成的 App 实例，提高响应速度。
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: dict[str, tuple[GeneratedApp, datetime]] = {}
        logger.info(f"App 实例缓存初始化：max_size={max_size}, ttl={ttl_seconds}s")

    def get(self, instance_id: str) -> Optional[GeneratedApp]:
        """从缓存获取 App 实例"""
        if instance_id not in self.cache:
            return None

        app, created_at = self.cache[instance_id]

        # 检查是否过期
        if datetime.now() - created_at > timedelta(seconds=self.ttl_seconds):
            self.remove(instance_id)
            return None

        return app

    def put(self, app: GeneratedApp) -> None:
        """缓存 App 实例"""
        # 如果缓存已满，移除最旧的
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        self.cache[app.id] = (app, datetime.now())
        logger.debug(f"App 实例已缓存：{app.id}")

    def remove(self, instance_id: str) -> bool:
        """从缓存移除"""
        if instance_id in self.cache:
            del self.cache[instance_id]
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        logger.info("App 实例缓存已清空")

    def _evict_oldest(self) -> None:
        """移除最旧的缓存项"""
        if not self.cache:
            return

        oldest_id = min(
            self.cache.keys(),
            key=lambda k: self.cache[k][1]
        )
        self.remove(oldest_id)
        logger.debug(f"缓存驱逐：{oldest_id}")


# 全局 App 生成器实例
_global_app_generator: Optional[AppGenerator] = None
_global_app_cache: Optional[AppInstanceCache] = None


def get_app_generator(
    tenant_manager: Any = None,
    capability_binder: Any = None,
    personalization_manager: Any = None,
    version_manager: Any = None
) -> AppGenerator:
    """获取全局 App 生成器"""
    global _global_app_generator

    if _global_app_generator is None:
        # 延迟导入避免循环依赖
        from .capability_binding import get_capability_binder
        from .personalization import get_personalization_manager
        from .tenant import get_tenant_manager
        from .versioning import get_version_manager

        _global_app_generator = AppGenerator(
            tenant_manager=tenant_manager or get_tenant_manager(),
            capability_binder=capability_binder or get_capability_binder(),
            personalization_manager=personalization_manager or get_personalization_manager(),
            version_manager=version_manager or get_version_manager(),
        )

    return _global_app_generator


def get_app_cache() -> AppInstanceCache:
    """获取全局 App 实例缓存"""
    global _global_app_cache
    if _global_app_cache is None:
        _global_app_cache = AppInstanceCache()
    return _global_app_cache


def reset_app_generator() -> None:
    """重置 App 生成器"""
    global _global_app_generator, _global_app_cache
    _global_app_generator = None
    _global_app_cache = None
