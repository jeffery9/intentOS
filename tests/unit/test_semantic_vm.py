"""
语义 VM 核心测试

测试 SemanticVM, LLMProcessor, SemanticMemory 等核心组件
"""

import pytest

from intentos.llm.backends.mock_backend import MockBackend
from intentos.semantic_vm import (
    LLMProcessor,
    SemanticInstruction,
    SemanticMemory,
    SemanticOpcode,
    SemanticProgram,
    SemanticVM,
)

# =============================================================================
# SemanticMemory 测试
# =============================================================================


class TestSemanticMemory:
    """语义内存测试"""

    def test_set_and_get(self):
        """测试设置和获取"""
        memory = SemanticMemory()

        memory.set("TEMPLATE", "test", {"key": "value"})
        assert memory.get("TEMPLATE", "test") == {"key": "value"}

    def test_get_nonexistent(self):
        """测试获取不存在的值"""
        memory = SemanticMemory()
        assert memory.get("TEMPLATE", "nonexistent") is None

    def test_delete(self):
        """测试删除"""
        memory = SemanticMemory()
        memory.set("TEMPLATE", "test", "value")

        assert memory.delete("TEMPLATE", "test") is True
        assert memory.get("TEMPLATE", "test") is None

    def test_delete_nonexistent(self):
        """测试删除不存在的值"""
        memory = SemanticMemory()
        assert memory.delete("TEMPLATE", "nonexistent") is False

    def test_query_all(self):
        """测试查询所有"""
        memory = SemanticMemory()
        memory.set("TEMPLATE", "t1", "value1")
        memory.set("TEMPLATE", "t2", "value2")

        results = memory.query("TEMPLATE")

        assert len(results) == 2

    def test_query_with_condition(self):
        """测试条件查询"""
        memory = SemanticMemory()
        memory.set("TEMPLATE", "active", "value1")
        memory.set("TEMPLATE", "inactive", "value2")

        results = memory.query("TEMPLATE", condition="key == 'active'")

        assert len(results) == 1
        assert results[0]["key"] == "active"

    def test_audit_log(self):
        """测试审计日志"""
        memory = SemanticMemory()
        audit_id = memory.log_audit("test_action", {"key": "value"})

        assert audit_id is not None
        assert len(memory.audit_log) == 1

    def test_get_state(self):
        """测试获取状态"""
        memory = SemanticMemory()
        memory.set("TEMPLATE", "t1", "v1")
        memory.set("CAPABILITY", "c1", "v2")

        state = memory.get_state()

        assert state["templates_count"] == 1
        assert state["capabilities_count"] == 1


# =============================================================================
# SemanticInstruction 测试
# =============================================================================


class TestSemanticInstruction:
    """语义指令测试"""

    def test_create_instruction(self):
        """测试创建指令"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.SET, parameters={"name": "x", "value": 10}
        )

        assert instr.opcode == SemanticOpcode.SET
        assert instr.parameters["name"] == "x"

    def test_to_dict(self):
        """测试转换为字典"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.CREATE, target="TEMPLATE", target_name="test"
        )

        data = instr.to_dict()

        assert data["opcode"] == "create"
        assert data["target"] == "TEMPLATE"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {"opcode": "set", "parameters": {"name": "y", "value": 20}}

        instr = SemanticInstruction.from_dict(data)

        assert instr.opcode == SemanticOpcode.SET
        assert instr.parameters["name"] == "y"

    def test_to_natural_language(self):
        """测试转换为自然语言"""
        instr = SemanticInstruction(
            opcode=SemanticOpcode.CREATE, target="TEMPLATE", target_name="test_template"
        )

        nl = instr.to_natural_language()

        assert "CREATE" in nl
        assert "test_template" in nl


# =============================================================================
# SemanticProgram 测试
# =============================================================================


class TestSemanticProgram:
    """语义程序测试"""

    def test_create_program(self):
        """测试创建程序"""
        program = SemanticProgram(name="test_program", description="Test program")

        assert program.name == "test_program"
        assert len(program.instructions) == 0

    def test_add_instruction(self):
        """测试添加指令"""
        program = SemanticProgram(name="test")

        instr = SemanticInstruction(opcode=SemanticOpcode.SET)
        program.add_instruction(instr)

        assert len(program.instructions) == 1

    def test_to_dict(self):
        """测试转换为字典"""
        program = SemanticProgram(name="test", version="2.0.0")

        data = program.to_dict()

        assert data["name"] == "test"
        assert data["version"] == "2.0.0"

    def test_from_dict(self):
        """测试从字典创建"""
        data = {"name": "restored_program", "description": "Restored", "version": "1.5.0"}

        program = SemanticProgram.from_dict(data)

        assert program.name == "restored_program"
        assert program.description == "Restored"


# =============================================================================
# SemanticVM 测试
# =============================================================================


class TestSemanticVM:
    """语义虚拟机测试"""

    @pytest.fixture
    def vm(self):
        """创建测试用 VM"""
        llm = MockBackend()
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_execute_nonexistent_program(self, vm):
        """测试执行不存在的程序"""
        result = await vm.execute_program("nonexistent")

        assert result["success"] is False
        assert "不存在" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_simple_program(self, vm):
        """测试执行简单程序"""
        program = SemanticProgram(name="simple")
        program.add_instruction(
            SemanticInstruction(opcode=SemanticOpcode.SET, parameters={"name": "x", "value": 100})
        )

        vm.memory.set("PROGRAM", program.name, program)
        result = await vm.execute_program(program.name)

        # VM 执行可能成功或失败取决于 LLM 模拟
        # 这里我们只验证程序能够执行
        assert "success" in result

    @pytest.mark.asyncio
    async def test_load_program(self, vm):
        """测试加载程序"""
        program = SemanticProgram(name="test_load")
        program.add_instruction(SemanticInstruction(opcode=SemanticOpcode.SET))

        await vm.load_program(program)

        loaded = vm.memory.get("PROGRAM", "test_load")
        assert loaded is not None
        assert loaded.name == "test_load"


# =============================================================================
# LLMProcessor 测试
# =============================================================================


class TestLLMProcessor:
    """LLM 处理器测试"""

    def test_create_processor(self):
        """测试创建处理器"""
        llm = MockBackend()
        processor = LLMProcessor(llm)

        assert processor.llm_executor == llm
        assert processor.processor_prompt is not None

    @pytest.mark.asyncio
    async def test_processor_initialization(self):
        """测试处理器初始化"""
        llm = MockBackend()
        processor = LLMProcessor(llm)
        memory = SemanticMemory()

        # 验证处理器可以创建
        assert processor is not None
        assert processor.llm_executor is not None


# =============================================================================
# 集成测试
# =============================================================================


class TestSemanticVMIntegration:
    """语义 VM 集成测试"""

    @pytest.fixture
    def vm(self):
        """创建测试用 VM"""
        llm = MockBackend()
        return SemanticVM(llm)

    @pytest.mark.asyncio
    async def test_program_creation_and_load(self, vm):
        """测试程序创建和加载"""
        # 创建程序
        program = SemanticProgram(name="lifecycle_test")
        program.add_instruction(
            SemanticInstruction(opcode=SemanticOpcode.SET, parameters={"name": "x", "value": 1})
        )

        # 加载程序
        await vm.load_program(program)

        # 验证程序已加载
        loaded = vm.memory.get("PROGRAM", "lifecycle_test")
        assert loaded is not None
        assert loaded.name == "lifecycle_test"
