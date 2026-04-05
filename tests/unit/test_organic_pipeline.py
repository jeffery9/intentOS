"""
有机架构演化机制测试

测试覆盖:
- 处理阶段抽象
- 管道编排器
- 使用模式分析器
- 动态优化器
- 架构自省 API
- 默认 7 层配置
- 向后兼容性
"""

import asyncio
import tempfile
from pathlib import Path

import pytest
import yaml

from intentos.architecture import (
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


# =============================================================================
# 处理阶段测试
# =============================================================================


class TestProcessingStage:
    """处理阶段测试"""

    def test_stage_creation(self):
        """创建阶段"""
        stage = IntentStage()
        assert stage.name == "intent"
        assert stage.stage_type == StageType.INTENT
        assert stage.enabled is True

    def test_stage_execute(self):
        """执行阶段"""
        stage = IntentStage()
        context = PipelineContext(raw_input="测试意图")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(stage.execute(context))
            assert result.intent is not None
            assert stage.execution_count == 1
        finally:
            loop.close()

    def test_stage_disabled(self):
        """禁用阶段"""
        stage = IntentStage()
        stage.enabled = False
        context = PipelineContext(raw_input="测试意图")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(stage.execute(context))
            # 禁用阶段应直接返回，不修改上下文
            assert result.intent is None
            assert stage.execution_count == 0
        finally:
            loop.close()

    def test_stage_statistics(self):
        """阶段统计"""
        stage = IntentStage()
        context = PipelineContext(raw_input="测试")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(stage.execute(context))
            loop.run_until_complete(stage.execute(context))

            assert stage.execution_count == 2
            assert stage.total_duration_ms > 0
        finally:
            loop.close()


# =============================================================================
# PipelineContext 测试
# =============================================================================


class TestPipelineContext:
    """执行上下文测试"""

    def test_context_creation(self):
        """创建上下文"""
        context = PipelineContext(raw_input="测试")
        assert context.raw_input == "测试"
        assert context.intent is None
        assert context.stage_history == []

    def test_record_stage(self):
        """记录阶段"""
        context = PipelineContext()
        context.record_stage("intent", 100.0, True)

        assert len(context.stage_history) == 1
        assert context.stage_history[0]["stage"] == "intent"
        assert context.stage_history[0]["duration_ms"] == 100.0
        assert context.stage_history[0]["success"] is True


# =============================================================================
# 管道编排器测试
# =============================================================================


class TestIntentPipeline:
    """管道编排器测试"""

    def test_create_empty(self):
        """创建空管道"""
        pipeline = IntentPipeline()
        assert len(pipeline.stages) == 0

    def test_add_stage(self):
        """添加阶段"""
        pipeline = IntentPipeline()
        pipeline.add_stage(IntentStage())
        assert len(pipeline.stages) == 1

    def test_add_stage_at_index(self):
        """在指定位置添加阶段"""
        pipeline = IntentPipeline()
        pipeline.add_stage(ExecutionStage())
        pipeline.add_stage(IntentStage(), index=0)

        assert pipeline.stages[0].name == "intent"
        assert pipeline.stages[1].name == "execution"

    def test_remove_stage(self):
        """移除阶段"""
        pipeline = IntentPipeline()
        pipeline.add_stage(IntentStage())
        pipeline.add_stage(ExecutionStage())

        removed = pipeline.remove_stage("intent")
        assert removed is True
        assert len(pipeline.stages) == 1
        assert pipeline.stages[0].name == "execution"

    def test_remove_nonexistent(self):
        """移除不存在的阶段"""
        pipeline = IntentPipeline()
        removed = pipeline.remove_stage("nonexistent")
        assert removed is False

    def test_get_stage(self):
        """获取阶段"""
        pipeline = IntentPipeline()
        stage = IntentStage()
        pipeline.add_stage(stage)

        retrieved = pipeline.get_stage("intent")
        assert retrieved is stage

    def test_get_stage_not_found(self):
        """获取不存在的阶段"""
        pipeline = IntentPipeline()
        retrieved = pipeline.get_stage("nonexistent")
        assert retrieved is None

    def test_execute_pipeline(self):
        """执行管道"""
        pipeline = create_default_7layer_pipeline()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            context = loop.run_until_complete(pipeline.execute("测试意图"))
            assert context.intent is not None
            assert context.workflow is not None
            assert context.execution_result is not None
        finally:
            loop.close()

    def test_execute_with_metadata(self):
        """带元数据执行"""
        pipeline = create_minimal_pipeline()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            context = loop.run_until_complete(
                pipeline.execute("测试", metadata={"user_id": "test_user"})
            )
            assert context.metadata["user_id"] == "test_user"
        finally:
            loop.close()

    def test_get_stats(self):
        """获取统计"""
        pipeline = create_default_7layer_pipeline()

        stats = pipeline.get_stats()
        assert stats["total_stages"] == 7
        assert stats["enabled_stages"] == 7
        assert len(stats["stage_stats"]) == 7

    def test_execution_history(self):
        """执行历史"""
        pipeline = create_minimal_pipeline()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(pipeline.execute("测试1"))
            loop.run_until_complete(pipeline.execute("测试2"))

            assert len(pipeline.execution_history) == 2
        finally:
            loop.close()


# =============================================================================
# 使用模式分析器测试
# =============================================================================


class TestUsagePatternAnalyzer:
    """使用模式分析器测试"""

    def test_record_execution(self):
        """记录执行"""
        analyzer = UsagePatternAnalyzer()
        analyzer.record_execution({
            "stages_executed": 7,
            "total_duration_ms": 500.0,
            "timestamp": "2026-04-05T14:30:25",
        })

        assert len(analyzer.execution_records) == 1

    def test_update_patterns(self):
        """更新模式"""
        analyzer = UsagePatternAnalyzer()

        # 记录多次执行
        for i in range(10):
            analyzer.record_execution({
                "stages_executed": 7,
                "total_duration_ms": 500.0 + i * 10,
                "timestamp": f"2026-04-05T14:30:{i:02d}",
            })

        patterns = analyzer.get_frequent_patterns(min_frequency=5)
        assert len(patterns) == 1
        assert patterns[0].frequency == 10

    def test_get_frequent_patterns(self):
        """获取高频模式"""
        analyzer = UsagePatternAnalyzer()

        # 记录不同模式
        for i in range(10):
            analyzer.record_execution({
                "stages_executed": 7,
                "total_duration_ms": 500.0,
                "timestamp": "2026-04-05T14:30:25",
            })

        for i in range(3):
            analyzer.record_execution({
                "stages_executed": 2,
                "total_duration_ms": 100.0,
                "timestamp": "2026-04-05T14:31:25",
            })

        frequent = analyzer.get_frequent_patterns(min_frequency=5)
        assert len(frequent) == 1
        assert frequent[0].pattern_id == "stages_7"

    def test_suggest_optimization(self):
        """建议优化"""
        analyzer = UsagePatternAnalyzer()

        # 数据不足
        suggestion = analyzer.suggest_optimization()
        assert "使用数据不足" in suggestion["suggestion"]

        # 有足够数据
        for i in range(10):
            analyzer.record_execution({
                "stages_executed": 7,
                "total_duration_ms": 500.0,
                "timestamp": f"2026-04-05T14:30:{i:02d}",
            })

        suggestion = analyzer.suggest_optimization()
        assert "检测到高频模式" in suggestion["suggestion"]
        assert suggestion["frequency"] == 10


# =============================================================================
# 动态优化器测试
# =============================================================================


class TestPipelineOptimizer:
    """动态优化器测试"""

    def test_analyze_no_optimization_needed(self):
        """分析无需优化"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        optimizer = PipelineOptimizer(pipeline, analyzer)

        result = optimizer.analyze_and_optimize()
        assert result["optimized"] is False

    def test_merge_stages(self):
        """合并阶段"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        optimizer = PipelineOptimizer(pipeline, analyzer)

        # 合并 L6 和 L5
        result = optimizer.merge_stages(["planning", "context"], "planning_context")
        assert result is True

        # 验证被合并的阶段已禁用
        planning_stage = pipeline.get_stage("planning")
        context_stage = pipeline.get_stage("context")
        assert planning_stage.enabled is False
        assert context_stage.enabled is False

    def test_split_stage(self):
        """拆分阶段"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        optimizer = PipelineOptimizer(pipeline, analyzer)

        # 拆分 execution 阶段为两个不同的阶段
        from intentos.architecture import ImprovementStage

        new_stages = [
            ExecutionStage(),  # 新阶段 1（名称相同）
            ImprovementStage(),  # 新阶段 2
        ]
        # 重命名第一个新阶段以避免冲突
        new_stages[0].name = "execution_part1"

        result = optimizer.split_stage("execution", new_stages)
        assert result is True

        # 验证原阶段已禁用
        execution_stage = pipeline.get_stage("execution")
        assert execution_stage.enabled is False

        # 验证新阶段已添加
        part1 = pipeline.get_stage("execution_part1")
        assert part1 is not None
        assert part1.enabled is True


# =============================================================================
# 架构自省 API 测试
# =============================================================================


class TestArchitectureIntrospector:
    """架构自省 API 测试"""

    def test_get_pipeline_config(self):
        """获取管道配置"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        introspector = ArchitectureIntrospector(pipeline, analyzer)

        config = introspector.get_pipeline_config()
        assert config["total_stages"] == 7
        assert len(config["stages"]) == 7
        assert config["stages"][0]["name"] == "intent"

    def test_get_stage_details(self):
        """获取阶段详情"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        introspector = ArchitectureIntrospector(pipeline, analyzer)

        details = introspector.get_stage_details("intent")
        assert details is not None
        assert details["name"] == "intent"
        assert details["type"] == "intent"

    def test_get_stage_details_not_found(self):
        """获取不存在的阶段详情"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        introspector = ArchitectureIntrospector(pipeline, analyzer)

        details = introspector.get_stage_details("nonexistent")
        assert details is None

    def test_get_usage_patterns(self):
        """获取使用模式"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()

        # 记录一些执行
        for i in range(5):
            analyzer.record_execution({
                "stages_executed": 7,
                "total_duration_ms": 500.0,
                "timestamp": f"2026-04-05T14:30:{i:02d}",
            })

        introspector = ArchitectureIntrospector(pipeline, analyzer)
        patterns = introspector.get_usage_patterns()
        assert len(patterns) == 1

    def test_get_execution_history(self):
        """获取执行历史"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        introspector = ArchitectureIntrospector(pipeline, analyzer)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(pipeline.execute("测试1"))
            loop.run_until_complete(pipeline.execute("测试2"))
            loop.run_until_complete(pipeline.execute("测试3"))

            history = introspector.get_execution_history(limit=2)
            assert len(history) == 2
        finally:
            loop.close()

    def test_export_config_json(self):
        """导出配置（JSON）"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        introspector = ArchitectureIntrospector(pipeline, analyzer)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.json"
            introspector.export_config(filepath)

            assert filepath.exists()
            content = filepath.read_text()
            assert "pipeline" in content

    def test_export_config_yaml(self):
        """导出配置（YAML）"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        introspector = ArchitectureIntrospector(pipeline, analyzer)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "config.yaml"
            introspector.export_config(filepath)

            assert filepath.exists()
            content = filepath.read_text()
            data = yaml.safe_load(content)
            assert "pipeline" in data


# =============================================================================
# 工厂函数测试
# =============================================================================


class TestFactoryFunctions:
    """工厂函数测试"""

    def test_create_default_7layer(self):
        """创建默认 7 层管道"""
        pipeline = create_default_7layer_pipeline()
        assert len(pipeline.stages) == 7

        # 验证顺序：L7 → L1
        assert pipeline.stages[0].stage_type == StageType.INTENT
        assert pipeline.stages[1].stage_type == StageType.PLANNING
        assert pipeline.stages[2].stage_type == StageType.CONTEXT
        assert pipeline.stages[3].stage_type == StageType.SAFETY
        assert pipeline.stages[4].stage_type == StageType.TOOL
        assert pipeline.stages[5].stage_type == StageType.EXECUTION
        assert pipeline.stages[6].stage_type == StageType.IMPROVEMENT

    def test_create_minimal(self):
        """创建最小管道"""
        pipeline = create_minimal_pipeline()
        assert len(pipeline.stages) == 2
        assert pipeline.stages[0].stage_type == StageType.INTENT
        assert pipeline.stages[1].stage_type == StageType.EXECUTION

    def test_create_custom(self):
        """创建自定义管道"""
        stage_configs = [
            {"type": "intent", "enabled": True},
            {"type": "safety", "enabled": True},
            {"type": "execution", "enabled": True},
        ]

        pipeline = create_custom_pipeline(stage_configs)
        assert len(pipeline.stages) == 3
        assert pipeline.stages[0].stage_type == StageType.INTENT
        assert pipeline.stages[1].stage_type == StageType.SAFETY
        assert pipeline.stages[2].stage_type == StageType.EXECUTION

    def test_create_custom_with_disabled(self):
        """创建自定义管道（含禁用阶段）"""
        stage_configs = [
            {"type": "intent", "enabled": True},
            {"type": "planning", "enabled": False},
            {"type": "execution", "enabled": True},
        ]

        pipeline = create_custom_pipeline(stage_configs)
        assert len(pipeline.stages) == 3
        assert pipeline.stages[0].enabled is True
        assert pipeline.stages[1].enabled is False
        assert pipeline.stages[2].enabled is True


# =============================================================================
# 集成测试
# =============================================================================


class TestIntegration:
    """集成测试"""

    def test_full_workflow_7layer(self):
        """完整工作流（7 层）"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        optimizer = PipelineOptimizer(pipeline, analyzer)
        introspector = ArchitectureIntrospector(pipeline, analyzer)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # 执行多次
            for i in range(10):
                context = loop.run_until_complete(
                    pipeline.execute(f"测试意图 {i}")
                )
                analyzer.record_execution({
                    "stages_executed": len(context.stage_history),
                    "total_duration_ms": sum(
                        h["duration_ms"] for h in context.stage_history
                    ),
                    "timestamp": f"2026-04-05T14:30:{i:02d}",
                })

            # 获取统计
            stats = pipeline.get_stats()
            assert stats["total_stages"] == 7
            assert stats["total_executions"] == 10

            # 获取配置
            config = introspector.get_pipeline_config()
            assert config["total_stages"] == 7

            # 获取模式
            patterns = introspector.get_usage_patterns()
            assert len(patterns) == 1

            # 优化建议
            suggestion = analyzer.suggest_optimization()
            assert "检测到高频模式" in suggestion["suggestion"]

        finally:
            loop.close()

    def test_dynamic_optimization(self):
        """动态优化"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        optimizer = PipelineOptimizer(pipeline, analyzer)

        # 模拟高频使用
        for i in range(10):
            analyzer.record_execution({
                "stages_executed": 7,
                "total_duration_ms": 500.0,
                "timestamp": f"2026-04-05T14:30:{i:02d}",
            })

        # 优化
        result = optimizer.analyze_and_optimize()
        assert "高频模式" in result["suggestion"]["suggestion"]

        # 合并阶段
        optimizer.merge_stages(["planning", "context"], "planning_context")

        # 验证
        planning = pipeline.get_stage("planning")
        context = pipeline.get_stage("context")
        assert planning.enabled is False
        assert context.enabled is False

    def test_export_and_import_config(self):
        """导出和导入配置"""
        pipeline = create_default_7layer_pipeline()
        analyzer = UsagePatternAnalyzer()
        introspector = ArchitectureIntrospector(pipeline, analyzer)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "pipeline_config.yaml"
            introspector.export_config(filepath)

            # 验证文件内容
            content = filepath.read_text()
            data = yaml.safe_load(content)
            assert data["pipeline"]["total_stages"] == 7

    def test_custom_pipeline_execution(self):
        """自定义管道执行"""
        stage_configs = [
            {"type": "intent", "enabled": True},
            {"type": "context", "enabled": True},
            {"type": "execution", "enabled": True},
        ]

        pipeline = create_custom_pipeline(stage_configs)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            context = loop.run_until_complete(pipeline.execute("自定义测试"))
            assert context.intent is not None
            assert context.context is not None
            assert context.execution_result is not None
        finally:
            loop.close()
