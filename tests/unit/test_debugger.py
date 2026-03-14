"""
Debugger 模块测试

覆盖调试器所有功能
"""

import pytest
from intentos.semantic_vm.debugger import (
    DebugEventType,
    DebuggerState,
    Breakpoint,
    DebugEvent,
    StackFrame,
    DebugSession,
    SemanticDebugger,
)
from datetime import datetime


# =============================================================================
# Enum Tests
# =============================================================================

class TestDebugEventType:
    """DebugEventType 测试"""

    def test_event_type_values(self):
        """测试事件类型值"""
        assert DebugEventType.BREAKPOINT.value == "breakpoint"
        assert DebugEventType.STEP.value == "step"
        assert DebugEventType.EXCEPTION.value == "exception"
        assert DebugEventType.PROGRAM_EXIT.value == "program_exit"


class TestDebuggerState:
    """DebuggerState 测试"""

    def test_state_values(self):
        """测试状态值"""
        assert DebuggerState.INACTIVE.value == "inactive"
        assert DebuggerState.RUNNING.value == "running"
        assert DebuggerState.PAUSED.value == "paused"
        assert DebuggerState.STEPPING.value == "stepping"


# =============================================================================
# Breakpoint Tests
# =============================================================================

class TestBreakpoint:
    """Breakpoint 测试"""

    def test_breakpoint_default(self):
        """测试默认断点"""
        bp = Breakpoint()
        assert bp.instruction_index == 0
        assert bp.enabled is True
        assert bp.temporary is False
        assert bp.hit_count == 0

    def test_breakpoint_custom(self):
        """测试自定义断点"""
        bp = Breakpoint(
            instruction_index=10,
            condition="x > 0",
            temporary=True,
            enabled=False
        )
        assert bp.instruction_index == 10
        assert bp.condition == "x > 0"
        assert bp.temporary is True
        assert bp.enabled is False

    def test_breakpoint_to_dict(self):
        """测试转换为字典"""
        bp = Breakpoint(instruction_index=5, condition="y == 10")
        data = bp.to_dict()
        assert data["instruction_index"] == 5
        assert data["condition"] == "y == 10"
        assert "id" in data


# =============================================================================
# DebugEvent Tests
# =============================================================================

class TestDebugEvent:
    """DebugEvent 测试"""

    def test_event_creation(self):
        """测试事件创建"""
        event = DebugEvent(
            type=DebugEventType.BREAKPOINT,
            message="Breakpoint hit"
        )
        assert event.type == DebugEventType.BREAKPOINT
        assert event.message == "Breakpoint hit"

    def test_event_with_data(self):
        """测试带数据的事件"""
        event = DebugEvent(
            type=DebugEventType.STEP,
            message="Step",
            data={"pc": 10}
        )
        assert event.data["pc"] == 10

    def test_event_to_dict(self):
        """测试转换为字典"""
        event = DebugEvent(type=DebugEventType.EXCEPTION, message="Error")
        data = event.to_dict()
        assert data["type"] == "exception"
        assert data["message"] == "Error"
        assert "timestamp" in data


# =============================================================================
# StackFrame Tests
# =============================================================================

class TestStackFrame:
    """StackFrame 测试"""

    def test_frame_creation(self):
        """测试栈帧创建"""
        frame = StackFrame(
            program_name="test",
            instruction_index=5,
            instruction_repr="SET x = 1"
        )
        assert frame.program_name == "test"
        assert frame.instruction_index == 5

    def test_frame_with_variables(self):
        """测试带变量的栈帧"""
        frame = StackFrame(
            program_name="prog",
            instruction_index=0,
            instruction_repr="START",
            variables={"x": 1},
            context={"user": "test"}
        )
        assert frame.variables["x"] == 1

    def test_frame_to_dict(self):
        """测试转换为字典"""
        frame = StackFrame(program_name="p", instruction_index=1, instruction_repr="I")
        data = frame.to_dict()
        assert data["program_name"] == "p"
        assert data["instruction_index"] == 1


# =============================================================================
# DebugSession Tests
# =============================================================================

class TestDebugSession:
    """DebugSession 测试"""

    def test_session_creation(self):
        """测试会话创建"""
        session = DebugSession()
        assert session.state == DebuggerState.INACTIVE
        assert session.breakpoints == {}
        assert session.current_pc == 0

    def test_session_to_dict(self):
        """测试转换为字典"""
        session = DebugSession()
        data = session.to_dict()
        assert "id" in data
        assert data["state"] == "inactive"


# =============================================================================
# SemanticDebugger Tests
# =============================================================================

