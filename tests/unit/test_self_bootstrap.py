"""
Self-Bootstrap 自我改进功能测试

测试元意图执行、协议自扩展和模板自生长
"""

import pytest
from datetime import datetime

from intentos.bootstrap import (
    MetaIntentExecutor,
    MetaIntent,
    MetaIntentType,
    BootstrapPolicy,
    ProtocolSelfExtender,
    IntentTemplateSelfGrower,
    IntentPatternMiner,
    create_meta_intent,
    create_meta_intent_executor,
)
from intentos.apps import IntentPackageRegistry
from intentos.graph import create_intent_graph


class TestMetaIntent:
    """测试元意图"""
    
    def test_create_meta_intent(self):
        """测试创建元意图"""
        meta_intent = create_meta_intent(
            type=MetaIntentType.REGISTER_CAPABILITY,
            target="test_capability",
            params={"name": "test_capability"},
            description="测试能力",
        )
        
        assert meta_intent.type == MetaIntentType.REGISTER_CAPABILITY
        assert meta_intent.target == "test_capability"
        assert meta_intent.description == "测试能力"
    
    def test_meta_intent_to_dict(self):
        """测试元意图序列化"""
        meta_intent = MetaIntent(
            type=MetaIntentType.OPTIMIZE_PERFORMANCE,
            target="cache",
            params={"size": 1000},
        )
        
        data = meta_intent.to_dict()
        
        assert data["type"] == "optimize_performance"
        assert data["target"] == "cache"
        assert data["params"]["size"] == 1000


class TestMetaIntentExecutor:
    """测试元意图执行器"""
    
    @pytest.fixture
    def executor(self):
        """创建执行器"""
        registry = IntentPackageRegistry()
        return create_meta_intent_executor(registry=registry)
    
    @pytest.mark.asyncio
    async def test_execute_register_capability(self, executor):
        """测试执行能力注册"""
        meta_intent = create_meta_intent(
            type=MetaIntentType.REGISTER_CAPABILITY,
            target="ar_renderer",
            params={
                "name": "ar_renderer",
                "description": "AR 渲染能力",
                "type": "io",
            },
        )
        
        result = await executor.execute(meta_intent)
        
        assert result.status == "completed"
        assert result.result["capability"]["name"] == "ar_renderer"
    
    @pytest.mark.asyncio
    async def test_execute_register_intent_template(self, executor):
        """测试执行意图模板注册"""
        meta_intent = create_meta_intent(
            type=MetaIntentType.REGISTER_INTENT_TEMPLATE,
            target="compare_regions",
            params={
                "name": "compare_regions",
                "description": "对比区域销售",
                "parameters": [
                    {"name": "region1", "type": "string"},
                    {"name": "region2", "type": "string"},
                ],
            },
        )
        
        result = await executor.execute(meta_intent)
        
        assert result.status == "completed"
        assert result.result["template"]["name"] == "compare_regions"
    
    @pytest.mark.asyncio
    async def test_execute_optimize_performance(self, executor):
        """测试执行性能优化"""
        meta_intent = create_meta_intent(
            type=MetaIntentType.OPTIMIZE_PERFORMANCE,
            target="system",
            params={
                "actions": [
                    {"action": "increase_cache_size", "target": "l2", "value": 5000},
                    {"action": "enable_feature", "target": "incremental_compilation", "value": True},
                ]
            },
        )
        
        result = await executor.execute(meta_intent)
        
        assert result.status == "completed"
        assert len(result.result["actions"]) == 2
    
    def test_get_history(self, executor):
        """测试获取执行历史"""
        # 执行几个元意图
        for i in range(3):
            meta_intent = create_meta_intent(
                type=MetaIntentType.REGISTER_CAPABILITY,
                target=f"cap_{i}",
                params={"name": f"cap_{i}"},
            )
            executor.execute(meta_intent)
        
        history = executor.get_history(time_range="24h")
        assert len(history) == 3
    
    def test_get_statistics(self, executor):
        """测试获取统计"""
        # 执行几个元意图
        executor.execute(create_meta_intent(
            type=MetaIntentType.REGISTER_CAPABILITY,
            target="cap1",
            params={"name": "cap1"},
        ))
        
        executor.execute(create_meta_intent(
            type=MetaIntentType.OPTIMIZE_PERFORMANCE,
            target="system",
            params={"actions": []},
        ))
        
        stats = executor.get_statistics()
        
        assert stats["total_executions"] == 2
        assert stats["completed"] == 2
        assert "register_capability" in stats["by_type"]


