"""
意图编译器模块

提供意图编译、缓存、优化功能

PEF 格式版本:
- v1.0: intentos.agent.compiler.PEF（向后兼容）
- v2.0: intentos.compiler.pef_format.PEF（推荐，人类可读）
"""

from .cache import (
    DiskCache,
    MemoryCache,
    MultiLevelCache,
    RedisCache,
    create_disk_cache,
    create_memory_cache,
    create_multi_level_cache,
    create_redis_cache,
    generate_cache_key,
)
from .compiler import CompiledPrompt, IntentCompiler, PromptTemplate
from .compiler_v2 import IntentCompilerV2, compile_intent
from .optimizer import (
    LLM_PROFILES,
    CompilationStrategy,
    ContextManager,
    DataLocalityOptimizer,
    LLMProfile,
    LLMProvider,
    MapReduceOptimizer,
    # Map/Reduce 优化
    MapReduceStrategy,
    MemoryLocalityAwareScheduler,
    NodeCapability,
    PromptOptimizer,
    StrategySelector,
    TokenOptimizer,
    create_prompt_optimizer,
    create_strategy_selector,
    get_llm_profile,
)
from .pef_format import (
    PEF,
    CapabilityBinding,
    ContextBinding,
    IntentDeclaration,
    WorkflowDefinition,
    WorkflowStep,
    create_pef,
    load_pef,
    save_pef,
)

__all__ = [
    # PEF v2.0 格式
    "PEF",
    "IntentDeclaration",
    "ContextBinding",
    "CapabilityBinding",
    "WorkflowStep",
    "WorkflowDefinition",
    "create_pef",
    "load_pef",
    "save_pef",
    # 编译器 v2.0
    "IntentCompilerV2",
    "compile_intent",
    # 编译器 v1.0（向后兼容）
    "IntentCompiler",
    "CompiledPrompt",
    "PromptTemplate",
    # 缓存
    "MemoryCache",
    "RedisCache",
    "DiskCache",
    "MultiLevelCache",
    "create_memory_cache",
    "create_redis_cache",
    "create_disk_cache",
    "create_multi_level_cache",
    "generate_cache_key",
    # 优化器
    "LLMProfile",
    "LLMProvider",
    "PromptOptimizer",
    "StrategySelector",
    "CompilationStrategy",
    "TokenOptimizer",
    "ContextManager",
    "get_llm_profile",
    "create_prompt_optimizer",
    "create_strategy_selector",
    "LLM_PROFILES",
    # Map/Reduce 优化
    "MapReduceStrategy",
    "NodeCapability",
    "MapReduceOptimizer",
    "DataLocalityOptimizer",
    "MemoryLocalityAwareScheduler",
]
