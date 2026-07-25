"""
测试 intentos.sdk.client - IntentOS Python SDK 客户端

覆盖:
- IntentOSClient 创建和初始化
- 意图图谱 API (create_intent, add_relationship, search_intents)
- 验证 API (validate_dag)
- 轨迹 API (create_trace, replay_trace)
- 导出/导入 (export_graph, import_graph)
"""

import json
import os
import tempfile

import pytest


@pytest.fixture
def client():
    """创建 SDK 客户端实例"""
    from intentos.sdk.client import IntentOSClient
    return IntentOSClient(host="localhost", port=8080)


class TestSDKClientInit:
    """客户端初始化测试"""

    def test_default_host_and_port(self):
        from intentos.sdk.client import IntentOSClient
        c = IntentOSClient()
        assert c.host == "localhost"
        assert c.port == 8080

    def test_custom_host_and_port(self):
        from intentos.sdk.client import IntentOSClient
        c = IntentOSClient(host="10.0.0.1", port=9090)
        assert c.host == "10.0.0.1"
        assert c.port == 9090

    def test_has_graph_and_verifier(self, client):
        assert client.graph is not None
        assert client.verifier is not None


class TestIntentGraphAPI:
    """意图图谱 API 测试"""

    def test_create_intent(self, client):
        from intentos.graph import IntentNodeType
        node = client.create_intent(
            name="分析销售数据",
            description="分析指定区域和时间的销售数据",
            tags=["销售", "分析"],
           )
        assert node.name == "分析销售数据"

    def test_add_relationship(self, client):
        from intentos.graph import IntentEdgeType
        n1 = client.create_intent(name="任务A")
        n2 = client.create_intent(name="任务B")
        edge = client.add_relationship(
            source_id=n1.node_id,
            target_id=n2.node_id,
            relationship=IntentEdgeType.TRIGGERS,
           )
        assert edge.source_id == n1.node_id

    def test_search_by_keyword(self, client):
        client.create_intent(name="销售分析", tags=["销售"])
        results = client.search_intents(keyword="销售")
        assert len(results) >= 1

    def test_search_by_tag(self, client):
        client.create_intent(name="任务X", tags=["urgent"])
        client.create_intent(name="任务Y", tags=["low"])
        results = client.search_intents(tag="urgent")
        assert len(results) == 1

    def test_get_graph_stats(self, client):
        client.create_intent(name="统计测试")
        stats = client.get_graph_stats()
        assert isinstance(stats, dict)


class TestValidationAPI:
    """验证 API 测试"""

    def test_validate_valid_dag(self, client):
        from intentos.verification import create_dag_node
        dag_nodes = [
            create_dag_node("task_1", "query", dependencies=[]),
            create_dag_node("task_2", "analyze", dependencies=["task_1"]),
           ]
        result = client.validate_dag(dag_nodes)
        assert "is_valid" in result

    def test_validate_dag_with_cycle(self, client):
        from intentos.verification import create_dag_node
        dag_nodes = [
            create_dag_node("task_a", "run", dependencies=["task_b"]),
            create_dag_node("task_b", "run", dependencies=["task_a"]),
           ]
        result = client.validate_dag(dag_nodes)
        assert not result["is_valid"] or len(result.get("errors", [])) > 0


class TestTraceAPI:
    """轨迹 API 测试"""

    def test_create_trace(self, client):
        trace = client.create_trace("intent_123")
        assert trace.intent_id == "intent_123"

    def test_replay_empty_trace(self, client):
        trace = client.create_trace("empty_intent")
        events = client.replay_trace(trace)
        assert isinstance(events, list)


class TestExportImport:
    """导出/导入测试"""

    def test_export_and_import_graph(self, client, tmp_path):
        client.create_intent(name="导出意图", tags=["test"])
        filepath = str(tmp_path / "graph.json")
        client.export_graph(filepath)
        assert os.path.exists(filepath)
        with open(filepath) as f:
            data = json.load(f)
        assert "nodes" in data

    def test_import_graph(self, tmp_path):
        filepath = str(tmp_path / "import_graph.json")
        graph_data = {"nodes": {}, "edges": {}}
        with open(filepath, "w") as f:
            json.dump(graph_data, f)
        from intentos.sdk.client import IntentOSClient
        client = IntentOSClient()
        client.import_graph(filepath)


class TestCreateClient:
    """便捷函数测试"""

    def test_create_client_default(self):
        from intentos.sdk.client import create_client
        c = create_client()
        assert c.host == "localhost"
        assert c.port == 8080

    def test_create_client_custom(self):
        from intentos.sdk.client import create_client
        c = create_client(host="prod.example.com", port=443)
        assert c.host == "prod.example.com"