class TestProtocolSelfExtender:
    """测试协议自扩展器"""
    
    def test_detect_capability_gap(self):
        """测试检测能力缺口"""
        extender = ProtocolSelfExtender()
        
        # 检测 AR 能力缺口
        gap = extender.detect_capability_gap(
            intent_text="用 AR 展示销售数据",
            available_capabilities=["data_loader", "chart_renderer"],
        )
        
        assert gap is not None
        assert "ar" in gap.capability_name.lower() or "render" in gap.capability_name.lower()
    
    def test_detect_no_gap(self):
        """测试没有能力缺口的情况"""
        extender = ProtocolSelfExtender()
        
        gap = extender.detect_capability_gap(
            intent_text="查询销售数据",
            available_capabilities=["data_loader", "chart_renderer"],
        )
        
        assert gap is None
    
    def test_generate_extension_suggestion(self):
        """测试生成扩展建议"""
        extender = ProtocolSelfExtender()
        
        # 先检测缺口
        gap = extender.detect_capability_gap(
            intent_text="用 3D 展示数据",
            available_capabilities=[],
        )
        
        # 生成建议
        suggestion = extender.generate_extension_suggestion(gap)
        
        assert suggestion.suggestion_type == "register_capability"
        assert "3d" in suggestion.params["name"].lower() or "render" in suggestion.params["name"].lower()
    
    def test_suggestion_to_meta_intent(self):
        """测试建议转换为元意图"""
        extender = ProtocolSelfExtender()
        
        gap = extender.detect_capability_gap(
            intent_text="用 AR 展示",
            available_capabilities=[],
        )
        suggestion = extender.generate_extension_suggestion(gap)
        
        meta_intent = suggestion.to_meta_intent()
        
        assert meta_intent.type == MetaIntentType.REGISTER_CAPABILITY
        assert meta_intent.target == gap.capability_name


class TestIntentPatternMiner:
    """测试意图模式挖掘器"""
    
    def test_record_intent(self):
        """测试记录意图"""
        miner = IntentPatternMiner()
        
        miner.record_intent(
            intent_text="对比华东和华南的销售",
            parameters={"region1": "华东", "region2": "华南"},
            success=True,
        )
        
        assert len(miner.history) == 1
    
    def test_analyze_patterns(self):
        """测试分析模式"""
        miner = IntentPatternMiner()
        
        # 记录多个相似意图
        for i in range(10):
            miner.record_intent(
                intent_text=f"对比华东和华南的 Q{i+1}销售",
                parameters={"region1": "华东", "region2": "华南", "period": f"Q{i+1}"},
                success=True,
            )
        
        patterns = miner.analyze_patterns(time_range="7d", min_frequency=5)
        
        assert len(patterns) >= 1
        assert patterns[0].frequency >= 5
    
    def test_get_template_candidates(self):
        """测试获取模板候选"""
        miner = IntentPatternMiner()
        
        # 记录足够多的相似意图
        for i in range(10):
            miner.record_intent(
                intent_text=f"分析华东区 Q{i+1}销售",
                parameters={"region": "华东", "period": f"Q{i+1}"},
                success=True,
            )
        
        miner.analyze_patterns()
        candidates = miner.get_template_candidates(min_frequency=5)
        
        assert len(candidates) >= 1


class TestIntentTemplateSelfGrower:
    """测试意图模板自生长器"""
    
    @pytest.fixture
    def grower(self):
        """创建自生长器"""
        graph = create_intent_graph()
        return IntentTemplateSelfGrower(intent_graph=graph)
    
    @pytest.mark.asyncio
    async def test_grow_from_history(self, grower):
        """测试从历史生长模板"""
        # 记录历史交互
        for i in range(10):
            grower.record_intent(
                intent_text=f"对比华东和华南的 Q{i+1}销售",
                parameters={"region1": "华东", "region2": "华南", "period": f"Q{i+1}"},
                success=True,
            )
        
        # 生长模板
        templates = await grower.grow_from_history(
            time_range="7d",
            min_frequency=5,
            auto_approve=True,
        )
        
        assert len(templates) >= 1
        assert "template" in templates[0]["template"]["name"]
    
    def test_get_statistics(self, grower):
        """测试获取统计"""
        # 记录一些意图
        for i in range(5):
            grower.record_intent(
                intent_text=f"测试意图 {i}",
                parameters={"param": f"value_{i}"},
                success=True,
            )
        
        stats = grower.get_statistics()
        
        assert stats["total_history_entries"] == 5


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_self_improvement_workflow(self):
        """测试完整的自我改进流程"""
        # 1. 初始化组件
        registry = IntentPackageRegistry()
        executor = create_meta_intent_executor(registry=registry)
        extender = ProtocolSelfExtender()
        
        # 2. 检测能力缺口
        gap = extender.detect_capability_gap(
            intent_text="用 VR 展示数据",
            available_capabilities=["data_loader"],
        )
        
        assert gap is not None
        
        # 3. 生成扩展建议
        suggestion = extender.generate_extension_suggestion(gap)
        meta_intent = suggestion.to_meta_intent()
        
        # 4. 执行元意图
        meta_intent.approved_by = "auto_approved"
        result = await executor.execute(meta_intent)
        
        assert result.status == "completed"
        
        # 5. 验证能力已注册
        stats = executor.get_statistics()
        assert stats["completed"] == 1
