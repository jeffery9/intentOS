"""
形式化验证模块

提供意图执行的形式化验证功能
"""

from .formal import (
    CapabilitySignature,
    # 类型检查
    CapabilityTypeChecker,
    DAGNode,
    DAGValidationResult,
    # DAG 验证
    DAGValidator,
    EventType,
    ExecutionEvent,
    ExecutionStatus,
    # 执行轨迹
    ExecutionTrace,
    # 形式化验证
    FormalVerifier,
    # 轨迹回放
    TraceReplayer,
    create_capability_signature,
    create_dag_node,
    # 工厂函数
    create_execution_trace,
    create_formal_verifier,
)

__all__ = [
    # 执行轨迹
    "ExecutionTrace",
    "ExecutionEvent",
    "ExecutionStatus",
    "EventType",
    # DAG 验证
    "DAGValidator",
    "DAGNode",
    "DAGValidationResult",
    # 类型检查
    "CapabilityTypeChecker",
    "CapabilitySignature",
    # 轨迹回放
    "TraceReplayer",
    # 形式化验证
    "FormalVerifier",
    # 工厂函数
    "create_execution_trace",
    "create_dag_node",
    "create_capability_signature",
    "create_formal_verifier",
]
