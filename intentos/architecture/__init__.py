"""
有机架构演化机制模块

提供：
- 可配置的处理阶段框架
- 使用模式分析器
- 动态合并/拆分处理阶段
- 架构自省 API
- 默认 7 层配置（向后兼容）
"""

from .organic_pipeline import (
    ArchitectureIntrospector,
    ContextStage,
    ExecutionStage,
    ImprovementStage,
    IntentPipeline,
    IntentStage,
    PipelineContext,
    PipelineOptimizer,
    PlanningStage,
    ProcessingStage,
    SafetyStage,
    StageType,
    ToolStage,
    UsagePattern,
    UsagePatternAnalyzer,
    create_custom_pipeline,
    create_default_7layer_pipeline,
    create_minimal_pipeline,
)

__all__ = [
    # 核心抽象
    "ProcessingStage",
    "PipelineContext",
    "StageType",
    # 默认 7 层实现
    "IntentStage",
    "PlanningStage",
    "ContextStage",
    "SafetyStage",
    "ToolStage",
    "ExecutionStage",
    "ImprovementStage",
    # 管道编排
    "IntentPipeline",
    # 使用模式分析
    "UsagePattern",
    "UsagePatternAnalyzer",
    # 动态优化
    "PipelineOptimizer",
    # 架构自省
    "ArchitectureIntrospector",
    # 工厂函数
    "create_default_7layer_pipeline",
    "create_minimal_pipeline",
    "create_custom_pipeline",
]
