"""
IntentOS - 意图操作系统原型

AI 原生软件范式：语言即系统
"""

from .core import (
    Intent,
    IntentType,
    IntentStatus,
    IntentTemplate,
    IntentStep,
    IntentExecutionResult,
    Capability,
    Context,
)
from .registry import IntentRegistry, capability
from .engine import ExecutionEngine
from .interface import IntentInterface, IntentOS
from .parser import IntentParser
from .compiler import IntentCompiler, CompiledPrompt, PromptTemplate
from .llm import (
    LLMExecutor,
    LLMRouter,
    LLMResponse,
    LLMBackend,
    Message,
    ToolDefinition,
    ToolCall,
    BackendConfig,
    create_executor,
    create_router,
)
from .prompt_format import (
    PromptExecutable,
    PromptMetadata,
    IntentDeclaration,
    ContextBinding,
    CapabilityBinding,
    ConstraintDefinition,
    WorkflowDefinition,
    WorkflowStep,
    OpsModel,
    SafetyPolicy,
    SafetyLevel,
    ExecutionMode,
)
from .intentgarden_v2 import IntentGarden
from .parallel import (
    DAG,
    Task,
    TaskStatus,
    TaskResult,
    ExecutionProgress,
    ExecutionNode,
    DistributedExecutor,
    ParallelDAGExecutor,
    ExecutionMode as ParallelExecutionMode,
    create_dag,
    create_task,
    create_local_node,
    create_remote_node,
)
from .memory import (
    MemoryManager,
    MemoryStats,
    MemoryLevel,
    MemoryAwareExecutor,
    MapReduceTask,
    MapReduceExecutor,
    DistributedShuffle,
    create_memory_manager as create_map_reduce_memory_manager,
    create_map_reduce_task,
    create_map_reduce_executor,
)
from .distributed_memory import (
    MemoryType,
    MemoryPriority,
    MemoryEntry,
    MemoryConfig,
    MemoryBackend,
    InMemoryBackend,
    RedisBackend,
    FileBackend,
    DistributedMemoryManager,
    create_memory_manager,
    create_and_initialize_memory_manager,
)

__version__ = "0.5.0"
__all__ = [
    # 核心模型
    "Intent",
    "IntentType",
    "IntentStatus",
    "IntentTemplate",
    "IntentStep",
    "IntentExecutionResult",
    "Capability",
    "Context",
    # 组件
    "IntentRegistry",
    "ExecutionEngine",
    "IntentParser",
    "IntentInterface",
    "IntentOS",
    # 编译器和 LLM
    "IntentCompiler",
    "CompiledPrompt",
    "PromptTemplate",
    # LLM 后端
    "LLMExecutor",
    "LLMRouter",
    "LLMResponse",
    "LLMBackend",
    "Message",
    "ToolDefinition",
    "ToolCall",
    "BackendConfig",
    "create_executor",
    "create_router",
    # Prompt 规范
    "PromptExecutable",
    "PromptMetadata",
    "IntentDeclaration",
    "ContextBinding",
    "CapabilityBinding",
    "ConstraintDefinition",
    "WorkflowDefinition",
    "WorkflowStep",
    "OpsModel",
    "SafetyPolicy",
    "SafetyLevel",
    "ExecutionMode",
    # 并行和分布式执行
    "DAG",
    "Task",
    "TaskStatus",
    "TaskResult",
    "ExecutionProgress",
    "ExecutionNode",
    "DistributedExecutor",
    "ParallelDAGExecutor",
    "ParallelExecutionMode",
    "create_dag",
    "create_task",
    "create_local_node",
    "create_remote_node",
    # 内存管理和 Map/Reduce
    "MemoryManager",
    "MemoryStats",
    "MemoryLevel",
    "MemoryAwareExecutor",
    "MapReduceTask",
    "MapReduceExecutor",
    "DistributedShuffle",
    "create_map_reduce_memory_manager",
    "create_map_reduce_task",
    "create_map_reduce_executor",
    # 分布式记忆
    "MemoryType",
    "MemoryPriority",
    "MemoryEntry",
    "MemoryConfig",
    "MemoryBackend",
    "InMemoryBackend",
    "RedisBackend",
    "FileBackend",
    "DistributedMemoryManager",
    "create_memory_manager",
    "create_and_initialize_memory_manager",
    # IntentGarden
    "IntentGarden",
    # 装饰器
    "capability",
]
