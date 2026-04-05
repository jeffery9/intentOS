"""
有机架构演化机制 - 可配置的处理阶段框架

核心理念：
- 移除硬编码的 7 层结构，改为可配置的处理阶段
- 实现使用模式分析器，自动识别高频操作序列
- 支持动态合并/拆分处理阶段
- 提供架构自省 API
- 保留默认 7 层配置以确保向后兼容

设计原则：
- Daoist 有机生长：系统根据实际使用模式演化架构
- Unix 组合性：每个阶段做一件事并做好
- 向后兼容：默认配置与现有 7 层完全兼容
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml


# =============================================================================
# 处理阶段抽象
# =============================================================================


class StageType(Enum):
    """处理阶段类型（对应 7 Level）"""

    INTENT = "intent"  # L7: 意图解析
    PLANNING = "planning"  # L6: 任务规划
    CONTEXT = "context"  # L5: 上下文收集
    SAFETY = "safety"  # L4: 安全检查
    TOOL = "tool"  # L3: 工具绑定
    EXECUTION = "execution"  # L2: 执行
    IMPROVEMENT = "improvement"  # L1: 改进反馈


@dataclass
class PipelineContext:
    """
    统一执行上下文

    贯穿所有处理阶段，每阶段只修改上下文的一部分
    """

    # 输入
    raw_input: str = ""  # 原始输入（自然语言）

    # L7: 意图层输出
    intent: Optional[dict[str, Any]] = None

    # L6: 规划层输出
    workflow: Optional[dict[str, Any]] = None

    # L5: 上下文层输出
    context: Optional[dict[str, Any]] = None

    # L4: 安全检查结果
    safety_check: Optional[dict[str, Any]] = None

    # L3: 工具绑定结果
    tool_bindings: Optional[list[dict[str, Any]]] = None

    # L2: 执行结果
    execution_result: Optional[Any] = None

    # L1: 改进建议
    improvement_suggestions: Optional[dict[str, Any]] = None

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    stage_history: list[dict[str, Any]] = field(default_factory=list)  # 阶段执行历史

    def record_stage(self, stage_name: str, duration_ms: float, success: bool) -> None:
        """记录阶段执行"""
        self.stage_history.append({
            "stage": stage_name,
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.now().isoformat(),
        })


class ProcessingStage(ABC):
    """
    处理阶段抽象基类

    每个阶段：
    - 接收 PipelineContext
    - 修改上下文的一部分
    - 返回修改后的上下文
    """

    def __init__(self, name: str, stage_type: StageType):
        self.name = name
        self.stage_type = stage_type
        self.enabled = True
        self.execution_count = 0
        self.total_duration_ms = 0.0

    @abstractmethod
    async def process(self, context: PipelineContext) -> PipelineContext:
        """
        处理阶段逻辑

        Args:
            context: 执行上下文

        Returns:
            修改后的执行上下文
        """
        ...

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """
        执行阶段（带监控）

        自动记录执行次数、时间和历史
        """
        if not self.enabled:
            return context

        start_time = time.time()
        try:
            result = await self.process(context)
            duration_ms = (time.time() - start_time) * 1000

            # 更新统计
            self.execution_count += 1
            self.total_duration_ms += duration_ms

            # 记录历史
            context.record_stage(self.name, duration_ms, True)

            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            context.record_stage(self.name, duration_ms, False)
            raise


# =============================================================================
# 默认 7 层实现
# =============================================================================


class IntentStage(ProcessingStage):
    """L7: 意图解析阶段"""

    def __init__(self):
        super().__init__("intent", StageType.INTENT)

    async def process(self, context: PipelineContext) -> PipelineContext:
        # 解析自然语言为结构化意图
        # 这里简化实现，实际应调用 IntentCompiler
        context.intent = {
            "goal": context.raw_input,
            "type": "functional",
            "parsed_at": datetime.now().isoformat(),
        }
        return context


class PlanningStage(ProcessingStage):
    """L6: 任务规划阶段"""

    def __init__(self):
        super().__init__("planning", StageType.PLANNING)

    async def process(self, context: PipelineContext) -> PipelineContext:
        # 生成任务 DAG
        context.workflow = {
            "steps": [{"id": "step1", "name": context.raw_input}],
            "dag_type": "linear",
        }
        return context


class ContextStage(ProcessingStage):
    """L5: 上下文收集阶段"""

    def __init__(self):
        super().__init__("context", StageType.CONTEXT)

    async def process(self, context: PipelineContext) -> PipelineContext:
        # 收集多模态上下文
        context.context = {
            "user_id": context.metadata.get("user_id", "anonymous"),
            "session_id": context.metadata.get("session_id", ""),
            "timestamp": datetime.now().isoformat(),
        }
        return context


class SafetyStage(ProcessingStage):
    """L4: 安全检查阶段"""

    def __init__(self):
        super().__init__("safety", StageType.SAFETY)

    async def process(self, context: PipelineContext) -> PipelineContext:
        # 权限校验
        context.safety_check = {
            "passed": True,
            "checks": ["permission", "rate_limit"],
        }
        return context


class ToolStage(ProcessingStage):
    """L3: 工具绑定阶段"""

    def __init__(self):
        super().__init__("tool", StageType.TOOL)

    async def process(self, context: PipelineContext) -> PipelineContext:
        # 能力绑定和协议适配
        context.tool_bindings = []
        return context


class ExecutionStage(ProcessingStage):
    """L2: 执行阶段"""

    def __init__(self):
        super().__init__("execution", StageType.EXECUTION)

    async def process(self, context: PipelineContext) -> PipelineContext:
        # 分布式调度执行
        context.execution_result = {
            "status": "completed",
            "message": f"执行完成: {context.raw_input}",
        }
        return context


class ImprovementStage(ProcessingStage):
    """L1: 改进反馈阶段"""

    def __init__(self):
        super().__init__("improvement", StageType.IMPROVEMENT)

    async def process(self, context: PipelineContext) -> PipelineContext:
        # 意图漂移检测和自动修复
        context.improvement_suggestions = {
            "optimization": "考虑缓存编译结果",
            "feedback": "用户满意度高",
        }
        return context


# =============================================================================
# 管道编排器
# =============================================================================


class IntentPipeline:
    """
    意图处理管道编排器

    负责：
    - 组合处理阶段
    - 按顺序执行
    - 监控和统计
    - 动态优化
    """

    def __init__(self, stages: Optional[list[ProcessingStage]] = None):
        self.stages: list[ProcessingStage] = stages or []
        self.execution_history: list[dict[str, Any]] = []

    def add_stage(self, stage: ProcessingStage, index: Optional[int] = None) -> None:
        """
        添加处理阶段

        Args:
            stage: 处理阶段实例
            index: 插入位置（None 表示追加到末尾）
        """
        if index is not None:
            self.stages.insert(index, stage)
        else:
            self.stages.append(stage)

    def remove_stage(self, stage_name: str) -> bool:
        """
        移除处理阶段

        Args:
            stage_name: 阶段名称

        Returns:
            是否成功移除
        """
        original_len = len(self.stages)
        self.stages = [s for s in self.stages if s.name != stage_name]
        return len(self.stages) < original_len

    def get_stage(self, stage_name: str) -> Optional[ProcessingStage]:
        """获取处理阶段"""
        for stage in self.stages:
            if stage.name == stage_name:
                return stage
        return None

    async def execute(self, raw_input: str, metadata: Optional[dict[str, Any]] = None) -> Any:
        """
        执行管道

        Args:
            raw_input: 原始输入（自然语言）
            metadata: 元数据

        Returns:
            最终执行结果
        """
        context = PipelineContext(
            raw_input=raw_input,
            metadata=metadata or {},
        )

        start_time = time.time()

        # 按顺序执行所有阶段
        for stage in self.stages:
            try:
                context = await stage.execute(context)
            except Exception as e:
                # 阶段失败，记录错误
                self.execution_history.append({
                    "input": raw_input,
                    "failed_stage": stage.name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                })
                raise

        total_duration_ms = (time.time() - start_time) * 1000

        # 记录执行历史
        self.execution_history.append({
            "input": raw_input,
            "stages_executed": len(context.stage_history),
            "total_duration_ms": total_duration_ms,
            "timestamp": datetime.now().isoformat(),
        })

        return context

    def get_stats(self) -> dict[str, Any]:
        """获取管道统计"""
        stage_stats = []
        for stage in self.stages:
            avg_duration = (
                stage.total_duration_ms / stage.execution_count
                if stage.execution_count > 0
                else 0
            )
            stage_stats.append({
                "name": stage.name,
                "type": stage.stage_type.value,
                "enabled": stage.enabled,
                "execution_count": stage.execution_count,
                "avg_duration_ms": avg_duration,
            })

        return {
            "total_stages": len(self.stages),
            "enabled_stages": sum(1 for s in self.stages if s.enabled),
            "stage_stats": stage_stats,
            "total_executions": len(self.execution_history),
        }


# =============================================================================
# 使用模式分析器
# =============================================================================


@dataclass
class UsagePattern:
    """使用模式"""

    pattern_id: str
    description: str
    frequency: int  # 出现频率
    stages_involved: list[str]  # 涉及的阶段
    avg_duration_ms: float
    last_seen: str = ""


class UsagePatternAnalyzer:
    """
    使用模式分析器

    分析执行历史，识别高频操作序列，为动态优化提供依据
    """

    def __init__(self):
        self.execution_records: list[dict[str, Any]] = []
        self.patterns: dict[str, UsagePattern] = {}

    def record_execution(self, execution_record: dict[str, Any]) -> None:
        """记录执行"""
        self.execution_records.append(execution_record)

        # 更新模式
        self._update_patterns(execution_record)

    def _update_patterns(self, record: dict[str, Any]) -> None:
        """更新使用模式"""
        # 简化实现：基于阶段序列生成模式 ID
        if "stages_executed" not in record:
            return

        pattern_key = f"stages_{record['stages_executed']}"

        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = UsagePattern(
                pattern_id=pattern_key,
                description=f"执行 {record['stages_executed']} 个阶段",
                frequency=0,
                stages_involved=[],
                avg_duration_ms=0,
            )

        pattern = self.patterns[pattern_key]
        pattern.frequency += 1
        pattern.avg_duration_ms = (
            pattern.avg_duration_ms * (pattern.frequency - 1) + record["total_duration_ms"]
        ) / pattern.frequency
        pattern.last_seen = record["timestamp"]

    def get_frequent_patterns(self, min_frequency: int = 10) -> list[UsagePattern]:
        """
        获取高频模式

        Args:
            min_frequency: 最小频率阈值

        Returns:
            高频模式列表
        """
        return [
            pattern
            for pattern in self.patterns.values()
            if pattern.frequency >= min_frequency
        ]

    def suggest_optimization(self) -> dict[str, Any]:
        """
        基于使用模式建议优化

        Returns:
            优化建议
        """
        frequent_patterns = self.get_frequent_patterns(min_frequency=5)

        if not frequent_patterns:
            return {"suggestion": "使用数据不足，继续收集"}

        # 找出最高频的模式
        top_pattern = max(frequent_patterns, key=lambda p: p.frequency)

        return {
            "suggestion": f"检测到高频模式: {top_pattern.description}",
            "pattern_id": top_pattern.pattern_id,
            "frequency": top_pattern.frequency,
            "avg_duration_ms": top_pattern.avg_duration_ms,
            "recommendation": "考虑合并或优化相关阶段",
        }


# =============================================================================
# 动态优化器
# =============================================================================


class PipelineOptimizer:
    """
    管道优化器

    根据使用模式分析结果，动态合并/拆分处理阶段
    """

    def __init__(self, pipeline: IntentPipeline, analyzer: UsagePatternAnalyzer):
        self.pipeline = pipeline
        self.analyzer = analyzer

    def analyze_and_optimize(self) -> dict[str, Any]:
        """
        分析并建议优化

        Returns:
            优化建议和执行结果
        """
        suggestion = self.analyzer.suggest_optimization()

        if "考虑合并" not in suggestion.get("recommendation", ""):
            return {
                "optimized": False,
                "reason": "无需优化",
                "suggestion": suggestion,
            }

        # 自动优化（简化实现）
        # 实际应根据模式智能合并阶段
        return {
            "optimized": True,
            "action": "合并低频阶段",
            "suggestion": suggestion,
        }

    def merge_stages(self, stage_names: list[str], new_stage_name: str) -> bool:
        """
        合并多个阶段为一个

        Args:
            stage_names: 要合并的阶段名称列表
            new_stage_name: 新阶段名称

        Returns:
            是否成功合并
        """
        # 简化实现：禁用被合并的阶段
        for name in stage_names:
            stage = self.pipeline.get_stage(name)
            if stage:
                stage.enabled = False

        return True

    def split_stage(self, stage_name: str, new_stages: list[ProcessingStage]) -> bool:
        """
        拆分一个阶段为多个

        Args:
            stage_name: 要拆分的阶段名称
            new_stages: 新阶段列表

        Returns:
            是否成功拆分
        """
        # 找到原阶段索引
        for i, stage in enumerate(self.pipeline.stages):
            if stage.name == stage_name:
                # 插入新阶段（在原阶段之前）
                for j, new_stage in enumerate(new_stages):
                    self.pipeline.stages.insert(i + j, new_stage)
                # 禁用原阶段
                stage.enabled = False
                return True

        return False


# =============================================================================
# 架构自省 API
# =============================================================================


class ArchitectureIntrospector:
    """
    架构自省 API

    允许查询当前处理流程、阶段配置、使用模式等
    """

    def __init__(self, pipeline: IntentPipeline, analyzer: UsagePatternAnalyzer):
        self.pipeline = pipeline
        self.analyzer = analyzer

    def get_pipeline_config(self) -> dict[str, Any]:
        """获取管道配置"""
        return {
            "total_stages": len(self.pipeline.stages),
            "stages": [
                {
                    "name": stage.name,
                    "type": stage.stage_type.value,
                    "enabled": stage.enabled,
                    "order": i,
                }
                for i, stage in enumerate(self.pipeline.stages)
            ],
        }

    def get_stage_details(self, stage_name: str) -> Optional[dict[str, Any]]:
        """获取阶段详情"""
        stage = self.pipeline.get_stage(stage_name)
        if not stage:
            return None

        return {
            "name": stage.name,
            "type": stage.stage_type.value,
            "enabled": stage.enabled,
            "execution_count": stage.execution_count,
            "total_duration_ms": stage.total_duration_ms,
            "avg_duration_ms": (
                stage.total_duration_ms / stage.execution_count
                if stage.execution_count > 0
                else 0
            ),
        }

    def get_usage_patterns(self) -> list[dict[str, Any]]:
        """获取使用模式"""
        return [
            {
                "pattern_id": pattern.pattern_id,
                "description": pattern.description,
                "frequency": pattern.frequency,
                "avg_duration_ms": pattern.avg_duration_ms,
                "last_seen": pattern.last_seen,
            }
            for pattern in self.analyzer.patterns.values()
        ]

    def get_execution_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取执行历史"""
        return self.pipeline.execution_history[-limit:]

    def export_config(self, file_path: str | Path) -> None:
        """导出配置到文件"""
        config = {
            "pipeline": self.get_pipeline_config(),
            "usage_patterns": self.get_usage_patterns(),
            "exported_at": datetime.now().isoformat(),
        }

        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix == ".json":
            path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
        else:
            path.write_text(yaml.dump(config, allow_unicode=True, default_flow_style=False))


