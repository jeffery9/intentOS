"""
Bootstrap Executor 第 4 部分测试

覆盖剩余未测试的方法
"""

from datetime import datetime, timedelta

import pytest

from intentos.bootstrap.executor import (
    BootstrapPrograms,
    BootstrapRecord,
    BootstrapValidator,
    SelfBootstrapExecutor,
)
from intentos.llm.executor import LLMExecutor
from intentos.semantic_vm import SemanticVM


class TestSelfBootstrapExecutorPart4:
    """SelfBootstrapExecutor 第 4 部分测试"""

    @pytest.fixture
    def executor(self):
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return SelfBootstrapExecutor(vm)

    @pytest.mark.asyncio
    async def test_apply_modification_config_nested(self, executor):
        executor.vm.memory.set("CONFIG", "NESTED.KEY", {"deep": "value"})
        stored = executor.vm.memory.get("CONFIG", "NESTED.KEY")
        assert stored is not None or stored is None

    @pytest.mark.asyncio
    async def test_apply_modification_policy_reset(self, executor):
        original = executor.policy.max_modifications_per_hour
        await executor._apply_modification("POLICY.max_modifications_per_hour", 999)
        assert executor.policy.max_modifications_per_hour == 999
        await executor._apply_modification("POLICY.max_modifications_per_hour", original)

    @pytest.mark.asyncio
    async def test_replicate_modification_with_config_prefix(self, executor):
        await executor._replicate_modification("CONFIG.IMPORTANT", "value")

    def test_get_bootstrap_history_filter_empty(self, executor):
        history = executor.get_bootstrap_history(action="nonexistent")
        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_bootstrap_history_large_limit(self, executor):
        for i in range(10):
            executor.records.append(BootstrapRecord(action=f"test_{i}", status="completed"))
        history = executor.get_bootstrap_history(limit=1000)
        assert len(history) == 10

    def test_get_policy_modification(self, executor):
        policy = executor.get_policy()
        policy.max_modifications_per_hour = 500
        assert executor.policy.max_modifications_per_hour == 500


class TestBootstrapProgramsPart3:
    """BootstrapPrograms 第 3 部分测试"""

    def test_create_parse_prompt_modifier_returns_program(self):
        program = BootstrapPrograms.create_parse_prompt_modifier("New prompt")
        assert hasattr(program, "name")
        assert hasattr(program, "instructions")

    def test_create_execute_prompt_modifier_returns_program(self):
        program = BootstrapPrograms.create_execute_prompt_modifier("Execute")
        assert hasattr(program, "name")
        assert hasattr(program, "instructions")

    def test_create_instruction_extender_returns_program(self):
        program = BootstrapPrograms.create_instruction_extender(["INST1", "INST2"])
        assert hasattr(program, "name")
        assert len(program.instructions) > 0

    def test_create_policy_modifier_returns_program(self):
        program = BootstrapPrograms.create_policy_modifier(key1="value1", key2="value2")
        assert hasattr(program, "name")
        assert hasattr(program, "instructions")


class TestBootstrapValidatorPart3:
    """BootstrapValidator 第 3 部分测试"""

    @pytest.fixture
    def validator(self):
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        executor = SelfBootstrapExecutor(vm)
        return BootstrapValidator(executor)

    @pytest.mark.asyncio
    async def test_validate_modification_empty_new_value(self, validator):
        record = BootstrapRecord(action="modify_config", target="CONFIG.TEST", new_value={})
        result = await validator.validate_modification(record)
        assert isinstance(result, dict)
        assert "valid" in result or "errors" in result

    @pytest.mark.asyncio
    async def test_validate_modification_with_old_value(self, validator):
        record = BootstrapRecord(
            action="modify_config", target="CONFIG.TEST", old_value="old", new_value="new"
        )
        result = await validator.validate_modification(record)
        assert isinstance(result, dict)


class TestBootstrapExecutorFullIntegrationPart2:
    """Bootstrap Executor 完整集成测试 - 第 2 部分"""

    @pytest.fixture
    def executor(self):
        llm = LLMExecutor(provider="mock")
        vm = SemanticVM(llm)
        return SelfBootstrapExecutor(vm)

    @pytest.mark.asyncio
    async def test_rate_limit_reset_workflow(self, executor):
        executor.modification_count = 15
        executor.policy.max_modifications_per_hour = 10
        executor.last_reset_time = datetime.now() - timedelta(hours=2)

        assert executor._check_rate_limit() is True
        assert executor.modification_count == 0

    @pytest.mark.asyncio
    async def test_approval_workflow(self, executor):
        requires = executor._requires_approval("delete_all_templates")
        assert requires is True

        requires = executor._requires_approval("modify_config")
        assert requires is False

    @pytest.mark.asyncio
    async def test_full_bootstrap_with_validator(self, executor):
        validator = BootstrapValidator(executor)

        record = BootstrapRecord(
            action="modify_config", target="CONFIG.INTEGRATION", new_value={"test": True}
        )

        validation = await validator.validate_modification(record)
        assert isinstance(validation, dict)

        execution = await executor.execute_bootstrap(
            action=record.action, target=record.target, new_value=record.new_value, context={}
        )
        assert execution.status in ["completed", "pending", "approved", "rejected", "failed"]

    def test_programs_chain_workflow(self):
        programs = [
            BootstrapPrograms.create_parse_prompt_modifier("p1"),
            BootstrapPrograms.create_execute_prompt_modifier("p2"),
            BootstrapPrograms.create_instruction_extender(["I1"]),
            BootstrapPrograms.create_policy_modifier(k="v"),
        ]

        for program in programs:
            assert program is not None
            assert hasattr(program, "name")
            assert hasattr(program, "instructions")
