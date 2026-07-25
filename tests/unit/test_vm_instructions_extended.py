
import pytest
from unittest.mock import MagicMock, AsyncMock
from intentos.semantic_vm.vm import SemanticVM, SemanticProgram, SemanticInstruction, SemanticOpcode
from intentos.kernel.core import PrivilegeLevel

@pytest.mark.anyio
async def test_vm_call_instruction():
    """测试 CALL 指令：子程序嵌套执行"""
    vm = SemanticVM()
    await vm.initialize()
    
    # 1. 定义子程序：设置变量 y = 20
    sub_prog = SemanticProgram(name="sub_routine")
    sub_prog.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.SET, parameters={"name": "y", "value": 20}
    ))
    await vm.load_program(sub_prog)
    
    # 2. 定义主程序：设置 x = 10，然后 CALL 子程序
    main_prog = SemanticProgram(name="main")
    main_prog.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.SET, parameters={"name": "x", "value": 10}
    ))
    main_prog.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.CALL, target_name="sub_routine"
    ))
    await vm.load_program(main_prog)
    
    # 执行主程序
    result = await vm.execute_program("main")
    
    assert result["success"] is True
    # 验证变量状态（跨程序执行）
    assert vm.memory.get("VARIABLE", "x") == 10
    assert vm.memory.get("VARIABLE", "y") == 20

@pytest.mark.anyio
async def test_vm_execute_with_io_capabilities():
    """测试 EXECUTE 指令：集成物理 IO (Skill)"""
    # 模拟能力注册中心和 IO 层
    registry = MagicMock()
    vm = SemanticVM(registry=registry)
    await vm.initialize()
    
    # 模拟 skill_io.skill_io_handler
    vm.io_capabilities.skill_io = MagicMock()
    vm.io_capabilities.skill_io.skill_io_handler = AsyncMock(return_value="Physical Result")
    
    prog = SemanticProgram(name="io_test")
    prog.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.EXECUTE, 
        parameters={"skill_name": "test_skill", "param": "val"}
    ))
    await vm.load_program(prog)
    
    result = await vm.execute_program("io_test")
    
    assert result["success"] is True
    assert result["results"][0]["result"] == "Physical Result"
    vm.io_capabilities.skill_io.skill_io_handler.assert_called_once()

@pytest.mark.anyio
async def test_vm_meta_instructions_privilege():
    """测试元指令权限：用户态应禁止执行"""
    vm = SemanticVM(mode=PrivilegeLevel.USER)
    await vm.initialize()
    
    prog = SemanticProgram(name="meta_test")
    prog.add_instruction(SemanticInstruction(
        opcode=SemanticOpcode.DEFINE_INSTRUCTION, 
        parameters={"name": "hacked", "handler": "..."}
    ))
    await vm.load_program(prog)
    
    result = await vm.execute_program("meta_test")
    
    # 验证第一条指令执行失败（权限拒绝）
    assert result["success"] is False
    assert "禁止执行特权指令" in result["results"][0]["error"]

@pytest.mark.anyio
async def test_processor_apply_operation_extended():
    """测试 LLMProcessor 扩展的 CRUD 操作"""
    from intentos.llm import LLMExecutor
    mock_llm = MagicMock()
    # 模拟 LLM 返回 create_template 操作
    mock_llm.execute = AsyncMock(return_value=MagicMock(
        content='{"operation": "create_template", "parameters": {"name": "new_tpl", "data": "val"}}'
    ))
    
    executor = LLMExecutor(provider="mock")
    executor.execute = mock_llm.execute
    
    vm = SemanticVM(llm_executor=executor)
    await vm.initialize()
    
    instr = SemanticInstruction(opcode=SemanticOpcode.CREATE, target="TEMPLATE", target_name="unused")
    
    # 直接测试处理器执行
    result = await vm.processor.execute(instr, vm.memory)
    
    assert result["operation"] == "create_template"
    # 验证内存是否已设置
    assert vm.memory.get("TEMPLATE", "new_tpl") == {"name": "new_tpl", "data": "val"}
