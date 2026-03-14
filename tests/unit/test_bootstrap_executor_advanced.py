"""
Bootstrap Executor 高级测试

覆盖更多未测试的方法
"""

import pytest
from datetime import datetime, timedelta
from intentos.bootstrap.executor import (
    BootstrapRecord,
    BootstrapPolicy,
    SelfBootstrapExecutor,
    BootstrapPrograms,
    BootstrapValidator,
)
from intentos.semantic_vm import SemanticVM
from intentos.llm.executor import LLMExecutor


class TestSelfBootstrapExecutorAdvanced:
    """SelfBootstrapExecutor 高级测试"""

    @pytest.fixture
    def executor(self):
        """创建测试用执行器"""
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return SelfBootstrapExecutor(vm)

    def test_check_rate_limit_under_limit(self, executor):
        """测试速率限制内"""
        executor.modification_count = 5
        executor.policy.max_modifications_per_hour = 10
        executor.last_reset_time = datetime.now()
        
        result = executor._check_rate_limit()
        
        assert result is True

    def test_check_rate_limit_over_limit(self, executor):
        """测试超出速率限制"""
        executor.modification_count = 15
        executor.policy.max_modifications_per_hour = 10
        executor.last_reset_time = datetime.now()
        
        result = executor._check_rate_limit()
        
        assert result is False

    def test_check_rate_limit_reset(self, executor):
        """测试速率限制重置"""
        executor.modification_count = 15
        executor.policy.max_modifications_per_hour = 10
        executor.last_reset_time = datetime.now() - timedelta(hours=2)
        
        result = executor._check_rate_limit()
        
        # 应该重置计数器并允许
        assert result is True
        assert executor.modification_count == 0

    def test_requires_approval_for_delete_all(self, executor):
        """测试删除所有需要审批"""
        result = executor._requires_approval("delete_all_templates")
        
        assert result is True

    def test_requires_approval_for_modify_audit(self, executor):
        """测试修改审计需要审批"""
        result = executor._requires_approval("modify_audit_rules")
        
        assert result is True

    def test_requires_approval_for_disable_bootstrap(self, executor):
        """测试禁用自举需要审批"""
        result = executor._requires_approval("disable_self_bootstrap")
        
        assert result is True

    def test_requires_approval_for_normal_action(self, executor):
        """测试普通操作不需要审批"""
        result = executor._requires_approval("modify_config")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_current_value_policy(self, executor):
        """测试获取策略当前值"""
        value = await executor._get_current_value("POLICY.allow_self_modification")
        
        assert value is True

    @pytest.mark.asyncio
    async def test_get_current_value_policy_nonexistent(self, executor):
        """测试获取不存在的策略值"""
        value = await executor._get_current_value("POLICY.nonexistent_field")
        
        assert value is None

    @pytest.mark.asyncio
    async def test_get_current_value_unknown_target(self, executor):
        """测试获取未知目标值"""
        value = await executor._get_current_value("UNKNOWN.TARGET")
        
        assert value is None

    @pytest.mark.asyncio
    async def test_apply_modification_policy(self, executor):
        """测试应用策略修改"""
        await executor._apply_modification("POLICY.max_modifications_per_hour", 50)
        
        assert executor.policy.max_modifications_per_hour == 50

    @pytest.mark.asyncio
    async def test_apply_modification_policy_nonexistent_field(self, executor):
        """测试应用不存在的策略字段"""
        # 不应该抛出异常
        await executor._apply_modification("POLICY.nonexistent_field", "value")

    @pytest.mark.asyncio
    async def test_replicate_modification_no_distributed_memory(self, executor):
        """测试无分布式内存时复制修改"""
        # 不应该抛出异常
        await executor._replicate_modification("CONFIG.TEST", "value")

    def test_get_bootstrap_history_empty(self, executor):
        """测试获取空历史"""
        history = executor.get_bootstrap_history()
        
        assert history == []

    def test_get_bootstrap_history_with_records(self, executor):
        """测试获取有记录的历史"""
        record = BootstrapRecord(action="test", status="completed")
        executor.records.append(record)
        
        history = executor.get_bootstrap_history()
        
        assert len(history) == 1
        assert history[0].action == "test"

    def test_get_bootstrap_history_with_limit(self, executor):
        """测试获取带限制的历史"""
        for i in range(10):
            executor.records.append(BootstrapRecord(action=f"test_{i}", status="completed"))
        
        history = executor.get_bootstrap_history(limit=5)
        
        assert len(history) == 5

    def test_get_bootstrap_history_filter_by_action(self, executor):
        """测试按动作过滤历史"""
        executor.records.append(BootstrapRecord(action="type_a", status="completed"))
        executor.records.append(BootstrapRecord(action="type_b", status="completed"))
        executor.records.append(BootstrapRecord(action="type_a", status="completed"))
        
        history = executor.get_bootstrap_history(action="type_a")
        
        assert len(history) == 2
        assert all(r.action == "type_a" for r in history)

    def test_get_policy(self, executor):
        """测试获取策略"""
        policy = executor.get_policy()
        
        assert policy is not None
        assert policy == executor.policy

    @pytest.mark.asyncio
    async def test_modify_policy_single_field(self, executor):
        """测试修改单个策略字段"""
        await executor.modify_policy(max_modifications_per_hour=100)
        
        assert executor.policy.max_modifications_per_hour == 100

    @pytest.mark.asyncio
    async def test_modify_policy_multiple_fields(self, executor):
        """测试修改多个策略字段"""
        await executor.modify_policy(
            max_modifications_per_hour=50,
            require_confidence_threshold=0.95
        )
        
        assert executor.policy.max_modifications_per_hour == 50
        assert executor.policy.require_confidence_threshold == 0.95

    @pytest.mark.asyncio
    async def test_modify_policy_unknown_field(self, executor):
        """测试修改未知策略字段"""
        # 不应该抛出异常
        await executor.modify_policy(unknown_field="value")


