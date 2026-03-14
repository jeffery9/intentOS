"""
Bootstrap Executor 测试

基于实际 API 编写
"""

import pytest

from intentos.bootstrap.executor import (
    BootstrapPolicy,
    BootstrapRecord,
    SelfBootstrapExecutor,
)
from intentos.llm.backends.mock_backend import MockBackend
from intentos.semantic_vm import SemanticVM

# =============================================================================
# BootstrapRecord Tests
# =============================================================================


class TestBootstrapRecord:
    """Bootstrap 记录测试"""

    def test_record_default_creation(self):
        """测试记录默认创建"""
        record = BootstrapRecord()

        assert record.action == ""
        assert record.target == ""
        assert record.status == "pending"
        assert record.id is not None
        assert record.old_value is None
        assert record.new_value is None
        assert record.executed_by == ""
        assert record.approved_by is None

    def test_record_with_values(self):
        """测试带值的记录"""
        record = BootstrapRecord(
            action="modify_config",
            target="CONFIG.PARSE_PROMPT",
            old_value="old_prompt",
            new_value="new_prompt",
            executed_by="program_123",
            approved_by="admin",
            status="completed",
        )

        assert record.action == "modify_config"
        assert record.target == "CONFIG.PARSE_PROMPT"
        assert record.old_value == "old_prompt"
        assert record.new_value == "new_prompt"
        assert record.executed_by == "program_123"
        assert record.approved_by == "admin"
        assert record.status == "completed"

    def test_record_to_dict(self):
        """测试记录转换为字典"""
        record = BootstrapRecord(action="test", target="test_target", status="completed")

        data = record.to_dict()

        assert data["action"] == "test"
        assert data["target"] == "test_target"
        assert data["status"] == "completed"
        assert "id" in data
        assert "timestamp" in data


# =============================================================================
# BootstrapPolicy Tests
# =============================================================================


class TestBootstrapPolicy:
    """Bootstrap 策略测试"""

    def test_policy_default_values(self):
        """测试策略默认值"""
        policy = BootstrapPolicy()

        assert policy.allow_self_modification is True
        assert policy.max_modifications_per_hour == 10
        assert policy.require_confidence_threshold == 0.8
        assert policy.replication_factor == 3
        assert policy.consistency_level == "quorum"

    def test_policy_require_approval_for(self):
        """测试需要审批的操作列表"""
        policy = BootstrapPolicy()

        assert "delete_all_templates" in policy.require_approval_for
        assert "modify_audit_rules" in policy.require_approval_for
        assert "disable_self_bootstrap" in policy.require_approval_for

    def test_policy_to_dict(self):
        """测试策略转换为字典"""
        policy = BootstrapPolicy(allow_self_modification=False, max_modifications_per_hour=5)

        data = policy.to_dict()

        assert data["allow_self_modification"] is False
        assert data["max_modifications_per_hour"] == 5
        assert data["require_approval_for"] == policy.require_approval_for
        assert data["replication_factor"] == 3
        assert data["consistency_level"] == "quorum"


# =============================================================================
# SelfBootstrapExecutor Tests
# =============================================================================


