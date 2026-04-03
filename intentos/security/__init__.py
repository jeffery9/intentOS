"""
Security 模块

提供能力门控、权限检查等安全功能。
"""

from .gate import (
    CapabilityGate,
    GateDecision,
    GateResult,
    DenialTracker,
    PermissionMode,
    CapabilityGateError,
    CircuitBreakerError,
    PermissionDeniedError,
)

__all__ = [
    "CapabilityGate",
    "GateDecision",
    "GateResult",
    "DenialTracker",
    "PermissionMode",
    "CapabilityGateError",
    "CircuitBreakerError",
    "PermissionDeniedError",
]