class TestSemanticDebugger:
    """SemanticDebugger 测试"""

    @pytest.fixture
    def debugger(self):
        """创建调试器"""
        return SemanticDebugger()

    def test_debugger_creation(self, debugger):
        """测试调试器创建"""
        assert debugger is not None
        assert debugger._sessions == {}

    def test_create_session(self, debugger):
        """测试创建会话"""
        session = debugger.create_session()
        assert session is not None
        assert session.id in debugger._sessions

    def test_get_session(self, debugger):
        """测试获取会话"""
        created = debugger.create_session()
        retrieved = debugger.get_session(created.id)
        assert retrieved == created

    def test_get_nonexistent_session(self, debugger):
        """测试获取不存在的会话"""
        session = debugger.get_session("nonexistent")
        assert session is None

    def test_close_session(self, debugger):
        """测试关闭会话"""
        session = debugger.create_session()
        debugger.close_session(session.id)
        assert session.id not in debugger._sessions

    def test_add_breakpoint(self, debugger):
        """测试添加断点"""
        debugger.create_session()
        bp = debugger.add_breakpoint(instruction_index=10)
        assert bp is not None
        assert bp.instruction_index == 10

    def test_remove_breakpoint(self, debugger):
        """测试移除断点"""
        debugger.create_session()
        bp = debugger.add_breakpoint(5)
        result = debugger.remove_breakpoint(bp.id)
        assert result is True

    def test_remove_nonexistent_breakpoint(self, debugger):
        """测试移除不存在的断点"""
        debugger.create_session()
        result = debugger.remove_breakpoint("nonexistent")
        assert result is False

    def test_list_breakpoints(self, debugger):
        """测试列出断点"""
        debugger.create_session()
        debugger.add_breakpoint(5)
        debugger.add_breakpoint(10)
        breakpoints = debugger.list_breakpoints()
        assert len(breakpoints) == 2

    def test_list_breakpoints_no_session(self, debugger):
        """测试无会话时列出断点"""
        breakpoints = debugger.list_breakpoints()
        assert breakpoints == []

    def test_continue_execution(self, debugger):
        """测试继续执行"""
        debugger.create_session()
        debugger._current_session.state = DebuggerState.PAUSED
        debugger.continue_execution()
        assert debugger._current_session.state == DebuggerState.RUNNING

    def test_step_over(self, debugger):
        """测试单步跳过"""
        debugger.create_session()
        debugger.step_over()
        assert debugger._current_session.state == DebuggerState.STEPPING

    def test_get_variables(self, debugger):
        """测试获取变量"""
        debugger.create_session()
        variables = debugger.get_variables()
        assert variables == {}

    def test_get_variable(self, debugger):
        """测试获取单个变量"""
        debugger.create_session()
        value = debugger.get_variable("nonexistent")
        assert value is None

    def test_get_call_stack(self, debugger):
        """测试获取调用栈"""
        debugger.create_session()
        stack = debugger.get_call_stack()
        assert stack == []

    def test_get_current_state(self, debugger):
        """测试获取当前状态"""
        debugger.create_session()
        state = debugger.get_current_state()
        assert state is not None
        assert "id" in state

    def test_get_state_no_session(self, debugger):
        """测试无会话时获取状态"""
        state = debugger.get_current_state()
        assert state == {}

    def test_push_frame(self, debugger):
        """测试压入栈帧"""
        debugger.create_session()
        debugger.push_frame("test", 0, "START", {}, {})
        assert len(debugger._current_session.call_stack) == 1

    def test_pop_frame(self, debugger):
        """测试弹出栈帧"""
        debugger.create_session()
        debugger.push_frame("test", 0, "START", {}, {})
        frame = debugger.pop_frame()
        assert frame is not None
        assert frame.program_name == "test"

    def test_pop_frame_empty(self, debugger):
        """测试空栈弹出"""
        debugger.create_session()
        frame = debugger.pop_frame()
        assert frame is None

    def test_update_frame(self, debugger):
        """测试更新栈帧"""
        debugger.create_session()
        debugger.push_frame("test", 0, "START", {}, {})
        debugger.update_frame(instruction_index=10, variables={"x": 1})
        frame = debugger._current_session.call_stack[-1]
        assert frame.instruction_index == 10


# =============================================================================
# Integration Tests
# =============================================================================

class TestDebuggerIntegration:
    """调试器集成测试"""

    @pytest.fixture
    def debugger(self):
        """创建调试器"""
        return SemanticDebugger()

    def test_full_debug_session(self, debugger):
        """测试完整调试会话"""
        session = debugger.create_session()
        bp1 = debugger.add_breakpoint(5)
        bp2 = debugger.add_breakpoint(10)
        breakpoints = debugger.list_breakpoints()
        assert len(breakpoints) == 2
        debugger.remove_breakpoint(bp1.id)
        assert len(debugger.list_breakpoints()) == 1
        debugger.close_session(session.id)

    def test_multiple_sessions(self, debugger):
        """测试多个会话"""
        session1 = debugger.create_session()
        session2 = debugger.create_session()
        
        # 验证两个会话都存在
        assert session1.id in debugger._sessions
        assert session2.id in debugger._sessions

    def test_breakpoint_lifecycle(self, debugger):
        """测试断点生命周期"""
        debugger.create_session()
        bp = debugger.add_breakpoint(20, "y == 10", temporary=True)
        assert bp.instruction_index == 20
        assert bp.temporary is True
        debugger.remove_breakpoint(bp.id)

    def test_stack_frame_operations(self, debugger):
        """测试栈帧操作"""
        debugger.create_session()
        debugger.push_frame("main", 0, "MAIN", {}, {})
        debugger.push_frame("func1", 5, "CALL", {"x": 1}, {})
        debugger.push_frame("func2", 10, "CALL", {"y": 2}, {})
        assert len(debugger._current_session.call_stack) == 3
        frame = debugger.pop_frame()
        assert frame.program_name == "func2"
        assert len(debugger._current_session.call_stack) == 2