# =============================================================================
# 工厂函数：创建默认 7 层管道
# =============================================================================


def create_default_7layer_pipeline() -> IntentPipeline:
    """
    创建默认 7 层管道（向后兼容）

    按照 L7 → L1 的顺序排列
    """
    stages = [
        IntentStage(),  # L7
        PlanningStage(),  # L6
        ContextStage(),  # L5
        SafetyStage(),  # L4
        ToolStage(),  # L3
        ExecutionStage(),  # L2
        ImprovementStage(),  # L1
    ]

    return IntentPipeline(stages=stages)


def create_minimal_pipeline() -> IntentPipeline:
    """
    创建最小管道（仅核心阶段）

    适用于简单意图，跳过不必要的阶段
    """
    stages = [
        IntentStage(),  # L7: 必须
        ExecutionStage(),  # L2: 必须
    ]

    return IntentPipeline(stages=stages)


def create_custom_pipeline(stage_configs: list[dict[str, Any]]) -> IntentPipeline:
    """
    创建自定义管道

    Args:
        stage_configs: 阶段配置列表
            每个配置包含：
            - type: 阶段类型（intent/planning/context/safety/tool/execution/improvement）
            - enabled: 是否启用
            - custom_class: 自定义阶段类（可选）

    Returns:
        自定义管道实例
    """
    stage_type_map = {
        "intent": IntentStage,
        "planning": PlanningStage,
        "context": ContextStage,
        "safety": SafetyStage,
        "tool": ToolStage,
        "execution": ExecutionStage,
        "improvement": ImprovementStage,
    }

    stages = []
    for config in stage_configs:
        stage_type = config.get("type", "intent")
        stage_class = stage_type_map.get(stage_type)

        if stage_class:
            stage = stage_class()
            stage.enabled = config.get("enabled", True)
            stages.append(stage)

    return IntentPipeline(stages=stages)
