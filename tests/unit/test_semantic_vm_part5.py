"""
Semantic VM 模块测试 - 第 5 部分

覆盖更多未测试的 VM 方法
"""

import pytest

from intentos.llm.executor import LLMExecutor
from intentos.semantic_vm import SemanticMemory
from intentos.semantic_vm.vm import (
    LLMProcessor,
    SemanticInstruction,
    SemanticOpcode,
    SemanticProgram,
    SemanticVM,
)


class TestSemanticInstructionPart5:
    """语义指令测试 - 第 5 部分"""

    def test_instruction_from_dict_with_all_fields(self):
        data = {
            "opcode": "set",
            "target": "VARIABLE",
            "target_name": "x",
            "parameters": {"value": 1},
            "condition": "x < 10",
            "body": [],
            "label": "loop_start",
            "jump_target": "loop_end",
            "line_number": 5,
        }
        instr = SemanticInstruction.from_dict(data)
        assert instr.opcode == SemanticOpcode.SET
        assert instr.target == "VARIABLE"
        assert instr.target_name == "x"
        assert instr.condition == "x < 10"
        assert instr.label == "loop_start"
        assert instr.jump_target == "loop_end"
        assert instr.line_number == 5

    def test_instruction_to_dict_with_all_fields(self):
        instr = SemanticInstruction(
            opcode=SemanticOpcode.SET,
            target="VARIABLE",
            target_name="y",
            parameters={"value": 2},
            condition="y < 20",
            label="start",
            jump_target="end",
            line_number=10,
        )
        data = instr.to_dict()
        assert data["opcode"] == "set"
        assert data["target"] == "VARIABLE"
        assert data["target_name"] == "y"
        assert data["condition"] == "y < 20"
        assert data["label"] == "start"
        assert data["jump_target"] == "end"
        assert data["line_number"] == 10


class TestSemanticProgramPart5:
    """语义程序测试 - 第 5 部分"""

    def test_program_add_multiple_instructions(self):
        program = SemanticProgram(name="multi")
        for i in range(5):
            program.add_instruction(
                SemanticInstruction(
                    opcode=SemanticOpcode.SET, parameters={"name": f"var_{i}", "value": i}
                )
            )
        assert len(program.instructions) == 5

    def test_program_from_dict_with_empty_instructions(self):
        data = {"name": "empty_prog", "description": "Empty program", "instructions": []}
        program = SemanticProgram.from_dict(data)
        assert program.name == "empty_prog"
        assert len(program.instructions) == 0

    def test_program_from_dict_with_multiple_instructions(self):
        data = {
            "name": "multi_prog",
            "instructions": [
                {"opcode": "set", "parameters": {"name": "a", "value": 1}},
                {"opcode": "set", "parameters": {"name": "b", "value": 2}},
                {"opcode": "set", "parameters": {"name": "c", "value": 3}},
            ],
        }
        program = SemanticProgram.from_dict(data)
        assert program.name == "multi_prog"
        assert len(program.instructions) == 3


class TestLLMProcessorPart5:
    """LLM 处理器测试 - 第 5 部分"""

    @pytest.fixture
    def processor(self):
        llm = LLMExecutor(provider="mock")
        return LLMProcessor(llm)

    def test_parse_response_with_nested_json(self, processor):
        content = '{"success": true, "data": {"nested": {"value": 42}}}'
        result = processor._parse_response(content)
        assert result["success"] is True
        assert result["data"]["nested"]["value"] == 42

    def test_parse_response_with_array(self, processor):
        content = '{"items": [1, 2, 3]}'
        result = processor._parse_response(content)
        assert result["items"] == [1, 2, 3]

    def test_parse_response_with_boolean(self, processor):
        content = '{"success": false, "error": "Failed"}'
        result = processor._parse_response(content)
        assert result["success"] is False
        assert result["error"] == "Failed"

    def test_parse_response_with_null(self, processor):
        content = '{"data": null}'
        result = processor._parse_response(content)
        assert result["data"] is None

    def test_parse_response_with_number(self, processor):
        content = '{"count": 42, "ratio": 3.14}'
        result = processor._parse_response(content)
        assert result["count"] == 42
        assert result["ratio"] == 3.14

    @pytest.mark.asyncio
    async def test_apply_operation_with_empty_result(self, processor):
        memory = SemanticMemory()
        result = {}
        await processor._apply_operation(result, memory)


class TestSemanticVMPart5:
    """语义 VM 测试 - 第 5 部分"""

    @pytest.fixture
    def vm(self):
        llm = LLMExecutor(provider="mock")
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_vm_execute_program_with_instructions(self, vm):
        program = SemanticProgram(name="with_instr")
        program.add_instruction(
            SemanticInstruction(opcode=SemanticOpcode.SET, parameters={"name": "test", "value": 1})
        )
        await vm.load_program(program)
        result = await vm.execute_program("with_instr")
        assert result is not None

    def test_vm_memory_operations(self, vm):
        vm.memory.set("TEMPLATE", "t1", "v1")
        vm.memory.set("TEMPLATE", "t2", "v2")

        v1 = vm.memory.get("TEMPLATE", "t1")
        v2 = vm.memory.get("TEMPLATE", "t2")

        assert v1 == "v1"
        assert v2 == "v2"

    def test_vm_processor_operations(self, vm):
        assert vm.processor is not None
        assert hasattr(vm.processor, "execute")
        assert hasattr(vm.processor, "execute_llm")


class TestSemanticVMIntegrationPart5:
    """语义 VM 集成测试 - 第 5 部分"""

    @pytest.fixture
    def vm(self):
        llm = LLMExecutor(provider="mock")
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_instruction_nested_body(self, vm):
        inner_instr = SemanticInstruction(
            opcode=SemanticOpcode.SET, parameters={"name": "inner", "value": 1}
        )
        outer_instr = SemanticInstruction(
            opcode=SemanticOpcode.WHILE, condition="x < 10", body=[inner_instr]
        )

        data = outer_instr.to_dict()
        restored = SemanticInstruction.from_dict(data)

        assert restored.opcode == SemanticOpcode.WHILE
        assert len(restored.body) == 1
        assert restored.body[0].opcode == SemanticOpcode.SET

    @pytest.mark.asyncio
    async def test_program_deep_copy(self, vm):
        original = SemanticProgram(name="original", version="1.0.0")
        original.add_instruction(SemanticInstruction(opcode=SemanticOpcode.SET))

        data = original.to_dict()
        copy1 = SemanticProgram.from_dict(data)
        copy2 = SemanticProgram.from_dict(copy1.to_dict())

        assert copy1.name == original.name
        assert copy2.name == original.name
        assert len(copy1.instructions) == 1
        assert len(copy2.instructions) == 1

    def test_processor_parse_complex_json(self, vm):
        processor = vm.processor

        complex_json = """
        {
            "success": true,
            "data": {
                "users": [
                    {"name": "Alice", "age": 30},
                    {"name": "Bob", "age": 25}
                ],
                "total": 2
            }
        }
        """
        result = processor._parse_response(complex_json)
        assert result["success"] is True
        assert len(result["data"]["users"]) == 2
        assert result["data"]["total"] == 2
