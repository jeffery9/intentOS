"""
CLI 工具测试
"""

import json
import pytest
import tempfile
import os
from intentos.cli.cli import (
    cmd_graph_init,
    cmd_graph_query,
    cmd_verify_dag,
    cmd_trace_record,
    cmd_trace_replay,
    cmd_status,
)


class MockArgs:
    """模拟命令行参数"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        # 设置默认值
        setattr(self, 'search', None)
        setattr(self, 'node_id', None)
        setattr(self, 'neighbors', None)
        setattr(self, 'stats', False)
        setattr(self, 'step', None)


class TestCLICommands:
    """测试 CLI 命令"""
    
    def test_cmd_graph_init(self, capsys):
        """测试图谱初始化命令"""
        args = MockArgs(output=None)
        cmd_graph_init(args)
        captured = capsys.readouterr()
        assert "demo_001" in captured.out
        assert "分析销售数据" in captured.out
    
    def test_cmd_graph_init_to_file(self):
        """测试图谱初始化到文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            args = MockArgs(output=temp_path)
            cmd_graph_init(args)
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert "nodes" in data
            assert len(data["nodes"]) == 2
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_cmd_graph_query(self, capsys):
        """测试图谱查询命令"""
        # 先创建图谱文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            from intentos.graph import create_intent_graph, create_intent_node, IntentNodeType
            graph = create_intent_graph()
            node = create_intent_node(
                node_id="test_001",
                node_type=IntentNodeType.ATOMIC,
                name="测试意图",
                tags=["测试"],
            )
            graph.add_node(node)
            
            with open(temp_path, 'w') as f:
                json.dump(graph.to_dict(), f, ensure_ascii=False)
            
            # 测试查询
            args = MockArgs(input=temp_path, search="测试")
            cmd_graph_query(args)
            captured = capsys.readouterr()
            assert "测试意图" in captured.out
            
            # 测试统计
            args = MockArgs(input=temp_path, stats=True)
            cmd_graph_query(args)
            captured = capsys.readouterr()
            assert "total_nodes" in captured.out or "总节点数" in captured.out
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_cmd_verify_dag_valid(self, capsys):
        """测试 DAG 验证（有效）"""
        args = MockArgs(input=None)
        result = cmd_verify_dag(args)
        captured = capsys.readouterr()
        assert "DAG 有效" in captured.out or "DAG 无效" in captured.out
    
    def test_cmd_trace_record(self, capsys):
        """测试轨迹记录命令"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            args = MockArgs(intent_id="intent_001", output=temp_path)
            cmd_trace_record(args)
            captured = capsys.readouterr()
            assert "轨迹已保存" in captured.out
            
            # 验证文件内容
            with open(temp_path, 'r') as f:
                data = json.load(f)
            assert data["intent_id"] == "intent_001"
            assert len(data["events"]) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_cmd_trace_replay(self, capsys):
        """测试轨迹回放命令"""
        # 先创建轨迹文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            from intentos.verification import create_execution_trace, EventType
            trace = create_execution_trace("intent_001")
            trace.add_event(EventType.TASK_START, "task_001")
            trace.add_event(EventType.TASK_END, "task_001")
            
            with open(temp_path, 'w') as f:
                json.dump(trace.to_dict(), f, ensure_ascii=False)
            
            # 测试回放
            args = MockArgs(input=temp_path)
            cmd_trace_replay(args)
            captured = capsys.readouterr()
            assert "回放轨迹" in captured.out
            assert "事件数" in captured.out
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_cmd_status(self, capsys):
        """测试状态命令"""
        args = MockArgs()
        cmd_status(args)
        captured = capsys.readouterr()
        assert "IntentOS" in captured.out
        assert "v16.0.0" in captured.out
        assert "✅" in captured.out


class TestSDKClient:
    """测试 SDK 客户端"""
    
    def test_create_client(self):
        """测试创建客户端"""
        from intentos.sdk import create_client
        client = create_client()
        
        assert client.host == "localhost"
        assert client.port == 8080
        assert client.graph is not None
        assert client.verifier is not None
    
    def test_create_intent(self):
        """测试创建意图"""
        from intentos.sdk import create_client
        client = create_client()
        
        intent = client.create_intent(
            name="测试意图",
            description="测试描述",
            tags=["测试"],
        )
        
        assert intent.name == "测试意图"
        assert intent.description == "测试描述"
        assert "测试" in intent.tags
    
    def test_search_intents(self):
        """测试搜索意图"""
        from intentos.sdk import create_client
        client = create_client()
        
        # 创建意图
        intent1 = client.create_intent(name="分析销售", tags=["销售"])
        intent2 = client.create_intent(name="生成报表", tags=["报表"])
        
        # 搜索
        results = client.search_intents(keyword="销售")
        assert len(results) == 1
        assert results[0].name == "分析销售"
        
        # 按标签搜索
        results = client.search_intents(tag="报表")
        assert len(results) == 1
    
    def test_add_relationship(self):
        """测试添加关系"""
        from intentos.sdk import create_client
        from intentos.graph import IntentEdgeType
        client = create_client()
        
        intent1 = client.create_intent(name="意图 1")
        intent2 = client.create_intent(name="意图 2")
        
        edge = client.add_relationship(
            source_id=intent1.node_id,
            target_id=intent2.node_id,
            relationship=IntentEdgeType.TRIGGERS,
        )
        
        assert edge is not None
        assert edge.source_id == intent1.node_id
        assert edge.target_id == intent2.node_id
    
    def test_validate_dag(self):
        """测试 DAG 验证"""
        from intentos.sdk import create_client
        from intentos.verification import create_dag_node
        client = create_client()
        
        dag_nodes = [
            create_dag_node("task_1", "query", dependencies=[]),
            create_dag_node("task_2", "analyze", dependencies=["task_1"]),
            create_dag_node("task_3", "visualize", dependencies=["task_2"]),
        ]
        
        result = client.validate_dag(dag_nodes)
        
        assert "is_valid" in result
        assert "errors" in result
        assert "warnings" in result
    
    def test_register_capability(self):
        """测试注册能力"""
        from intentos.sdk import create_client
        client = create_client()
        
        signature = client.register_capability(
            name="test_capability",
            input_schema={"type": "object", "required": ["query"]},
            output_schema={"type": "object"},
            description="测试能力",
        )
        
        assert signature.name == "test_capability"
        assert signature.description == "测试能力"
    
    def test_validate_capability_call(self):
        """测试能力调用验证"""
        from intentos.sdk import create_client
        client = create_client()
        
        # 注册能力
        client.register_capability(
            name="test_cap",
            input_schema={"type": "object", "required": ["query"]},
            output_schema={"type": "object"},
        )
        
        # 验证有效调用
        result = client.validate_capability_call(
            "test_cap",
            {"query": "test"},
        )
        assert result["is_valid"] == True
        
        # 验证无效调用（缺少必需字段）
        result = client.validate_capability_call(
            "test_cap",
            {},
        )
        assert result["is_valid"] == False
    
    def test_trace_operations(self):
        """测试轨迹操作"""
        from intentos.sdk import create_client
        from intentos.verification import EventType
        client = create_client()
        
        # 创建轨迹
        trace = client.create_trace("intent_001")
        trace.add_event(EventType.TASK_START, "task_001")
        trace.add_event(EventType.TASK_END, "task_001")
        
        # 回放
        events = client.replay_trace(trace)
        assert len(events) == 2
        
        # 单步回放
        events = client.replay_trace(trace, step=1)
        assert len(events) == 1
    
    def test_export_import_graph(self):
        """测试图谱导出导入"""
        from intentos.sdk import create_client
        client = create_client()
        
        # 创建意图
        client.create_intent(name="意图 1", tags=["test"])
        client.create_intent(name="意图 2", tags=["test"])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # 导出
            client.export_graph(temp_path)
            
            # 清空图谱
            client.graph = client.graph.__class__()
            
            # 导入
            client.import_graph(temp_path)
            
            # 验证
            stats = client.get_graph_stats()
            assert stats["total_nodes"] == 2
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)