# =============================================================================
# BootstrapPrograms Tests
# =============================================================================

class TestBootstrapPrograms:
    """BootstrapPrograms 测试"""

    def test_create_parse_prompt_modifier(self):
        """测试创建解析 Prompt 修改程序"""
        program = BootstrapPrograms.create_parse_prompt_modifier("New prompt")
        
        assert program is not None
        assert program.name == "modify_parse_prompt"

    def test_create_execute_prompt_modifier(self):
        """测试创建执行 Prompt 修改程序"""
        program = BootstrapPrograms.create_execute_prompt_modifier("New execute prompt")
        
        assert program is not None
        assert program.name == "modify_execute_prompt"

    def test_create_instruction_extender(self):
        """测试创建指令扩展程序"""
        program = BootstrapPrograms.create_instruction_extender(["INST1", "INST2"])
        
        assert program is not None
        assert program.name == "extend_instruction_set"

    def test_create_policy_modifier(self):
        """测试创建策略修改程序"""
        program = BootstrapPrograms.create_policy_modifier(
            max_modifications_per_hour=50,
            require_confidence_threshold=0.9
        )
        
        assert program is not None
        assert program.name == "modify_bootstrap_policy"


# =============================================================================
# BootstrapValidator Tests
# =============================================================================

class TestBootstrapValidatorAdvanced:
    """BootstrapValidator 高级测试"""

    @pytest.fixture
    def validator(self):
        """创建测试用验证器"""
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        executor = SelfBootstrapExecutor(vm)
        return BootstrapValidator(executor)

    @pytest.mark.asyncio
    async def test_validate_modification_valid_record(self, validator):
        """测试验证有效记录"""
        record = BootstrapRecord(
            action="modify_config",
            target="CONFIG.TEST",
            new_value={"key": "value"},
            status="pending"
        )
        
        result = await validator.validate_modification(record)
        
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "suggestions" in result

    @pytest.mark.asyncio
    async def test_validate_modification_empty_action(self, validator):
        """测试验证空动作"""
        record = BootstrapRecord(
            action="",
            target="CONFIG.TEST",
            new_value={}
        )
        
        result = await validator.validate_modification(record)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_modification_empty_target(self, validator):
        """测试验证空目标"""
        record = BootstrapRecord(
            action="modify_config",
            target="",
            new_value={}
        )
        
        result = await validator.validate_modification(record)
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_modification_dangerous_action(self, validator):
        """测试验证危险动作"""
        record = BootstrapRecord(
            action="delete_all",
            target="TEMPLATES",
            new_value=None
        )
        
        result = await validator.validate_modification(record)
        
        # 应该有警告
        assert len(result["warnings"]) > 0 or len(result["errors"]) > 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestBootstrapExecutorFullIntegration:
    """Bootstrap Executor 完整集成测试"""

    @pytest.fixture
    def executor(self):
        """创建测试用执行器"""
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return SelfBootstrapExecutor(vm)

    @pytest.mark.asyncio
    async def test_full_modification_workflow(self, executor):
        """测试完整修改工作流"""
        # 1. 检查速率限制
        assert executor._check_rate_limit() is True
        
        # 2. 检查审批要求
        assert executor._requires_approval("delete_all_templates") is True
        assert executor._requires_approval("modify_config") is False
        
        # 3. 获取当前策略值
        current = await executor._get_current_value("POLICY.allow_self_modification")
        assert current is True
        
        # 4. 应用策略修改
        await executor._apply_modification("POLICY.max_modifications_per_hour", 200)
        assert executor.policy.max_modifications_per_hour == 200
        
        # 5. 执行自举操作
        record = await executor.execute_bootstrap(
            action="modify_config",
            target="CONFIG.TEST",
            new_value={"data": "test"},
            context={}
        )
        
        assert record.status in ["completed", "pending", "approved", "rejected", "failed"]
        
        # 6. 获取历史
        history = executor.get_bootstrap_history()
        assert len(history) >= 1
        
        # 7. 修改策略
        await executor.modify_policy(require_confidence_threshold=0.99)
        assert executor.policy.require_confidence_threshold == 0.99

    def test_programs_creation_and_usage(self):
        """测试程序创建和使用"""
        # 创建各种程序
        parse_modifier = BootstrapPrograms.create_parse_prompt_modifier("New prompt")
        execute_modifier = BootstrapPrograms.create_execute_prompt_modifier("Execute")
        extender = BootstrapPrograms.create_instruction_extender(["INST"])
        policy_modifier = BootstrapPrograms.create_policy_modifier(key="value")
        
        # 验证程序创建
        assert parse_modifier.name == "modify_parse_prompt"
        assert execute_modifier.name == "modify_execute_prompt"
        assert extender.name == "extend_instruction_set"
        assert policy_modifier.name == "modify_bootstrap_policy"
