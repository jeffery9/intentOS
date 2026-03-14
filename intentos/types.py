"""
IntentOS 类型定义

集中定义所有类型注解，避免循环导入
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

# =============================================================================
# 基础类型
# =============================================================================

JSON = Dict[str, Any]
Metadata = Dict[str, Any]


# =============================================================================
# 状态枚举
# =============================================================================


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MemoryType(Enum):
    """记忆类型"""

    WORKING = "working"  # 工作记忆
    SHORT_TERM = "short_term"  # 短期记忆
    LONG_TERM = "long_term"  # 长期记忆


class MemoryPriority(Enum):
    """记忆优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


# =============================================================================
# 结果类型
# =============================================================================


@dataclass
class Result:
    """执行结果基类"""

    success: bool
    error: Optional[str] = None
    audit_id: Optional[str] = None


@dataclass
class CreateResult(Result):
    """创建操作结果"""

    created_id: Optional[str] = None


@dataclass
class UpdateResult(Result):
    """更新操作结果"""

    pass


@dataclass
class DeleteResult(Result):
    """删除操作结果"""

    pass


@dataclass
class QueryResult(Result):
    """查询操作结果"""

    data: Any = None


# =============================================================================
# 配置类型
# =============================================================================


@dataclass
class VMConfig:
    """虚拟机配置"""

    max_concurrency: int = 10
    timeout_seconds: int = 300
    retry_count: int = 3
    memory_limit_mb: int = 1024


@dataclass
class DistributedConfig:
    """分布式配置"""

    cluster_name: str = "intentos-cluster"
    node_id: Optional[str] = None
    seed_nodes: Optional[List[str]] = None
    replication_factor: int = 3
    consistency_level: str = "quorum"  # eventual/quorum/strong


# =============================================================================
# 回调类型
# =============================================================================

InstructionCallback = Callable[[str, JSON], None]
ProgressCallback = Callable[[float, str], None]
ErrorCallback = Callable[[str, Exception], None]


# =============================================================================
# 流类型
# =============================================================================

InstructionStream = AsyncIterator[str]
DataStream = AsyncIterator[JSON]
ProgressStream = AsyncIterator[tuple[float, str]]
