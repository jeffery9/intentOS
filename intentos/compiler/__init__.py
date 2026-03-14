"""
意图编译器模块

提供意图编译、缓存、优化功能
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

__all__ = [
    # 编译器
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
