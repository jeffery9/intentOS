"""
Capability Gate - 能力门控管线

多步决策管线, 实现:
- Deny 优先 (全局禁止的能力)
- Bypass-immune 层 (关键安全约束不被覆盖)
- 熔断器 (防止无限重试)
- 模式级变换 (dontAsk/auto/headless)

参考 Claude Code 的 Permission Rule Chain 设计。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# =============================================================================
# 决策类型
# =============================================================================


class GateDecision(Enum):
    """门控决策"""
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"
    PASSTHROUGH = "passthrough"


@dataclass
class GateResult:
    """门控结果"""
    decision: GateDecision
    reason: str
    requires_confirmation: bool = False
    circuit_broken: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# 熔断器
# =============================================================================


class DenialTracker:
    """
    熔断器 - 防止无限重试
    
    连续 3 次拒绝 或 总计 20 次拒绝 → 熔断 5 分钟
    """
    
    def __init__(
        self,
        consecutive_threshold: int = 3,
        total_threshold: int = 20,
        circuit_duration: int = 300,
    ):
        self.consecutive_threshold = consecutive_threshold
        self.total_threshold = total_threshold
        self.circuit_duration = circuit_duration  # 秒
        
        self.consecutive_denials: dict[str, int] = {}
        self.total_denials: dict[str, int] = {}
        self.circuit_open_until: dict[str, float] = {}
    
    def record_denial(self, capability_id: str) -> None:
        """记录拒绝"""
        self.consecutive_denials[capability_id] = \
            self.consecutive_denials.get(capability_id, 0) + 1
        self.total_denials[capability_id] = \
            self.total_denials.get(capability_id, 0) + 1
        
        # 检查是否触发熔断
        if (self.consecutive_denials[capability_id] >= self.consecutive_threshold or
            self.total_denials[capability_id] >= self.total_threshold):
            self.circuit_open_until[capability_id] = time.time() + self.circuit_duration
    
    def is_circuit_open(self, capability_id: str) -> bool:
        """检查熔断器是否开启"""
        if capability_id not in self.circuit_open_until:
            return False
        
        if time.time() < self.circuit_open_until[capability_id]:
            return True
        
        # 熔断器过期, 重置
        del self.circuit_open_until[capability_id]
        self.consecutive_denials[capability_id] = 0
        return False
    
    def record_allow(self, capability_id: str) -> None:
        """记录允许 (重置连续计数)"""
        self.consecutive_denials[capability_id] = 0
    
    def reset(self, capability_id: Optional[str] = None) -> None:
        """重置熔断器"""
        if capability_id:
            self.consecutive_denials.pop(capability_id, None)
            self.total_denials.pop(capability_id, None)
            self.circuit_open_until.pop(capability_id, None)
        else:
            self.consecutive_denials.clear()
            self.total_denials.clear()
            self.circuit_open_until.clear()


# =============================================================================
# Capability Gate
# =============================================================================


class PermissionMode(Enum):
    """权限模式"""
    INTERACTIVE = "interactive"  # 正常模式, 可以询问用户
    DONT_ASK = "dont_ask"        # 不询问, 直接拒绝
    AUTO = "auto"                # 自动模式, 使用分类器
    HEADLESS = "headless"        # 无头模式, 使用 Hook


class CapabilityGate:
    """
    Capability Gate - 能力门控管线
    
    决策流程 (deny 优先, bypass-immune 层):
    1. 全局 deny 规则
    2. Ask 规则 (需要确认)
    3. 权限检查
    4. 安全标注检查 (bypass-immune)
    5. 熔断器检查
    6. 内容级规则 (bypass-immune)
    7. 安全检查 (bypass-immune)
    """
    
    def __init__(self):
        self.deny_rules: set[str] = set()  # 全局禁止的能力
        self.ask_rules: set[str] = set()   # 需要确认的能力
        self.denial_tracker = DenialTracker()
        self.mode = PermissionMode.INTERACTIVE
    
    def add_deny_rule(self, capability_id: str) -> None:
        """添加全局禁止规则"""
        self.deny_rules.add(capability_id)
    
    def remove_deny_rule(self, capability_id: str) -> None:
        """移除全局禁止规则"""
        self.deny_rules.discard(capability_id)
    
    def add_ask_rule(self, capability_id: str) -> None:
        """添加需要确认规则"""
        self.ask_rules.add(capability_id)
    
    def remove_ask_rule(self, capability_id: str) -> None:
        """移除需要确认规则"""
        self.ask_rules.discard(capability_id)
    
    async def evaluate(
        self,
        capability_id: str,
        context: Any,
        input_data: dict[str, Any],
        capability: Optional[Any] = None,
    ) -> GateResult:
        """
        执行管线评估
        
        Args:
            capability_id: 能力 ID
            context: 执行上下文 (包含 permissions)
            input_data: 输入数据
            capability: 能力对象 (可选, 如未提供则从 registry 获取)
        
        Returns:
            门控结果
        """
        # Step 1a: 全局 deny 规则 (最高优先级)
        if capability_id in self.deny_rules:
            return GateResult(GateDecision.DENY, "全局禁止")
        
        # Step 1b: Ask 规则 (需要确认)
        if capability_id in self.ask_rules:
            return GateResult(
                GateDecision.ASK,
                "需要用户确认",
                requires_confirmation=True
            )
        
        # Step 1c: 权限检查
        if capability and capability.required_permissions:
            if not self._has_permission(context, capability):
                return GateResult(
                    GateDecision.ASK,
                    f"权限不足: 需要 {capability.required_permissions}",
                    requires_confirmation=True
                )
        
        # Step 1d: 安全标注检查 (bypass-immune)
        if capability:
            if hasattr(capability, 'is_destructive') and capability.is_destructive(input_data):
                return GateResult(
                    GateDecision.ASK,
                    "破坏性操作",
                    requires_confirmation=True
                )
        
        # Step 1e: 熔断器检查
        if self.denial_tracker.is_circuit_open(capability_id):
            return GateResult(
                GateDecision.DENY,
                "熔断器触发",
                circuit_broken=True
            )
        
        # Step 1f: 内容级规则 (bypass-immune)
        if self._matches_content_rule(capability_id, input_data):
            return GateResult(
                GateDecision.ASK,
                "内容级规则",
                requires_confirmation=True
            )
        
        # Step 1g: 安全检查 (bypass-immune)
        if self._safety_check(input_data):
            return GateResult(
                GateDecision.ASK,
                "安全检查未通过",
                requires_confirmation=True
            )
        
        # 全部通过
        return GateResult(GateDecision.ALLOW, "允许执行")
    
    def transform_decision(self, result: GateResult) -> GateResult:
        """
        根据权限模式变换门控结果
        
        模式级变换:
        - dontAsk: ASK/PASSTHROUGH → DENY
        - auto: PASSTHROUGH → 使用分类器 API
        - headless: PASSTHROUGH → 使用 Hook 系统
        """
        if self.mode == PermissionMode.DONT_ASK:
            # 不能问用户就直接拒绝
            if result.decision in (GateDecision.ASK, GateDecision.PASSTHROUGH):
                return GateResult(
                    GateDecision.DENY,
                    f"dontAsk 模式: {result.reason}"
                )
        
        elif self.mode == PermissionMode.AUTO:
            # 使用分类器 API 评估 (TODO: 实现分类器)
            if result.decision == GateDecision.PASSTHROUGH:
                return GateResult(
                    GateDecision.ASK,
                    "Auto 模式需要分类器评估",
                    requires_confirmation=True
                )
        
        elif self.mode == PermissionMode.HEADLESS:
            # 使用 Hook 系统处理 (TODO: 实现 Hook)
            if result.decision == GateDecision.PASSTHROUGH:
                return GateResult(
                    GateDecision.ASK,
                    "Headless 模式需要 Hook 处理",
                    requires_confirmation=True
                )
        
        return result
    
    def _has_permission(self, context: Any, capability: Any) -> bool:
        """检查权限"""
        # 兼容字典或对象格式
        if isinstance(context, dict):
            user_perms = set(context.get("permissions", []))
        else:
            user_perms = set(getattr(context, "permissions", []))
        
        required_perms = set(capability.required_permissions)
        return required_perms.issubset(user_perms)
    
    def _matches_content_rule(self, capability_id: str, input_data: dict) -> bool:
        """
        内容级规则匹配 (bypass-immune)
        
        例如: Bash(npm publish:*) 即使 bypass 也需要确认
        """
        # TODO: 实现内容级规则匹配
        return False
    
    def _safety_check(self, input_data: dict) -> bool:
        """
        安全检查 (bypass-immune)
        
        例如: 敏感路径检查 (.git/, .claude/ 等)
        """
        # TODO: 实现安全检查
        return False


# =============================================================================
# 异常定义
# =============================================================================


class CapabilityGateError(Exception):
    """能力门控异常"""
    pass


class CircuitBreakerError(CapabilityGateError):
    """熔断器异常"""
    pass


class PermissionDeniedError(CapabilityGateError):
    """权限拒绝异常"""
    pass
