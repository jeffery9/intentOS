"""
IntentOS Bootstrap 测试套件

测试覆盖：
- Self-Bootstrap 执行器
- 元意图执行器
- 协议自扩展器
- 模板自生长器
- 自修改 OS
- 双内存 OS
- 自我繁殖（改进版）

目标覆盖率：>80%
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from intentos.bootstrap import (
    # Executor
    SelfBootstrapExecutor,
    BootstrapRecord,
    BootstrapPolicy,
    # Meta Intent
    MetaIntentExecutor,
    MetaIntent,
    MetaIntentType,
    # Protocol Extender
    ProtocolSelfExtender,
    CapabilityGap,
    # Template Grower
    IntentTemplateSelfGrower,
    IntentPatternMiner,
    # Self Modifying OS
    SelfModifyingOS,
    # Dual Memory OS
    DualMemoryOS,
    MemoryBankStatus,
    # Self Reproduction
    SelfReproduction,
    ReproductionType,
    ReproductionStatus,
    SecurityError,
)
from intentos.apps import IntentPackageRegistry
from intentos.graph import create_intent_graph


# =============================================================================
# Self-Bootstrap Executor 测试
# =============================================================================


class TestSelfBootstrapExecutor:
    """测试 Self-Bootstrap 执行器"""
    
    def test_bootstrap_record_creation(self):
        """测试自举记录创建"""
        record = BootstrapRecord(
            action="modify_parse_prompt",
            target="intent_parser",
            old_value="old_prompt",
            new_value="new_prompt",
        )
        
        assert record.action == "modify_parse_prompt"
        assert record.status == "pending"
        assert record.id is not None
    
    def test_bootstrap_record_to_dict(self):
        """测试自举记录序列化"""
        record = BootstrapRecord(
            action="test_action",
            target="test_target",
        )
        
        data = record.to_dict()
        
        assert "id" in data
        assert "action" in data
        assert "timestamp" in data
    
    def test_bootstrap_policy_default(self):
        """测试默认策略"""
        policy = BootstrapPolicy()
        
        assert policy.allow_self_modification is True
        assert "delete_all_templates" in policy.require_approval_for
        assert policy.max_modifications_per_hour == 10
    
    @pytest.mark.asyncio
    async def test_executor_creation(self):
        """测试执行器创建"""
        executor = SelfBootstrapExecutor()
        
        assert executor.policy is not None
        assert len(executor.history) == 0
    
    @pytest.mark.asyncio
    async def test_executor_execute_modification(self):
        """测试执行修改操作"""
        executor = SelfBootstrapExecutor()
        
        record = BootstrapRecord(
            action="modify_parse_prompt",
            target="test",
            new_value="new_value",
        )
        
        # 执行（简化版本）
        result = await executor._execute_modification(record)
        
        assert result is not None


# =============================================================================
# Meta Intent Executor 测试
# =============================================================================


class TestMetaIntentExecutor:
    """测试元意图执行器"""
    
    @pytest.fixture
    def executor(self):
        """创建执行器"""
        registry = IntentPackageRegistry()
        return MetaIntentExecutor(registry=registry)
    
    def test_meta_intent_creation(self):
        """测试元意图创建"""
        intent = MetaIntent(
            type=MetaIntentType.REGISTER_CAPABILITY,
            target="test_capability",
            params={"name": "test"},
        )
        
        assert intent.type == MetaIntentType.REGISTER_CAPABILITY
        assert intent.status == "pending"
    
    def test_meta_intent_to_dict(self):
        """测试元意图序列化"""
        intent = MetaIntent(
            type=MetaIntentType.OPTIMIZE_PERFORMANCE,
            target="cache",
        )
        
        data = intent.to_dict()
        
        assert data["type"] == "optimize_performance"
        assert data["target"] == "cache"
    
    @pytest.mark.asyncio
    async def test_execute_register_capability(self, executor):
        """测试执行能力注册"""
        intent = MetaIntent(
            type=MetaIntentType.REGISTER_CAPABILITY,
            target="ar_renderer",
            params={
                "name": "ar_renderer",
                "description": "AR 渲染",
            },
        )
        
        result = await executor.execute(intent)
        
        assert result.status == "completed"
        assert result.result["capability"]["name"] == "ar_renderer"
    
    @pytest.mark.asyncio
    async def test_execute_register_intent_template(self, executor):
        """测试执行意图模板注册"""
        intent = MetaIntent(
            type=MetaIntentType.REGISTER_INTENT_TEMPLATE,
            target="compare_regions",
            params={
                "name": "compare_regions",
                "description": "对比区域",
                "parameters": [
                    {"name": "region1", "type": "string"},
                    {"name": "region2", "type": "string"},
                ],
            },
        )
        
        result = await executor.execute(intent)
        
        assert result.status == "completed"
    
    @pytest.mark.asyncio
    async def test_execute_optimize_performance(self, executor):
        """测试执行性能优化"""
        intent = MetaIntent(
            type=MetaIntentType.OPTIMIZE_PERFORMANCE,
            target="system",
            params={
                "actions": [
                    {"action": "increase_cache_size", "value": 5000},
                ]
            },
        )
        
        result = await executor.execute(intent)
        
        assert result.status == "completed"
        assert len(result.result["actions"]) == 1
    
    def test_get_history(self, executor):
        """测试获取执行历史"""
        # 执行几个元意图
        asyncio.run(executor.execute(MetaIntent(
            type=MetaIntentType.REGISTER_CAPABILITY,
            target="cap1",
            params={"name": "cap1"},
        )))
        
        history = executor.get_history(time_range="24h")
        assert len(history) >= 1
    
    def test_get_statistics(self, executor):
        """测试获取统计"""
        asyncio.run(executor.execute(MetaIntent(
            type=MetaIntentType.REGISTER_CAPABILITY,
            target="cap1",
            params={"name": "cap1"},
        )))
        
        stats = executor.get_statistics()
        
        assert stats["total_executions"] >= 1
        assert stats["completed"] >= 1


# =============================================================================
# Protocol Extender 测试
# =============================================================================


class TestProtocolSelfExtender:
    """测试协议自扩展器"""
    
    def test_detect_capability_gap(self):
        """测试检测能力缺口"""
        extender = ProtocolSelfExtender()
        
        gap = extender.detect_capability_gap(
            intent_text="用 AR 展示销售数据",
            available_capabilities=["data_loader", "chart_renderer"],
        )
        
        assert gap is not None
        assert "ar" in gap.capability_name.lower() or "render" in gap.capability_name.lower()
    
    def test_detect_no_gap(self):
        """测试没有能力缺口"""
        extender = ProtocolSelfExtender()
        
        gap = extender.detect_capability_gap(
            intent_text="查询销售数据",
            available_capabilities=["data_loader"],
        )
        
        assert gap is None
    
    def test_generate_extension_suggestion(self):
        """测试生成扩展建议"""
        extender = ProtocolSelfExtender()
        
        gap = extender.detect_capability_gap(
            intent_text="用 3D 展示数据",
            available_capabilities=[],
        )
        
        suggestion = extender.generate_extension_suggestion(gap)
        
        assert suggestion.suggestion_type == "register_capability"
        assert suggestion.params["name"] is not None
    
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
    
    def test_get_detected_gaps(self):
        """测试获取检测到的缺口"""
        extender = ProtocolSelfExtender()
        
        extender.detect_capability_gap("用 AR 展示", [])
        extender.detect_capability_gap("用 VR 展示", [])
        
        gaps = extender.get_detected_gaps()
        
        assert len(gaps) == 2


# =============================================================================
# Template Grower 测试
# =============================================================================


class TestIntentTemplateSelfGrower:
    """测试意图模板自生长器"""
    
    @pytest.fixture
    def grower(self):
        """创建自生长器"""
        graph = create_intent_graph()
        return IntentTemplateSelfGrower(intent_graph=graph)
    
    def test_record_intent(self, grower):
        """测试记录意图"""
        grower.record_intent(
            intent_text="对比华东和华南的销售",
            parameters={"region1": "华东", "region2": "华南"},
            success=True,
        )
        
        assert len(grower.miner.history) == 1
    
    def test_analyze_patterns(self, grower):
        """测试分析模式"""
        # 记录多个相似意图
        for i in range(10):
            grower.record_intent(
                intent_text=f"对比华东和华南的 Q{i+1}销售",
                parameters={"region1": "华东", "region2": "华南", "period": f"Q{i+1}"},
                success=True,
            )
        
        patterns = grower.miner.analyze_patterns(time_range="7d", min_frequency=5)
        
        assert len(patterns) >= 1
    
    def test_get_template_candidates(self, grower):
        """测试获取模板候选"""
        for i in range(10):
            grower.record_intent(
                intent_text=f"分析华东区 Q{i+1}销售",
                parameters={"region": "华东", "period": f"Q{i+1}"},
                success=True,
            )
        
        grower.miner.analyze_patterns()
        candidates = grower.miner.get_template_candidates(min_frequency=5)
        
        assert len(candidates) >= 1
    
    @pytest.mark.asyncio
    async def test_grow_from_history(self, grower):
        """测试从历史生长模板"""
        for i in range(10):
            grower.record_intent(
                intent_text=f"对比华东和华南的 Q{i+1}销售",
                parameters={"region1": "华东", "region2": "华南", "period": f"Q{i+1}"},
                success=True,
            )
        
        templates = await grower.grow_from_history(
            time_range="7d",
            min_frequency=5,
            auto_approve=True,
        )
        
        assert len(templates) >= 1
    
    def test_get_statistics(self, grower):
        """测试获取统计"""
        for i in range(5):
            grower.record_intent(
                intent_text=f"测试意图 {i}",
                parameters={"param": f"value_{i}"},
                success=True,
            )
        
        stats = grower.get_statistics()
        
        assert stats["total_history_entries"] == 5


# =============================================================================
# Self Modifying OS 测试
# =============================================================================


class TestSelfModifyingOS:
    """测试自修改 OS"""
    
    def test_os_creation(self):
        """测试 OS 创建"""
        os = SelfModifyingOS()
        
        assert os.instructions is not None
        assert len(os.components) == 0
    
    def test_define_instruction(self):
        """测试定义指令"""
        os = SelfModifyingOS()
        
        def test_handler(**kwargs):
            return {"status": "tested"}
        
        component = os.define_instruction("TEST_INSTR", test_handler, "测试指令")
        
        assert "TEST_INSTR" in os.instructions
        assert component.name == "TEST_INSTR"
        assert component.component_type == "instruction"
    
    def test_modify_compiler_rule(self):
        """测试修改编译器规则"""
        os = SelfModifyingOS()
        
        new_rule = {"strategy": "llm_v2"}
        component = os.modify_compiler_rule("intent_parse", new_rule)
        
        assert os.compiler_rules["intent_parse"] == new_rule
        assert component.component_type == "compiler_rule"
    
    def test_modify_executor_rule(self):
        """测试修改执行器规则"""
        os = SelfModifyingOS()
        
        new_rule = {"max_concurrent": 20}
        component = os.modify_executor_rule("task_scheduler", new_rule)
        
        assert os.executor_rules["task_scheduler"] == new_rule
    
    def test_get_statistics(self):
        """测试获取统计"""
        os = SelfModifyingOS()
        
        os.define_instruction("TEST1", lambda **kw: {})
        os.define_instruction("TEST2", lambda **kw: {})
        
        stats = os.get_statistics()
        
        assert stats["total_components"] == 2
        assert stats["instructions"] == 2


# =============================================================================
# Dual Memory OS 测试
# =============================================================================


class TestDualMemoryOS:
    """测试双内存 OS"""
    
    def test_os_creation(self):
        """测试 OS 创建"""
        os = DualMemoryOS()
        
        assert os.active_bank == os.left_bank
        assert os.left_bank.status == MemoryBankStatus.ACTIVE
        assert os.right_bank.status == MemoryBankStatus.STANDBY
    
    def test_get_active_bank(self):
        """测试获取活动内存库"""
        os = DualMemoryOS()
        
        active = os.get_active_bank()
        
        assert active == os.left_bank
        assert active.status == MemoryBankStatus.ACTIVE
    
    def test_get_standby_bank(self):
        """测试获取备用内存库"""
        os = DualMemoryOS()
        
        standby = os.get_standby_bank()
        
        assert standby == os.right_bank
        assert standby.status == MemoryBankStatus.STANDBY
    
    def test_start_upgrade(self):
        """测试开始升级"""
        os = DualMemoryOS()
        
        standby = os.start_upgrade()
        
        assert standby.status == MemoryBankStatus.UPGRADING
    
    def test_upgrade_instruction(self):
        """测试升级指令"""
        os = DualMemoryOS()
        os.start_upgrade()
        
        def new_handler(**kwargs):
            return {"status": "new"}
        
        os.upgrade_instruction("NEW_INSTR", new_handler)
        
        standby = os.get_standby_bank()
        assert "NEW_INSTR" in standby.instructions
    
    def test_upgrade_compiler_rule(self):
        """测试升级编译器规则"""
        os = DualMemoryOS()
        os.start_upgrade()
        
        new_rule = {"strategy": "v2"}
        os.upgrade_compiler_rule("parse_rule", new_rule)
        
        standby = os.get_standby_bank()
        assert standby.compiler_rules["parse_rule"] == new_rule
    
    def test_complete_upgrade(self):
        """测试完成升级"""
        os = DualMemoryOS()
        os.start_upgrade()
        
        # 升级
        os.upgrade_instruction("NEW_INSTR", lambda **kw: {})
        
        # 完成
        success = os.complete_upgrade()
        
        assert success is True
        assert os.active_bank == os.right_bank
    
    def test_upgrade_with_verification_failure(self):
        """测试升级失败回滚"""
        os = DualMemoryOS()
        os.start_upgrade()
        
        # 不添加必需指令，让验证失败
        # 移除基础指令来模拟失败
        standby = os.get_standby_bank()
        standby.instructions.clear()
        
        success = os.complete_upgrade()
        
        assert success is False
        assert os.active_bank == os.left_bank  # 应该回滚
    
    def test_force_switch(self):
        """测试强制切换"""
        os = DualMemoryOS()
        
        # 切换到右脑
        os.start_upgrade()
        os.upgrade_instruction("TEST", lambda **kw: {})
        os.complete_upgrade()
        
        assert os.active_bank == os.right_bank
        
        # 强制切回左脑
        success = os.force_switch()
        
        assert success is True
        assert os.active_bank == os.left_bank
    
    def test_get_status(self):
        """测试获取状态"""
        os = DualMemoryOS()
        
        status = os.get_status()
        
        assert "active_bank" in status
        assert "left_bank" in status
        assert "right_bank" in status
    
    def test_switch_history(self):
        """测试切换历史"""
        os = DualMemoryOS()
        
        # 多次切换
        os.start_upgrade()
        os.upgrade_instruction("TEST", lambda **kw: {})
        os.complete_upgrade()
        
        history = os.get_switch_history()
        
        assert len(history) >= 1


# =============================================================================
# Self Reproduction 测试（改进版）
# =============================================================================


class TestSelfReproduction:
    """测试自我繁殖（改进版）"""
    
    @pytest.fixture
    def reproducer(self):
        """创建繁殖器"""
        return SelfReproduction(instance_id="test_instance")
    
    def test_reproducer_creation(self, reproducer):
        """测试繁殖器创建"""
        assert reproducer.instance_id == "test_instance"
        assert reproducer._max_concurrent == 3
    
    @pytest.mark.asyncio
    async def test_discover_self(self, reproducer):
        """测试自我发现"""
        instance = await reproducer.discover_self()
        
        assert instance.id == "test_instance"
        assert instance.status == "running"
    
    def test_ethical_check_no_ethics(self, reproducer):
        """测试伦理检查（无伦理规则）"""
        plan = reproducer._create_test_plan()
        
        # 默认应该拒绝
        result = asyncio.run(reproducer._check_ethical_guidelines(plan))
        
        assert result is False
    
    def test_ethical_check_high_cost(self, reproducer):
        """测试伦理检查（高成本）"""
        plan = reproducer._create_test_plan(estimated_cost=250.0)
        
        # 高成本需要审批
        result = asyncio.run(reproducer._check_ethical_guidelines(plan))
        
        assert result is False
        assert plan.status == ReproductionStatus.WAITING_APPROVAL
    
    def test_calculate_cost(self, reproducer):
        """测试成本计算"""
        plan = reproducer._create_test_plan(
            type=ReproductionType.CLONE,
            target_region="us-west-2",
        )
        
        cost = reproducer._calculate_cost(plan)
        
        assert cost > 0
    
    @pytest.mark.asyncio
    async def test_acquire_reproduction_slot(self, reproducer):
        """测试获取繁殖槽位"""
        result = await reproducer._acquire_reproduction_slot()
        
        assert result is True
    
    def test_security_error(self):
        """测试安全异常"""
        with pytest.raises(SecurityError):
            raise SecurityError("Test security error")
    
    def test_audit_log_creation(self, reproducer):
        """测试审计日志创建"""
        asyncio.run(reproducer._log_audit("test_action", "Test details"))
        
        logs = reproducer.get_audit_logs()
        
        assert len(logs) == 1
        assert logs[0].action == "test_action"
    
    def test_get_statistics(self, reproducer):
        """测试获取统计"""
        stats = reproducer.get_statistics()
        
        assert "total_plans" in stats
        assert "active" in stats


# =============================================================================
# 集成测试
# =============================================================================


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_self_improvement_workflow(self):
        """测试完整的自我改进流程"""
        # 初始化
        registry = IntentPackageRegistry()
        executor = MetaIntentExecutor(registry=registry)
        extender = ProtocolSelfExtender()
        
        # 检测能力缺口
        gap = extender.detect_capability_gap(
            intent_text="用 AR 展示数据",
            available_capabilities=["data_loader"],
        )
        
        assert gap is not None
        
        # 生成元意图
        suggestion = extender.generate_extension_suggestion(gap)
        meta_intent = suggestion.to_meta_intent()
        
        # 执行
        meta_intent.approved_by = "auto_approved"
        result = await executor.execute(meta_intent)
        
        assert result.status == "completed"
    
    @pytest.mark.asyncio
    async def test_dual_memory_upgrade_workflow(self):
        """测试双内存升级流程"""
        os = DualMemoryOS()
        
        # 开始升级
        os.start_upgrade()
        
        # 升级多项内容
        os.upgrade_instruction("AR_RENDER", lambda **kw: {"status": "ar"})
        os.upgrade_compiler_rule("parse_v2", {"strategy": "llm"})
        os.upgrade_executor_rule("scheduler_v2", {"max": 20})
        
        # 完成升级
        success = os.complete_upgrade()
        
        assert success is True
        assert os.active_bank == os.right_bank
        
        # 验证新指令可用
        assert "AR_RENDER" in os.active_bank.instructions
    
    def test_self_modifying_os_workflow(self):
        """测试自修改 OS 流程"""
        os = SelfModifyingOS()
        
        # 定义新指令
        def ar_handler(**kwargs):
            return {"status": "rendered"}
        
        os.define_instruction("AR_RENDER", ar_handler)
        
        # 修改规则
        os.modify_compiler_rule("parse_prompt", {"template": "v2"})
        
        # 验证
        stats = os.get_statistics()
        
        assert stats["instructions"] == 4  # 基础 3 个 + 新增 1 个
        assert stats["compiler_rules"] == 1


# =============================================================================
# 性能基准测试
# =============================================================================


class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    @pytest.mark.asyncio
    async def test_meta_intent_execution_time(self):
        """测试元意图执行时间"""
        registry = IntentPackageRegistry()
        executor = MetaIntentExecutor(registry=registry)
        
        intent = MetaIntent(
            type=MetaIntentType.REGISTER_CAPABILITY,
            target="test_cap",
            params={"name": "test"},
        )
        
        import time
        start = time.time()
        await executor.execute(intent)
        elapsed = (time.time() - start) * 1000
        
        # 应该 < 100ms
        assert elapsed < 100
    
    @pytest.mark.asyncio
    async def test_concurrent_reproductions(self, reproducer=None):
        """测试并发繁殖"""
        if reproducer is None:
            reproducer = SelfReproduction(instance_id="bench_instance")
        
        import time
        start = time.time()
        
        # 尝试并发执行
        tasks = [
            reproducer._acquire_reproduction_slot()
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        elapsed = (time.time() - start) * 1000
        
        # 最多 3 个成功
        success_count = sum(1 for r in results if r)
        assert success_count <= 3
        
        # 时间应该 < 50ms
        assert elapsed < 50


# Helper method for SelfReproduction test
def _create_test_plan(self, type=ReproductionType.CLONE, estimated_cost=50.0, target_region="us-east-1"):
    """创建测试计划（辅助方法）"""
    return ReproductionPlan(
        type=type,
        source_instance="test",
        target_instance="test_target",
        target_region=target_region,
        estimated_cost=estimated_cost,
    )

# Add helper to SelfReproduction class
SelfReproduction._create_test_plan = _create_test_plan
