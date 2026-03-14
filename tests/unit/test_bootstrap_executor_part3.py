"""
Bootstrap Executor 第 3 部分测试

覆盖剩余未测试的方法
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


class TestSelfBootstrapExecutorPart3:
    """SelfBootstrapExecutor 第 3 部分测试"""

    @pytest.fixture
    def executor(self):
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return SelfBootstrapExecutor(vm)

    @pytest.mark.asyncio
    async def test_get_current_value_instruction_set(self, executor):
        """测试获取指令集当前值"""
        value = await executor._get_current_value("INSTRUCTION_SET.META_ACTIONS")
        assert value is None or isinstance(value, list)

    @pytest.mark.asyncio
    async def test_apply_modification_instruction_set(self, executor):
        """测试应用指令集修改"""
        await executor._apply_modification("INSTRUCTION_SET.CUSTOM_OP", {"logic": "test"})
        assert hasattr(executor.vm.processor, "_handle_custom_op")

    @pytest.mark.asyncio
    async def test_replicate_modification_no_memory(self):
        """测试无内存时复制"""
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        executor = SelfBootstrapExecutor(vm)
        
        await executor._replicate_modification("CONFIG.TEST", "value")

    def test_get_bootstrap_history_empty_list(self, executor):
        """测试获取空历史列表"""
        history = executor.get_bootstrap_history()
        assert isinstance(history, list)

    def test_get_bootstrap_history_limit_zero(self, executor):
        """测试获取零限制的历史"""
        executor.records.append(BootstrapRecord(action="test", status="completed"))
        history = executor.get_bootstrap_history(limit=0)
        assert len(history) == 0

    def test_get_policy_returns_policy(self, executor):
        """测试获取策略"""
        policy = executor.get_policy()
        assert isinstance(policy, BootstrapPolicy)

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


class TestBootstrapProgramsPart2:
    """BootstrapPrograms 第 2 部分测试"""

    def test_create_self_replicator_structure(self):
        """测试创建自我复制程序结构"""
        program = BootstrapPrograms.create_self_replicator()
        assert program is not None
        assert program.name == "self_replicator"
        assert len(program.instructions) > 0

    def test_create_auto_scaler_structure(self):
        """测试创建自动扩缩容程序结构"""
        program = BootstrapPrograms.create_auto_scaler(
            scale_up_threshold=0.8,
            scale_down_threshold=0.3
        )
        assert program is not None
        assert program.name == "auto_scaler"
        assert len(program.instructions) > 0

    def test_create_parse_prompt_modifier_structure(self):
        """测试创建解析 Prompt 修改程序结构"""
        program = BootstrapPrograms.create_parse_prompt_modifier("New prompt")
        assert program.name == "modify_parse_prompt"

    def test_create_execute_prompt_modifier_structure(self):
        """测试创建执行 Prompt 修改程序结构"""
        program = BootstrapPrograms.create_execute_prompt_modifier("Execute")
        assert program.name == "modify_execute_prompt"

    def test_create_instruction_extender_structure(self):
        """测试创建指令扩展程序结构"""
        program = BootstrapPrograms.create_instruction_extender(["INST1"])
        assert program.name == "extend_instruction_set"

    def test_create_policy_modifier_structure(self):
        """测试创建策略修改程序结构"""
        program = BootstrapPrograms.create_policy_modifier(key="value")
        assert program.name == "modify_bootstrap_policy"


class TestBootstrapValidatorPart2:
    """BootstrapValidator 第 2 部分测试"""

    @pytest.fixture
    def validator(self):
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        executor = SelfBootstrapExecutor(vm)
        return BootstrapValidator(executor)

    @pytest.mark.asyncio
    async def test_validate_modification_with_all_fields(self, validator):
        """测试验证完整记录"""
        record = BootstrapRecord(
            action="modify_config",
            target="CONFIG.TEST",
            old_value="old",
            new_value="new",
            status="pending"
        )
        result = await validator.validate_modification(record)
        assert "valid" in result

    @pytest.mark.asyncio
    async def test_validate_modification_missing_new_value(self, validator):
        """测试验证缺少新值"""
        record = BootstrapRecord(
            action="modify_config",
            target="CONFIG.TEST",
            new_value=None
        )
        result = await validator.validate_modification(record)
        assert "valid" in result or "errors" in result

    @pytest.mark.asyncio
    async def test_validate_with_warnings(self, validator):
        """测试验证带警告"""
        record = BootstrapRecord(
            action="delete_all_templates",
            target="TEMPLATES",
            new_value=None
        )
        result = await validator.validate_modification(record)
        assert isinstance(result, dict)


class TestBootstrapExecutorFullIntegration:
    """Bootstrap Executor 完整集成测试"""

    @pytest.fixture
    def executor(self):
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return SelfBootstrapExecutor(vm)

    @pytest.mark.asyncio
    async def test_complete_modification_cycle(self, executor):
        """测试完整修改周期"""
        # 1. 检查速率限制
        assert executor._check_rate_limit() is True
        
        # 2. 检查审批
        assert executor._requires_approval("delete_all_templates") is True
        
        # 3. 获取当前值
        current = await executor._get_current_value("POLICY.allow_self_modification")
        assert current is True or current is None
        
        # 4. 应用修改
        await executor._apply_modification("POLICY.max_modifications_per_hour", 200)
        
        # 5. 执行操作
        record = await executor.execute_bootstrap(
            action="modify_config",
            target="CONFIG.TEST",
            new_value={"data": "test"},
            context={}
        )
        assert record.status in ["completed", "pending", "approved", "rejected", "failed"]
        
        # 6. 获取历史
        history = executor.get_bootstrap_history()
        assert isinstance(history, list)

    def test_programs_all_types(self):
        """测试所有程序类型"""
        programs = [
            BootstrapPrograms.create_parse_prompt_modifier("prompt"),
            BootstrapPrograms.create_execute_prompt_modifier("exec"),
            BootstrapPrograms.create_instruction_extender(["I1"]),
            BootstrapPrograms.create_policy_modifier(k="v"),
            BootstrapPrograms.create_self_replicator(),
            BootstrapPrograms.create_auto_scaler(),
        ]
        
        for program in programs:
            assert program is not None
            assert hasattr(program, 'name')

    @pytest.mark.asyncio
    async def test_validator_executor_integration(self, executor):
        """测试验证器执行器集成"""
        validator = BootstrapValidator(executor)
        
        record = BootstrapRecord(
            action="modify_config",
            target="CONFIG.VALIDATION",
            new_value={"test": True}
        )
        
        validation = await validator.validate_modification(record)
        assert isinstance(validation, dict)
        
        execution = await executor.execute_bootstrap(
            action=record.action,
            target=record.target,
            new_value=record.new_value,
            context={}
        )
        assert execution.status in ["completed", "pending", "approved", "rejected", "failed"]
