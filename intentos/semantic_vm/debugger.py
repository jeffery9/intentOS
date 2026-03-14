"""
调试器支持

提供断点、单步执行、状态检查

设计文档：docs/private/011-debugger-support.md
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4


class DebugEventType(Enum):
    """调试事件类型"""
    BREAKPOINT = "breakpoint"
    STEP = "step"
    EXCEPTION = "exception"
    PROGRAM_EXIT = "program_exit"


class DebuggerState(Enum):
    """调试器状态"""
    INACTIVE = "inactive"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"


@dataclass
class Breakpoint:
    """断点"""
    
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    instruction_index: int = 0
    condition: Optional[str] = None
    temporary: bool = False
    enabled: bool = True
    hit_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "instruction_index": self.instruction_index,
            "condition": self.condition,
            "temporary": self.temporary,
            "enabled": self.enabled,
            "hit_count": self.hit_count,
        }


@dataclass
class DebugEvent:
    """调试事件"""
    
    type: DebugEventType
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class StackFrame:
    """栈帧"""
    
    program_name: str
    instruction_index: int
    instruction_repr: str
    variables: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "program_name": self.program_name,
            "instruction_index": self.instruction_index,
            "instruction_repr": self.instruction_repr,
            "variables": self.variables,
            "context": self.context,
        }


@dataclass
class DebugSession:
    """调试会话"""
    
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    state: DebuggerState = DebuggerState.INACTIVE
    
    breakpoints: dict[str, Breakpoint] = field(default_factory=dict)
    
    current_pc: int = 0
    current_program: str = ""
    
    call_stack: list[StackFrame] = field(default_factory=list)
    
    event_history: list[DebugEvent] = field(default_factory=list)
    
    continue_future: Optional[asyncio.Future] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "state": self.state.value,
            "breakpoints": {k: v.to_dict() for k, v in self.breakpoints.items()},
            "current_pc": self.current_pc,
            "current_program": self.current_program,
            "call_stack": [f.to_dict() for f in self.call_stack],
            "event_history": [e.to_dict() for e in self.event_history[-10:]],
        }


class SemanticDebugger:
    """语义 VM 调试器"""
    
    def __init__(self):
        self._sessions: dict[str, DebugSession] = {}
        self._current_session: Optional[DebugSession] = None
    
    def create_session(self) -> DebugSession:
        """创建调试会话"""
        session = DebugSession()
        self._sessions[session.id] = session
        self._current_session = session
        return session
    
    def get_session(self, session_id: str) -> Optional[DebugSession]:
        """获取调试会话"""
        return self._sessions.get(session_id)
    
    def close_session(self, session_id: str) -> None:
        """关闭调试会话"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            if session.continue_future:
                session.continue_future.set_result(None)
            del self._sessions[session_id]
    
    def add_breakpoint(
        self,
        instruction_index: int,
        condition: Optional[str] = None,
        temporary: bool = False,
    ) -> Breakpoint:
        """添加断点"""
        if not self._current_session:
            raise RuntimeError("没有活跃的调试会话")
        
        breakpoint = Breakpoint(
            instruction_index=instruction_index,
            condition=condition,
            temporary=temporary,
        )
        
        self._current_session.breakpoints[breakpoint.id] = breakpoint
        return breakpoint
    
    def remove_breakpoint(self, breakpoint_id: str) -> bool:
        """移除断点"""
        if not self._current_session:
            return False
        
        if breakpoint_id in self._current_session.breakpoints:
            del self._current_session.breakpoints[breakpoint_id]
            return True
        
        return False
    
    def list_breakpoints(self) -> list[Breakpoint]:
        """列出所有断点"""
        if not self._current_session:
            return []
        return list(self._current_session.breakpoints.values())
    
    async def should_pause(
        self,
        pc: int,
        program_name: str,
        variables: dict,
    ) -> bool:
        """检查是否应该暂停"""
        if not self._current_session:
            return False
        
        session = self._current_session
        
        if session.state == DebuggerState.INACTIVE:
            return False
        
        for bp in session.breakpoints.values():
            if bp.enabled and bp.instruction_index == pc:
                if bp.condition:
                    if not self._evaluate_condition(bp.condition, variables):
                        continue
                
                bp.hit_count += 1
                await self._trigger_breakpoint(session, pc, program_name, bp)
                
                if bp.temporary:
                    self.remove_breakpoint(bp.id)
                
                return True
        
        if session.state == DebuggerState.STEPPING:
            await self._trigger_step(session, pc, program_name, variables)
            return True
        
        return False
    
    def _evaluate_condition(self, condition: str, variables: dict) -> bool:
        """评估断点条件"""
        try:
            from .safe_eval import SafeConditionEvaluator
            return SafeConditionEvaluator.evaluate(condition, variables)
        except Exception:
            return False
    
    async def _trigger_breakpoint(
        self,
        session: DebugSession,
        pc: int,
        program_name: str,
        breakpoint: Breakpoint,
    ) -> None:
        """触发断点事件"""
        session.state = DebuggerState.PAUSED
        session.current_pc = pc
        session.current_program = program_name
        
        event = DebugEvent(
            type=DebugEventType.BREAKPOINT,
            message=f"断点命中：{breakpoint.id}",
            data={
                "breakpoint_id": breakpoint.id,
                "instruction_index": pc,
                "program_name": program_name,
            },
        )
        
        session.event_history.append(event)
        await self._wait_for_continue(session)
    
    async def _trigger_step(
        self,
        session: DebugSession,
        pc: int,
        program_name: str,
        variables: dict,
    ) -> None:
        """触发单步事件"""
        session.state = DebuggerState.PAUSED
        session.current_pc = pc
        session.current_program = program_name
        
        event = DebugEvent(
            type=DebugEventType.STEP,
            message=f"单步执行：{pc}",
            data={
                "instruction_index": pc,
                "program_name": program_name,
                "variables": variables,
            },
        )
        
        session.event_history.append(event)
        await self._wait_for_continue(session)
    
    async def _wait_for_continue(self, session: DebugSession) -> None:
        """等待继续执行"""
        session.continue_future = asyncio.Future()
        await session.continue_future
        session.continue_future = None
    
    def continue_execution(self) -> None:
        """继续执行"""
        if not self._current_session:
            raise RuntimeError("没有活跃的调试会话")
        
        self._current_session.state = DebuggerState.RUNNING
        
        if self._current_session.continue_future:
            self._current_session.continue_future.set_result(None)
    
    def step_over(self) -> None:
        """单步跳过"""
        if not self._current_session:
            raise RuntimeError("没有活跃的调试会话")
        
        self._current_session.state = DebuggerState.STEPPING
        
        if self._current_session.continue_future:
            self._current_session.continue_future.set_result(None)
    
    def get_variables(self) -> dict[str, Any]:
        """获取当前变量"""
        if not self._current_session:
            return {}
        
        if self._current_session.call_stack:
            frame = self._current_session.call_stack[-1]
            return frame.variables.copy()
        
        return {}
    
    def get_variable(self, name: str) -> Any:
        """获取单个变量"""
        variables = self.get_variables()
        return variables.get(name)
    
    def get_call_stack(self) -> list[StackFrame]:
        """获取调用栈"""
        if not self._current_session:
            return []
        return self._current_session.call_stack.copy()
    
    def get_current_state(self) -> dict:
        """获取当前调试状态"""
        if not self._current_session:
            return {}
        return self._current_session.to_dict()
    
    def push_frame(
        self,
        program_name: str,
        instruction_index: int,
        instruction_repr: str,
        variables: dict,
        context: dict,
    ) -> None:
        """压入栈帧"""
        if not self._current_session:
            return
        
        frame = StackFrame(
            program_name=program_name,
            instruction_index=instruction_index,
            instruction_repr=instruction_repr,
            variables=variables,
            context=context,
        )
        
        self._current_session.call_stack.append(frame)
    
    def pop_frame(self) -> Optional[StackFrame]:
        """弹出栈帧"""
        if not self._current_session:
            return None
        
        if self._current_session.call_stack:
            return self._current_session.call_stack.pop()
        
        return None
    
    def update_frame(
        self,
        instruction_index: int,
        variables: dict,
    ) -> None:
        """更新栈帧"""
        if not self._current_session:
            return
        
        if self._current_session.call_stack:
            frame = self._current_session.call_stack[-1]
            frame.instruction_index = instruction_index
            frame.variables = variables
