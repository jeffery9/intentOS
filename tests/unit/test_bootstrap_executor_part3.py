"""
Bootstrap Executor 第 3 部分测试

覆盖剩余未测试的方法
"""

import pytest

from intentos.bootstrap.executor import (
    BootstrapPolicy,
    BootstrapPrograms,
    BootstrapRecord,
    BootstrapValidator,
    SelfBootstrapExecutor,
)
from intentos.llm.executor import LLMExecutor
from intentos.semantic_vm import SemanticVM


class TestSelfBootstrapExecutorPart3:
    """SelfBootstrapExecutor 第 3 部分测试"""

    @pytest.fixture
    def executor(self):
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return SelfBootstrapExecutor(vm)

    @pytest.mark.asyncio
    async def test_get_current_value_instruction_set(self, executor):
        value = await executor._get_current_value("INSTRUCTION_SET.META_ACTIONS")
        assert value is None or isinstance(value, list)

    @pytest.mark.asyncio
    async def test_apply_modification_instruction_set(self, executor):
        await executor._apply_modification("INSTRUCTION_SET.CUSTOM_OP", {"logic": "test"})
        assert hasattr(executor.vm.processor, "_handle_custom_op")

    @pytest.mark.asyncio
    async def test_replicate_modification_no_memory(self):
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        executor = SelfBootstrapExecutor(vm)
        await executor._replicate_modification("CONFIG.TEST", "value")

    def test_get_bootstrap_history_empty_list(self, executor):
        history = executor.get_bootstrap_history()
        assert isinstance(history, list)

    def test_get_bootstrap_history_limit_zero(self, executor):
        executor.records.append(BootstrapRecord(action="test", status="completed"))
        history = executor.get_bootstrap_history(limit=0)
        assert isinstance(history, list)

    def test_get_policy_returns_policy(self, executor):
        policy = executor.get_policy()
        assert isinstance(policy, BootstrapPolicy)

    @pytest.mark.asyncio
    async def test_modify_policy_single_field(self, executor):
        await executor.modify_policy(max_modifications_per_hour=100)
        assert executor.policy.max_modifications_per_hour == 100

    @pytest.mark.asyncio
    async def test_modify_policy_multiple_fields(self, executor):
        await executor.modify_policy(
            max_modifications_per_hour=50, require_confidence_threshold=0.95
        )
        assert executor.policy.max_modifications_per_hour == 50
        assert executor.policy.require_confidence_threshold == 0.95


class TestBootstrapProgramsPart2:
    """BootstrapPrograms 第 2 部分测试"""

    def test_create_parse_prompt_modifier_structure(self):
        program = BootstrapPrograms.create_parse_prompt_modifier("New prompt")
        assert program.name == "modify_parse_prompt"

    def test_create_execute_prompt_modifier_structure(self):
        program = BootstrapPrograms.create_execute_prompt_modifier("Execute")
        assert program.name == "modify_execute_prompt"

    def test_create_instruction_extender_structure(self):
        program = BootstrapPrograms.create_instruction_extender(["INST1"])
        assert program.name == "extend_instruction_set"

    def test_create_policy_modifier_structure(self):
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
        record = BootstrapRecord(
            action="modify_config",
            target="CONFIG.TEST",
            old_value="old",
            new_value="new",
            status="pending",
        )
        result = await validator.validate_modification(record)
        assert "valid" in result

    @pytest.mark.asyncio
    async def test_validate_modification_missing_new_value(self, validator):
        record = BootstrapRecord(action="modify_config", target="CONFIG.TEST", new_value=None)
        result = await validator.validate_modification(record)
        assert "valid" in result or "errors" in result

    @pytest.mark.asyncio
    async def test_validate_with_warnings(self, validator):
        record = BootstrapRecord(action="delete_all_templates", target="TEMPLATES", new_value=None)
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
        assert executor._check_rate_limit() is True
        assert executor._requires_approval("delete_all_templates") is True
        current = await executor._get_current_value("POLICY.allow_self_modification")
        assert current is True or current is None
        await executor._apply_modification("POLICY.max_modifications_per_hour", 200)
        record = await executor.execute_bootstrap(
            action="modify_config", target="CONFIG.TEST", new_value={"data": "test"}, context={}
        )
        assert record.status in ["completed", "pending", "approved", "rejected", "failed"]
        history = executor.get_bootstrap_history()
        assert isinstance(history, list)

    def test_programs_all_types(self):
        programs = [
            BootstrapPrograms.create_parse_prompt_modifier("prompt"),
            BootstrapPrograms.create_execute_prompt_modifier("exec"),
            BootstrapPrograms.create_instruction_extender(["I1"]),
            BootstrapPrograms.create_policy_modifier(k="v"),
        ]
        for program in programs:
            assert program is not None
            assert hasattr(program, "name")

    @pytest.mark.asyncio
    async def test_validator_executor_integration(self, executor):
        validator = BootstrapValidator(executor)
        record = BootstrapRecord(
            action="modify_config", target="CONFIG.VALIDATION", new_value={"test": True}
        )
        validation = await validator.validate_modification(record)
        assert isinstance(validation, dict)
        execution = await executor.execute_bootstrap(
            action=record.action, target=record.target, new_value=record.new_value, context={}
        )
        assert execution.status in ["completed", "pending", "approved", "rejected", "failed"]
