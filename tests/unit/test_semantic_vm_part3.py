"""
Semantic VM 模块测试 - 第 3 部分

覆盖更多未测试的 VM 方法
"""

import pytest
from intentos.semantic_vm.vm import (
    SemanticInstruction,
    SemanticProgram,
    SemanticVM,
    LLMProcessor,
    SemanticOpcode,
)
from intentos.semantic_vm import SemanticMemory
from intentos.llm.executor import LLMExecutor


class TestSemanticInstructionPart3:
    """语义指令测试 - 第 3 部分"""

    def test_instruction_from_dict_minimal(self):
        data = {"opcode": "set"}
        instr = SemanticInstruction.from_dict(data)
        assert instr.opcode == SemanticOpcode.SET

    def test_instruction_from_dict_with_body(self):
        data = {
            "opcode": "while",
            "condition": "x < 10",
            "body": [{"opcode": "set", "parameters": {"name": "x", "value": 1}}]
        }
        instr = SemanticInstruction.from_dict(data)
        assert instr.opcode == SemanticOpcode.WHILE
        assert len(instr.body) == 1

    def test_instruction_to_natural_language_delete(self):
        instr = SemanticInstruction(opcode=SemanticOpcode.DELETE, target="TEMPLATE", target_name="old")
        nl = instr.to_natural_language()
        assert "DELETE" in nl

    def test_instruction_to_natural_language_if(self):
        instr = SemanticInstruction(opcode=SemanticOpcode.IF, condition="x > 0")
        nl = instr.to_natural_language()
        assert "IF" in nl

    def test_instruction_to_natural_language_jump(self):
        instr = SemanticInstruction(opcode=SemanticOpcode.JUMP, jump_target="label_1")
        nl = instr.to_natural_language()
        assert "JUMP" in nl


class TestSemanticProgramPart3:
    """语义程序测试 - 第 3 部分"""

    def test_program_from_dict_minimal(self):
        data = {"name": "minimal_prog"}
        program = SemanticProgram.from_dict(data)
        assert program.name == "minimal_prog"
        assert program.instructions == []

    def test_program_to_dict_with_version(self):
        program = SemanticProgram(name="versioned", version="3.0.0")
        data = program.to_dict()
        assert data["version"] == "3.0.0"


class TestLLMProcessorPart3:
    """LLM 处理器测试 - 第 3 部分"""

    @pytest.fixture
    def processor(self):
        llm = LLMExecutor(provider="mock")
        return LLMProcessor(llm)

    def test_parse_response_empty(self, processor):
        result = processor._parse_response("")
        assert result["success"] is False

    def test_parse_response_plain_text(self, processor):
        result = processor._parse_response("This is plain text")
        assert result["success"] is False
        assert "raw_content" in result

    def test_parse_response_partial_json(self, processor):
        content = '''Some text before
```json
{"success": true}
```
Some text after'''
        result = processor._parse_response(content)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_apply_operation_unknown(self, processor):
        memory = SemanticMemory()
        result = {"operation": "unknown_operation", "parameters": {}}
        await processor._apply_operation(result, memory)

    def test_update_processor_prompt_custom(self, processor):
        new_prompt = "Custom prompt template"
        processor.update_processor_prompt(new_prompt)
        assert "Custom prompt" in processor.processor_prompt


class TestSemanticVMPart3:
    """语义 VM 测试 - 第 3 部分"""

    @pytest.fixture
    def vm(self):
        llm = LLMExecutor(provider="mock")
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_vm_execute_program_not_loaded(self, vm):
        result = await vm.execute_program("nonexistent")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_vm_load_and_execute_empty_program(self, vm):
        program = SemanticProgram(name="empty")
        await vm.load_program(program)
        result = await vm.execute_program("empty")
        assert result is not None

    def test_vm_memory_access(self, vm):
        assert vm.memory is not None
        assert isinstance(vm.memory, SemanticMemory)

    def test_vm_processor_access(self, vm):
        assert vm.processor is not None


class TestSemanticVMIntegrationPart3:
    """语义 VM 集成测试 - 第 3 部分"""

    @pytest.fixture
    def vm(self):
        llm = LLMExecutor(provider="mock")
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_instruction_lifecycle(self, vm):
        instr = SemanticInstruction(opcode=SemanticOpcode.SET, parameters={"name": "x", "value": 1})
        data = instr.to_dict()
        restored = SemanticInstruction.from_dict(data)
        nl = instr.to_natural_language()
        assert restored.opcode == instr.opcode
        assert nl is not None

    @pytest.mark.asyncio
    async def test_program_lifecycle(self, vm):
        program = SemanticProgram(name="lifecycle", description="Lifecycle test")
        program.add_instruction(SemanticInstruction(opcode=SemanticOpcode.SET, parameters={"name": "test", "value": 1}))
        data = program.to_dict()
        restored = SemanticProgram.from_dict(data)
        await vm.load_program(restored)
        assert restored.name == program.name
        assert len(restored.instructions) == 1

    def test_processor_parse_response_formats(self, vm):
        processor = vm.processor
        json_result = processor._parse_response('{"success": true}')
        assert json_result["success"] is True
        md_result = processor._parse_response('```json\n{"success": true}\n```')
        assert md_result["success"] is True
        code_result = processor._parse_response('```\n{"success": true}\n```')
        assert code_result["success"] is True
        invalid_result = processor._parse_response('Invalid JSON')
        assert invalid_result["success"] is False