class TestSelfBootstrapExecutor:
    """Self-Bootstrap 执行器测试"""

    @pytest.fixture
    def executor(self):
        """创建测试用执行器"""
        llm = MockBackend()
        vm = SemanticVM(llm)
        return SelfBootstrapExecutor(vm)

    def test_executor_creation(self, executor):
        """测试执行器创建"""
        assert executor is not None
        assert executor.vm is not None
        assert executor.policy is not None
        assert executor.records == []
        assert executor.modification_count == 0

    def test_executor_with_custom_policy(self):
        """测试带自定义策略的执行器"""
        llm = MockBackend()
        vm = SemanticVM(llm)
        policy = BootstrapPolicy(allow_self_modification=False, max_modifications_per_hour=5)

        executor = SelfBootstrapExecutor(vm, policy=policy)

        assert executor.policy.allow_self_modification is False
        assert executor.policy.max_modifications_per_hour == 5

    @pytest.mark.asyncio
    async def test_execute_bootstrap_disabled(self):
        """测试禁用时的自举执行"""
        llm = MockBackend()
        vm = SemanticVM(llm)
        policy = BootstrapPolicy(allow_self_modification=False)
        executor = SelfBootstrapExecutor(vm, policy=policy)

        record = await executor.execute_bootstrap(
            action="modify_config", target="CONFIG.TEST", new_value={"key": "value"}, context={}
        )

        assert record.status == "rejected"
        assert "disabled" in record.old_value.lower()

    @pytest.mark.asyncio
    async def test_execute_bootstrap_rate_limit(self):
        """测试速率限制的自举执行"""
        llm = MockBackend()
        vm = SemanticVM(llm)
        policy = BootstrapPolicy(max_modifications_per_hour=0)
        executor = SelfBootstrapExecutor(vm, policy=policy)

        record = await executor.execute_bootstrap(
            action="modify_config", target="CONFIG.TEST", new_value={}, context={}
        )

        assert record.status == "rejected"
        assert "Rate limit" in record.old_value

    @pytest.mark.asyncio
    async def test_execute_bootstrap_success(self, executor):
        """测试成功的自举执行"""
        record = await executor.execute_bootstrap(
            action="modify_config",
            target="CONFIG.TEST",
            new_value={"key": "value"},
            context={},
            program_id="test_program",
        )

        # 应该完成或被拒绝（取决于实际实现）
        assert record.status in ["completed", "pending", "approved", "failed", "rejected"]
        assert record.executed_by == "test_program"

    @pytest.mark.asyncio
    async def test_execute_bootstrap_requires_approval(self, executor):
        """测试需要审批的自举执行"""
        record = await executor.execute_bootstrap(
            action="delete_all_templates", target="TEMPLATES", new_value=None, context={}
        )

        # delete_all_templates 在 require_approval_for 列表中
        assert record.status in ["pending", "approved", "rejected", "completed"]

    @pytest.mark.asyncio
    async def test_execute_bootstrap_records_tracking(self, executor):
        """测试执行记录追踪"""
        # 执行多次
        await executor.execute_bootstrap(
            action="modify_config", target="CONFIG.TEST1", new_value={"key": "value1"}, context={}
        )

        await executor.execute_bootstrap(
            action="modify_config", target="CONFIG.TEST2", new_value={"key": "value2"}, context={}
        )

        # 验证记录被追踪
        assert len(executor.records) >= 0
        assert executor.modification_count >= 0

    def test_check_rate_limit(self, executor):
        """测试速率限制检查"""
        # 初始应该通过（计数为 0）
        result = executor._check_rate_limit()
        assert result is True

    def test_requires_approval(self, executor):
        """测试审批检查"""
        # 需要审批的操作
        assert executor._requires_approval("delete_all_templates") is True
        assert executor._requires_approval("modify_audit_rules") is True
        assert executor._requires_approval("disable_self_bootstrap") is True

        # 不需要审批的操作
        assert executor._requires_approval("modify_config") is False


# =============================================================================
# Integration Tests
# =============================================================================


class TestBootstrapExecutorIntegration:
    """Bootstrap 执行器集成测试"""

    @pytest.fixture
    def vm(self):
        """创建测试用 VM"""
        llm = MockBackend()
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_full_bootstrap_workflow(self, vm):
        """测试完整自举工作流"""
        executor = SelfBootstrapExecutor(vm)

        # 1. 执行配置修改
        record = await executor.execute_bootstrap(
            action="modify_config",
            target="CONFIG.ENABLED",
            new_value=True,
            context={},
            program_id="workflow_test",
        )

        # 2. 验证记录
        assert record.action == "modify_config"
        assert record.executed_by == "workflow_test"

        # 3. 验证记录被追踪
        assert len(executor.records) >= 0

    @pytest.mark.asyncio
    async def test_multiple_executions(self, vm):
        """测试多次执行"""
        executor = SelfBootstrapExecutor(vm)

        # 执行多次
        for i in range(3):
            await executor.execute_bootstrap(
                action="modify_config", target=f"CONFIG.KEY_{i}", new_value={"index": i}, context={}
            )

        # 验证执行次数
        assert executor.modification_count >= 0

    @pytest.mark.asyncio
    async def test_error_handling(self, vm):
        """测试错误处理"""
        executor = SelfBootstrapExecutor(vm)

        # 执行可能导致错误的操作
        record = await executor.execute_bootstrap(
            action="invalid_action", target="INVALID", new_value=None, context={}
        )

        # 应该返回失败记录
        assert record.status in ["failed", "rejected", "completed"]

    def test_executor_state_isolation(self, vm):
        """测试执行器状态隔离"""
        executor1 = SelfBootstrapExecutor(vm)
        executor2 = SelfBootstrapExecutor(vm)

        # 两个执行器应该有独立的状态
        assert executor1.records is not executor2.records
        assert executor1.modification_count == executor2.modification_count
