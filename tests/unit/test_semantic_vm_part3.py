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


# =============================================================================
# SemanticInstruction Tests - Part 3
# =============================================================================

class TestSemanticInstructionPart3:
    """语义指令测试 - 第 3 部分"""

    def test_instruction_from_dict_with_distributed_opcode(self):
        """测试从字典创建带分布式操作码的指令"""
        data = {
            "opcode": "replicate",  # 分布式操作码
            "target": "PROGRAM",
            "target_name": "test"
        }
        
        instr = SemanticInstruction.from_dict(data)
        
        assert instr.target == "PROGRAM"
        assert instr.target_name == "test"

    def test_instruction_from_dict_with_custom_opcode(self):
        """测试从字典创建带自定义操作码的指令"""
        data = {
            "opcode": "CUSTOM_OP",
            "target": "TEST"
        }
        
        instr = SemanticInstruction.from_dict(data)
        
        assert instr.opcode == "CUSTOM_OP"

    def test_instruction_to_natural_language_delete(self):
        """测试转换为自然语言 - DELETE"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.DELETE,
            target="TEMPLATE",
            target_name="old_template"
        )
        
        nl = instr.to_natural_language()
        
        assert "DELETE" in nl

    def test_instruction_to_natural_language_if(self):
        """测试转换为自然语言 - IF"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.IF,
            condition="x > 0"
        )
        
        nl = instr.to_natural_language()
        
        assert "IF" in nl

    def test_instruction_to_natural_language_jump(self):
        """测试转换为自然语言 - JUMP"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.JUMP,
            jump_target="label_1"
        )
        
        nl = instr.to_natural_language()
        
        assert "JUMP" in nl

    def test_instruction_to_natural_language_define_function(self):
        """测试转换为自然语言 - DEFINE_FUNCTION"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.DEFINE_FUNCTION,
            target_name="my_function"
        )
        
        nl = instr.to_natural_language()
        
        # 应该返回某种字符串
        assert nl is not None
        assert len(nl) > 0


# =============================================================================
# SemanticProgram Tests - Part 3
# =============================================================================

class TestSemanticProgramPart3:
    """语义程序测试 - 第 3 部分"""

    def test_program_from_dict_minimal(self):
        """测试从字典创建最小程序"""
        data = {
            "name": "minimal_prog"
        }
        
        program = SemanticProgram.from_dict(data)
        
        assert program.name == "minimal_prog"
        assert program.description == ""
        assert program.instructions == []

    def test_program_to_dict_with_version(self):
        """测试程序转换为字典带版本"""
        program = SemanticProgram(
            name="versioned",
            version="3.0.0"
        )
        
        data = program.to_dict()
        
        assert data["version"] == "3.0.0"


# =============================================================================
# LLMProcessor Tests - Part 3
# =============================================================================

class TestLLMProcessorPart3:
    """LLM 处理器测试 - 第 3 部分"""

    @pytest.fixture
    def processor(self):
        """创建测试用处理器"""
        llm = LLMExecutor(provider="mock")
        return LLMProcessor(llm)

    def test_parse_response_empty(self, processor):
        """测试解析空响应"""
        result = processor._parse_response("")
        
        assert result["success"] is False
        assert "解析失败" in result["error"]

    def test_parse_response_plain_text(self, processor):
        """测试解析纯文本响应"""
        content = "This is plain text, not JSON"
        
        result = processor._parse_response(content)
        
        assert result["success"] is False
        assert result["raw_content"] == content

    def test_parse_response_partial_json(self, processor):
        """测试解析部分 JSON"""
        content = '''Some text before
```json
{"success": true}
```
Some text after'''
        
        result = processor._parse_response(content)
        
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_apply_operation_unknown(self, processor):
        """测试应用未知操作"""
        memory = SemanticMemory()
        
        result = {
            "operation": "unknown_operation",
            "parameters": {}
        }
        
        # 不应该抛出异常
        await processor._apply_operation(result, memory)

    def test_update_processor_prompt_custom(self, processor):
        """测试更新自定义处理器 Prompt"""
        new_prompt = "Custom prompt template with {instruction_nl}"
        
        processor.update_processor_prompt(new_prompt)
        
        assert "Custom prompt" in processor.processor_prompt


# =============================================================================
# SemanticVM Tests - Part 3
# =============================================================================

class TestSemanticVMPart3:
    """语义 VM 测试 - 第 3 部分"""

    @pytest.fixture
    def vm(self):
        """创建测试用 VM"""
        llm = LLMExecutor(provider="mock")
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_vm_execute_program_not_loaded(self, vm):
        """测试执行未加载的程序"""
        # 程序未加载，应该失败
        result = await vm.execute_program("nonexistent")
        
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_vm_load_and_execute_empty_program(self, vm):
        """测试加载并执行空程序"""
        program = SemanticProgram(name="empty")
        
        await vm.load_program(program)
        result = await vm.execute_program("empty")
        
        assert result is not None

    def test_vm_memory_access(self, vm):
        """测试 VM 内存访问"""
        # 验证内存对象存在
        assert vm.memory is not None
        assert isinstance(vm.memory, SemanticMemory)
        
        # 设置和获取内存
        vm.memory.set("TEMPLATE", "test", {"data": "value"})
        stored = vm.memory.get("TEMPLATE", "test")
        
        assert stored is not None

    def test_vm_processor_access(self, vm):
        """测试 VM 处理器访问"""
        assert vm.processor is not None
        assert isinstance(vm.processor, LLMProcessor)


# =============================================================================
# Integration Tests
# =============================================================================

class TestSemanticVMIntegrationPart3:
    """语义 VM 集成测试 - 第 3 部分"""

    @pytest.fixture
    def vm(self):
        """创建测试用 VM"""
        llm = LLMExecutor(provider="mock")
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_instruction_lifecycle(self, vm):
        """测试指令生命周期"""
        # 1. 创建指令
        instr = SemanticInstruction(
            opcode=SemanticOpcode.SET,
            parameters={"name": "x", "value": 1}
        )
        
        # 2. 转换为字典
        data = instr.to_dict()
        
        # 3. 从字典创建
        restored = SemanticInstruction.from_dict(data)
        
        # 4. 转换为自然语言
        nl = instr.to_natural_language()
        
        assert restored.opcode == instr.opcode
        assert nl is not None

    @pytest.mark.asyncio
    async def test_program_lifecycle(self, vm):
        """测试程序生命周期"""
        # 1. 创建程序
        program = SemanticProgram(
            name="lifecycle",
            description="Lifecycle test"
        )
        program.add_instruction(SemanticInstruction(
            opcode=SemanticOpcode.SET,
            parameters={"name": "test", "value": 1}
        ))
        
        # 2. 转换为字典
        data = program.to_dict()
        
        # 3. 从字典创建
        restored = SemanticProgram.from_dict(data)
        
        # 4. 加载到 VM
        await vm.load_program(restored)
        
        # 验证
        assert restored.name == program.name
        assert len(restored.instructions) == 1

    def test_processor_parse_response_formats(self, vm):
        """测试处理器解析多种响应格式"""
        processor = vm.processor
        
        # JSON 格式
        json_result = processor._parse_response('{"success": true}')
        assert json_result["success"] is True
        
        # Markdown JSON 格式
        md_result = processor._parse_response('```json\n{"success": true}\n```')
        assert md_result["success"] is True
        
        # Markdown 代码块格式
        code_result = processor._parse_response('```\n{"success": true}\n```')
        assert code_result["success"] is True
        
        # 无效格式
        invalid_result = processor._parse_response('Invalid JSON')
        assert invalid_result["success"] is False
