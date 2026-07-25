"""
测试 intentos.verification.formal - 形式化验证

覆盖:
- FormalVerifier (创建, register_capability, verify)
- CapabilitySignature (签名)
- DAGNode / validate_dag
- ExecutionTrace / TraceReplayer
"""

import pytest


class TestFormalVerifier:
    """形式化验证器测试"""

    def test_create_verifier(self):
        from intentos.verification.formal import FormalVerifier
        v = FormalVerifier()
        assert v is not None

    def test_create_formal_verifier_function(self):
        from intentos.verification import create_formal_verifier
        v = create_formal_verifier()
        assert v is not None


class TestDAGNode:
    """DAG 节点测试"""

    def test_create_dag_node(self):
        from intentos.verification import DAGNode, create_dag_node
        node = create_dag_node("task_1", "query", dependencies=[])
        assert node.node_id == "task_1"
        assert node.operation == "query"

    def test_dag_node_with_dependencies(self):
        from intentos.verification import DAGNode, create_dag_node
        node = create_dag_node("task_2", "analyze", dependencies=["task_1"])
        assert "task_1" in node.dependencies


class TestExecutionTrace:
    """执行轨迹测试"""

    def test_create_execution_trace(self):
        from intentos.verification import ExecutionTrace, create_execution_trace
        trace = create_execution_trace("intent_abc")
        assert trace.intent_id == "intent_abc"

    def test_trace_to_dict(self):
        from intentos.verification import ExecutionTrace, create_execution_trace
        trace = create_execution_trace("trace_test")
        d = trace.to_dict()
        assert isinstance(d, dict)
        assert "intent_id" in d


class TestTraceReplayer:
    """轨迹回放器测试"""

    def test_replay_empty_trace(self):
        from intentos.verification import ExecutionTrace, TraceReplayer
        trace = ExecutionTrace(intent_id="empty")
        replayer = TraceReplayer(trace)
        result = replayer.play_all()
        assert isinstance(result, list)


class TestCapabilitySignature:
    """能力签名测试"""

    def test_create_capability_signature(self):
        from intentos.verification import CapabilitySignature, create_capability_signature
        sig = create_capability_signature(
            name="query_sales",
            input_schema={"region": "string"},
            output_schema={"data": "array"},
            description="查询销售数据",
            )
        assert sig.name == "query_sales"
