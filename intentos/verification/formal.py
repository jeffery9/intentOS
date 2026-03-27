"""
形式化验证模块 (Formal Verification)

提供意图执行的形式化验证功能：
1. DAG 有效性验证
2. 能力调用类型检查
3. 执行轨迹回放
4. 语义规范验证
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# =============================================================================
# 执行状态和事件
# =============================================================================


class ExecutionStatus(Enum):
    """执行状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class EventType(Enum):
    """事件类型"""

    TASK_START = "task_start"
    TASK_END = "task_end"
    TASK_ERROR = "task_error"
    CAPABILITY_CALL = "capability_call"
    CAPABILITY_RETURN = "capability_return"
    STATE_CHANGE = "state_change"
    MESSAGE = "message"


@dataclass
class ExecutionEvent:
    """
    执行事件
    
    记录执行过程中的每个事件
    """
    event_id: str
    event_type: EventType
    timestamp: datetime
    task_id: str
    data: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "task_id": self.task_id,
            "data": self.data,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> ExecutionEvent:
        return cls(
            event_id=data["event_id"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            task_id=data["task_id"],
            data=data.get("data", {}),
        )


# =============================================================================
# 执行轨迹
# =============================================================================


@dataclass
class ExecutionTrace:
    """
    执行轨迹
    
    记录一次完整执行的所有事件和状态
    """
    trace_id: str
    intent_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    events: list[ExecutionEvent] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_event(
        self,
        event_type: EventType,
        task_id: str,
        data: Optional[dict] = None,
    ) -> ExecutionEvent:
        """添加事件"""
        event = ExecutionEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            task_id=task_id,
            data=data or {},
        )
        self.events.append(event)
        
        if event_type == EventType.TASK_START and self.start_time is None:
            self.start_time = event.timestamp
            self.status = ExecutionStatus.RUNNING
        
        if event_type in [EventType.TASK_END, EventType.TASK_ERROR]:
            if event_type == EventType.TASK_ERROR:
                self.status = ExecutionStatus.FAILED
                self.error_message = data.get("error", "") if data else ""
            else:
                self.status = ExecutionStatus.COMPLETED
            self.end_time = event.timestamp
        
        return event
    
    def get_events_by_task(self, task_id: str) -> list[ExecutionEvent]:
        """获取指定任务的所有事件"""
        return [e for e in self.events if e.task_id == task_id]
    
    def get_events_by_type(self, event_type: EventType) -> list[ExecutionEvent]:
        """获取指定类型的所有事件"""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_duration(self) -> float:
        """获取执行时长（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "intent_id": self.intent_id,
            "status": self.status.value,
            "events": [e.to_dict() for e in self.events],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "duration": self.get_duration(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> ExecutionTrace:
        trace = cls(
            trace_id=data["trace_id"],
            intent_id=data["intent_id"],
            status=ExecutionStatus(data["status"]),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            error_message=data.get("error_message", ""),
            metadata=data.get("metadata", {}),
        )
        trace.events = [ExecutionEvent.from_dict(e) for e in data.get("events", [])]
        return trace


# =============================================================================
# DAG 验证
# =============================================================================


@dataclass
class DAGNode:
    """DAG 节点"""
    node_id: str
    task_type: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class DAGValidationResult:
    """DAG 验证结果"""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DAGValidator:
    """
    DAG 验证器
    
    验证任务 DAG 的有效性：
    1. 无环性检查
    2. 依赖完整性检查
    3. 输入输出类型检查
    4. 可达性检查
    """
    
    def validate(self, dag_nodes: list[DAGNode]) -> DAGValidationResult:
        """
        验证 DAG
        
        Args:
            dag_nodes: DAG 节点列表
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        
        # 1. 检查节点 ID 唯一性
        node_ids = [n.node_id for n in dag_nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("存在重复的节点 ID")
        
        # 2. 构建邻接表
        node_map = {n.node_id: n for n in dag_nodes}
        adjacency = {n.node_id: [] for n in dag_nodes}
        
        for node in dag_nodes:
            for dep_id in node.dependencies:
                if dep_id not in node_map:
                    errors.append(f"节点 {node.node_id} 依赖不存在的节点 {dep_id}")
                else:
                    adjacency[dep_id].append(node.node_id)
        
        # 3. 检查环
        has_cycle = self._has_cycle(dag_nodes, adjacency)
        if has_cycle:
            errors.append("DAG 存在环，不是有效的有向无环图")
        
        # 4. 检查孤立节点（没有依赖也没有被依赖）
        for node in dag_nodes:
            has_dependencies = len(node.dependencies) > 0
            is_depended_on = len(adjacency[node.node_id]) > 0
            
            if not has_dependencies and not is_depended_on and len(dag_nodes) > 1:
                warnings.append(f"节点 {node.node_id} 是孤立节点")
        
        # 5. 检查输入输出类型
        for node in dag_nodes:
            type_errors = self._validate_node_io(node)
            errors.extend(type_errors)
        
        return DAGValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def _has_cycle(
        self,
        nodes: list[DAGNode],
        adjacency: dict[str, list[str]],
    ) -> bool:
        """使用 DFS 检查是否有环"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n.node_id: WHITE for n in nodes}
        
        def dfs(node_id: str) -> bool:
            color[node_id] = GRAY
            
            for neighbor_id in adjacency.get(node_id, []):
                if color[neighbor_id] == GRAY:
                    return True  # 发现后向边，存在环
                if color[neighbor_id] == WHITE and dfs(neighbor_id):
                    return True
            
            color[node_id] = BLACK
            return False
        
        for node in nodes:
            if color[node.node_id] == WHITE:
                if dfs(node.node_id):
                    return True
        
        return False
    
    def _validate_node_io(self, node: DAGNode) -> list[str]:
        """验证节点的输入输出"""
        errors = []
        
        # 检查输入是否包含必需的字段
        if "required_inputs" in node.outputs:
            required = node.outputs["required_inputs"]
            for req_input in required:
                if req_input not in node.inputs:
                    errors.append(
                        f"节点 {node.node_id} 缺少必需输入：{req_input}"
                    )
        
        return errors


# =============================================================================
# 能力调用类型检查
# =============================================================================


@dataclass
class CapabilitySignature:
    """能力签名"""
    name: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    description: str = ""


class CapabilityTypeChecker:
    """
    能力调用类型检查器
    
    验证能力调用的输入输出是否符合 Schema
    """
    
    def __init__(self):
        self.capabilities: dict[str, CapabilitySignature] = {}
    
    def register_capability(self, signature: CapabilitySignature) -> None:
        """注册能力签名"""
        self.capabilities[signature.name] = signature
    
    def validate_call(
        self,
        capability_name: str,
        inputs: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        验证能力调用
        
        Args:
            capability_name: 能力名称
            inputs: 输入参数
            
        Returns:
            (是否有效，错误列表)
        """
        if capability_name not in self.capabilities:
            return (False, [f"能力 {capability_name} 未注册"])
        
        signature = self.capabilities[capability_name]
        errors = []
        
        # 验证输入 Schema
        errors.extend(self._validate_schema(inputs, signature.input_schema, "输入"))
        
        return (len(errors) == 0, errors)
    
    def validate_response(
        self,
        capability_name: str,
        outputs: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        验证能力响应
        
        Args:
            capability_name: 能力名称
            outputs: 输出参数
            
        Returns:
            (是否有效，错误列表)
        """
        if capability_name not in self.capabilities:
            return (False, [f"能力 {capability_name} 未注册"])
        
        signature = self.capabilities[capability_name]
        errors = []
        
        # 验证输出 Schema
        errors.extend(self._validate_schema(outputs, signature.output_schema, "输出"))
        
        return (len(errors) == 0, errors)
    
    def _validate_schema(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
        context: str,
    ) -> list[str]:
        """验证数据是否符合 Schema"""
        errors = []
        
        # 简单 Schema 验证
        if "type" in schema:
            expected_type = schema["type"]
            if expected_type == "object" and not isinstance(data, dict):
                errors.append(f"{context}类型错误：期望 object，得到 {type(data).__name__}")
        
        # 检查必需字段
        if "required" in schema and isinstance(data, dict):
            for field in schema.get("required", []):
                if field not in data:
                    errors.append(f"{context}缺少必需字段：{field}")
        
        # 检查属性类型
        if "properties" in schema and isinstance(data, dict):
            for prop_name, prop_schema in schema["properties"].items():
                if prop_name in data:
                    prop_errors = self._validate_property(
                        data[prop_name], prop_schema, f"{context}.{prop_name}"
                    )
                    errors.extend(prop_errors)
        
        return errors
    
    def _validate_property(
        self,
        value: Any,
        schema: dict[str, Any],
        path: str,
    ) -> list[str]:
        """验证属性类型"""
        errors = []
        
        if "type" in schema:
            expected_type = schema["type"]
            type_map = {
                "string": str,
                "integer": int,
                "number": (int, float),
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            
            expected_python_type = type_map.get(expected_type)
            if expected_python_type and not isinstance(value, expected_python_type):
                errors.append(
                    f"{path} 类型错误：期望 {expected_type}，得到 {type(value).__name__}"
                )
        
        return errors


# =============================================================================
# 执行轨迹回放器
# =============================================================================


class TraceReplayer:
    """
    执行轨迹回放器
    
    支持：
    1. 完整回放
    2. 单步执行
    3. 断点调试
    4. 状态恢复
    """
    
    def __init__(self, trace: ExecutionTrace):
        self.trace = trace
        self.current_event_index = 0
        self.breakpoints: set[int] = set()  # 断点位置
        self.state_history: list[dict] = []  # 状态历史
    
    def reset(self) -> None:
        """重置回放"""
        self.current_event_index = 0
        self.state_history = []
    
    def step(self) -> Optional[ExecutionEvent]:
        """单步执行"""
        if self.current_event_index >= len(self.trace.events):
            return None
        
        event = self.trace.events[self.current_event_index]
        self.current_event_index += 1
        
        # 记录状态
        self.state_history.append({
            "event_index": self.current_event_index,
            "event": event.to_dict(),
        })
        
        return event
    
    def step_back(self) -> Optional[ExecutionEvent]:
        """回退一步"""
        if self.current_event_index <= 0:
            return None
        
        self.current_event_index -= 1
        return self.trace.events[self.current_event_index]
    
    def play_until(
        self,
        event_type: Optional[EventType] = None,
        task_id: Optional[str] = None,
    ) -> list[ExecutionEvent]:
        """
        播放直到指定条件
        
        Args:
            event_type: 目标事件类型
            task_id: 目标任务 ID
            
        Returns:
            播放的事件列表
        """
        events = []
        
        while self.current_event_index < len(self.trace.events):
            event = self.trace.events[self.current_event_index]
            events.append(event)
            self.current_event_index += 1
            
            # 检查断点
            if self.current_event_index in self.breakpoints:
                break
            
            # 检查停止条件
            if event_type and event.event_type != event_type:
                continue
            if task_id and event.task_id != task_id:
                continue
            
            if (event_type is None or event.event_type == event_type) and \
               (task_id is None or event.task_id == task_id):
                break
        
        return events
    
    def play_all(self) -> list[ExecutionEvent]:
        """播放所有事件"""
        events = []
        while self.current_event_index < len(self.trace.events):
            event = self.step()
            if event:
                events.append(event)
        return events
    
    def add_breakpoint(self, event_index: int) -> None:
        """添加断点"""
        if 0 <= event_index < len(self.trace.events):
            self.breakpoints.add(event_index)
    
    def remove_breakpoint(self, event_index: int) -> None:
        """移除断点"""
        self.breakpoints.discard(event_index)
    
    def get_current_state(self) -> dict[str, Any]:
        """获取当前状态"""
        return {
            "current_event_index": self.current_event_index,
            "total_events": len(self.trace.events),
            "trace_status": self.trace.status.value,
            "is_completed": self.current_event_index >= len(self.trace.events),
        }
    
    def get_state_at(self, event_index: int) -> Optional[dict]:
        """获取指定位置的状态"""
        for state in self.state_history:
            if state["event_index"] == event_index:
                return state
        return None


# =============================================================================
# 形式化验证器
# =============================================================================


class FormalVerifier:
    """
    形式化验证器
    
    提供完整的验证功能：
    1. DAG 验证
    2. 类型检查
    3. 轨迹验证
    """
    
    def __init__(self):
        self.dag_validator = DAGValidator()
        self.type_checker = CapabilityTypeChecker()
    
    def verify_intent_execution(
        self,
        dag_nodes: list[DAGNode],
        trace: ExecutionTrace,
    ) -> dict[str, Any]:
        """
        验证意图执行
        
        Args:
            dag_nodes: DAG 节点
            trace: 执行轨迹
            
        Returns:
            验证报告
        """
        report = {
            "dag_valid": False,
            "trace_valid": False,
            "errors": [],
            "warnings": [],
        }
        
        # 1. 验证 DAG
        dag_result = self.dag_validator.validate(dag_nodes)
        report["dag_valid"] = dag_result.is_valid
        report["errors"].extend(dag_result.errors)
        report["warnings"].extend(dag_result.warnings)
        
        # 2. 验证轨迹
        trace_valid = self._verify_trace(trace, dag_nodes)
        report["trace_valid"] = trace_valid
        if not trace_valid:
            report["errors"].append("执行轨迹与 DAG 不匹配")
        
        return report
    
    def _verify_trace(
        self,
        trace: ExecutionTrace,
        dag_nodes: list[DAGNode],
    ) -> bool:
        """验证轨迹是否与 DAG 一致"""
        node_map = {n.node_id: n for n in dag_nodes}
        
        # 检查所有任务是否都在 DAG 中
        task_ids = set()
        for event in trace.events:
            if event.event_type == EventType.TASK_START:
                task_ids.add(event.task_id)
        
        # 验证每个任务都有对应的 DAG 节点
        for task_id in task_ids:
            if task_id not in node_map:
                return False
        
        # 验证执行顺序符合依赖关系
        completed_tasks = set()
        for event in trace.events:
            if event.event_type == EventType.TASK_START:
                node = node_map.get(event.task_id)
                if node:
                    # 检查所有依赖是否已完成
                    for dep_id in node.dependencies:
                        if dep_id not in completed_tasks:
                            return False
            
            if event.event_type == EventType.TASK_END:
                completed_tasks.add(event.task_id)
        
        return True
    
    def register_capability(self, signature: CapabilitySignature) -> None:
        """注册能力签名"""
        self.type_checker.register_capability(signature)
    
    def validate_capability_call(
        self,
        capability_name: str,
        inputs: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """验证能力调用"""
        return self.type_checker.validate_call(capability_name, inputs)


# =============================================================================
# 工厂函数
# =============================================================================


def create_execution_trace(intent_id: str) -> ExecutionTrace:
    """创建执行轨迹"""
    return ExecutionTrace(
        trace_id=str(uuid.uuid4()),
        intent_id=intent_id,
    )


def create_dag_node(
    node_id: str,
    task_type: str,
    dependencies: Optional[list[str]] = None,
) -> DAGNode:
    """创建 DAG 节点"""
    return DAGNode(
        node_id=node_id,
        task_type=task_type,
        dependencies=dependencies or [],
    )


def create_capability_signature(
    name: str,
    input_schema: dict[str, Any],
    output_schema: dict[str, Any],
    description: str = "",
) -> CapabilitySignature:
    """创建能力签名"""
    return CapabilitySignature(
        name=name,
        input_schema=input_schema,
        output_schema=output_schema,
        description=description,
    )


def create_formal_verifier() -> FormalVerifier:
    """创建形式化验证器"""
    return FormalVerifier()
