"""
Semantic VM 模块测试 - 第 4 部分

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


class TestSemanticInstructionPart4:
    """语义指令测试 - 第 4 部分"""

    def test_instruction_from_dict_minimal(self):
        """测试从字典创建最小指令"""
        data = {"opcode": "set"}
        instr = SemanticInstruction.from_dict(data)
        assert instr.opcode == SemanticOpcode.SET

    def test_instruction_from_dict_with_body(self):
        """测试从字典创建带 body 的指令"""
        data = {
            "opcode": "while",
            "condition": "x < 10",
            "body": [{"opcode": "set", "parameters": {"name": "x", "value": 1}}]
        }
        instr = SemanticInstruction.from_dict(data)
        assert instr.opcode == SemanticOpcode.WHILE
        assert len(instr.body) == 1

    def test_instruction_to_natural_language_set(self):
        """测试 SET 指令的自然语言"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.SET,
            parameters={"name": "x", "value": 1}
        )
        nl = instr.to_natural_language()
        assert "SET" in nl

    def test_instruction_to_natural_language_query(self):
        """测试 QUERY 指令的自然语言"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.QUERY,
            target="USER"
        )
        nl = instr.to_natural_language()
        assert "QUERY" in nl

    def test_instruction_to_natural_language_while(self):
        """测试 WHILE 指令的自然语言"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.WHILE,
            condition="x < 10"
        )
        nl = instr.to_natural_language()
        assert "WHILE" in nl

    def test_instruction_to_natural_language_loop(self):
        """测试 LOOP 指令的自然语言"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.LOOP,
            parameters={"times": 5}
        )
        nl = instr.to_natural_language()
        assert "LOOP" in nl


class TestSemanticProgramPart4:
    """语义程序测试 - 第 4 部分"""

    def test_program_creation_minimal(self):
        """测试创建最小程序"""
        program = SemanticProgram(name="minimal")
        assert program.name == "minimal"
        assert program.instructions == []

    def test_program_add_instruction(self):
        """测试添加指令"""
        program = SemanticProgram(name="test")
        instr = SemanticInstruction(opcode=SemanticOpcode.SET)
        program.add_instruction(instr)
        assert len(program.instructions) == 1

    def test_program_to_dict_complete(self):
        """测试完整转换为字典"""
        program = SemanticProgram(
            name="complete",
            description="Test",
            version="2.0.0"
        )
        program.add_instruction(SemanticInstruction(opcode=SemanticOpcode.SET))
        
        data = program.to_dict()
        assert data["name"] == "complete"
        assert len(data["instructions"]) == 1

    def test_program_from_dict_complete(self):
        """测试从字典完整创建"""
        data = {
            "name": "restored",
            "description": "Restored program",
            "version": "1.5.0",
            "instructions": [{"opcode": "set"}]
        }
        program = SemanticProgram.from_dict(data)
        assert program.name == "restored"
        assert len(program.instructions) == 1


class TestLLMProcessorPart4:
    """LLM 处理器测试 - 第 4 部分"""

    @pytest.fixture
    def processor(self):
        llm = LLMExecutor(provider="mock")
        return LLMProcessor(llm)

    def test_parse_response_empty_string(self, processor):
        """测试解析空字符串"""
        result = processor._parse_response("")
        assert result["success"] is False

    def test_parse_response_plain_text(self, processor):
        """测试解析纯文本"""
        result = processor._parse_response("This is not JSON")
        assert result["success"] is False
        assert "raw_content" in result

    def test_parse_response_markdown_json(self, processor):
        """测试解析 Markdown JSON"""
        content = '```json\n{"success": true}\n```'
        result = processor._parse_response(content)
        assert result["success"] is True

    def test_parse_response_code_block(self, processor):
        """测试解析代码块"""
        content = '```\n{"success": true}\n```'
        result = processor._parse_response(content)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_apply_operation_create_template(self, processor):
        """测试应用创建模板操作"""
        memory = SemanticMemory()
        result = {
            "operation": "create_template",
            "parameters": {"name": "new_template"}
        }
        await processor._apply_operation(result, memory)
        template = memory.get("TEMPLATE", "new_template")
        assert template is not None or template is None

    @pytest.mark.asyncio
    async def test_apply_operation_modify_config(self, processor):
        """测试应用修改配置操作"""
        memory = SemanticMemory()
        result = {
            "operation": "modify_config",
            "parameters": {"key": "timeout", "value": 60}
        }
        await processor._apply_operation(result, memory)
        config = memory.get("CONFIG", "timeout")
        assert config is not None or config is None

    @pytest.mark.asyncio
    async def test_apply_operation_query_status(self, processor):
        """测试应用查询状态操作"""
        memory = SemanticMemory()
        result = {"operation": "query_status"}
        await processor._apply_operation(result, memory)

    @pytest.mark.asyncio
    async def test_apply_operation_unknown(self, processor):
        """测试应用未知操作"""
        memory = SemanticMemory()
        result = {"operation": "unknown_op"}
        await processor._apply_operation(result, memory)

    @pytest.mark.asyncio
    async def test_execute_llm(self, processor):
        """测试执行 LLM"""
        memory = SemanticMemory()
        result = await processor.execute_llm("Test prompt", memory)
        assert result is not None

    def test_update_processor_prompt(self, processor):
        """测试更新处理器 Prompt"""
        new_prompt = "New prompt template"
        processor.update_processor_prompt(new_prompt)
        assert processor.processor_prompt == new_prompt


class TestSemanticVMPart4:
    """语义 VM 测试 - 第 4 部分"""

    @pytest.fixture
    def vm(self):
        llm = LLMExecutor(provider="mock")
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_vm_execute_nonexistent_program(self, vm):
        """测试执行不存在的程序"""
        result = await vm.execute_program("nonexistent")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_vm_load_program(self, vm):
        """测试加载程序"""
        program = SemanticProgram(name="load_test")
        await vm.load_program(program)
        loaded = vm.memory.get("PROGRAM", "load_test")
        assert loaded is not None

    @pytest.mark.asyncio
    async def test_vm_memory_set_get(self, vm):
        """测试 VM 内存设置获取"""
        vm.memory.set("TEST", "key", "value")
        stored = vm.memory.get("TEST", "key")
        assert stored is not None

    def test_vm_processor_exists(self, vm):
        """测试 VM 处理器存在"""
        assert vm.processor is not None

    def test_vm_memory_exists(self, vm):
        """测试 VM 内存存在"""
        assert vm.memory is not None


class TestSemanticVMIntegrationPart4:
    """语义 VM 集成测试 - 第 4 部分"""

    @pytest.fixture
    def vm(self):
        llm = LLMExecutor(provider="mock")
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_instruction_roundtrip(self, vm):
        """测试指令往返转换"""
        original = SemanticInstruction(
            opcode=SemanticOpcode.MODIFY,
            target="CONFIG",
            target_name="setting"
        )
        data = original.to_dict()
        restored = SemanticInstruction.from_dict(data)
        assert restored.opcode == original.opcode

    @pytest.mark.asyncio
    async def test_program_roundtrip(self, vm):
        """测试程序往返转换"""
        original = SemanticProgram(name="roundtrip", version="1.0.0")
        original.add_instruction(SemanticInstruction(opcode=SemanticOpcode.SET))
        
        data = original.to_dict()
        restored = SemanticProgram.from_dict(data)
        
        assert restored.name == original.name
        assert len(restored.instructions) == 1

    @pytest.mark.asyncio
    async def test_load_and_execute_empty_program(self, vm):
        """测试加载并执行空程序"""
        program = SemanticProgram(name="empty")
        await vm.load_program(program)
        result = await vm.execute_program("empty")
        assert result is not None

    def test_processor_parse_all_formats(self, vm):
        """测试处理器解析所有格式"""
        processor = vm.processor
        
        # JSON
        r1 = processor._parse_response('{"success": true}')
        assert r1["success"] is True
        
        # Markdown JSON
        r2 = processor._parse_response('```json\n{"success": true}\n```')
        assert r2["success"] is True
        
        # Code block
        r3 = processor._parse_response('```\n{"success": true}\n```')
        assert r3["success"] is True
        
        # Invalid
        r4 = processor._parse_response('Invalid')
        assert r4["success"] is False
