"""
意图图谱测试

测试意图图谱的核心功能：
1. 节点和边的增删查
2. 多跳查询
3. 相似度计算
4. 意图推荐
"""

import pytest
from intentos.graph import (
    IntentGraph,
    IntentNode,
    IntentEdge,
    IntentNodeType,
    IntentEdgeType,
    IntentSimilarityCalculator,
    IntentRecommender,
    create_intent_node,
    create_intent_edge,
    create_intent_graph,
)


class TestIntentNode:
    """测试意图节点"""
    
    def test_create_node(self):
        """测试创建节点"""
        node = create_intent_node(
            node_id="node_001",
            node_type=IntentNodeType.ATOMIC,
            name="分析销售数据",
            description="分析指定区域和时间的销售数据",
            tags=["销售", "分析", "数据"],
        )
        
        assert node.node_id == "node_001"
        assert node.node_type == IntentNodeType.ATOMIC
        assert node.name == "分析销售数据"
        assert len(node.tags) == 3
    
    def test_node_serialization(self):
        """测试节点序列化"""
        node = IntentNode(
            node_id="node_001",
            node_type=IntentNodeType.TEMPLATE,
            name="测试模板",
            description="测试描述",
            tags=["测试"],
        )
        
        # 序列化
        data = node.to_dict()
        
        # 反序列化
        restored = IntentNode.from_dict(data)
        
        assert restored.node_id == node.node_id
        assert restored.name == node.name
        assert restored.tags == node.tags


class TestIntentEdge:
    """测试意图边"""
    
    def test_create_edge(self):
        """测试创建边"""
        edge = create_intent_edge(
            edge_id="edge_001",
            source_id="node_001",
            target_id="node_002",
            edge_type=IntentEdgeType.DEPENDS_ON,
            weight=0.8,
        )
        
        assert edge.edge_id == "edge_001"
        assert edge.source_id == "node_001"
        assert edge.target_id == "node_002"
        assert edge.edge_type == IntentEdgeType.DEPENDS_ON
        assert edge.weight == 0.8


class TestIntentGraph:
    """测试意图图谱"""
    
    @pytest.fixture
    def sample_graph(self) -> IntentGraph:
        """创建示例图谱"""
        graph = IntentGraph()
        
        # 添加节点
        node1 = create_intent_node(
            node_id="node_001",
            node_type=IntentNodeType.ATOMIC,
            name="分析销售数据",
            tags=["销售", "分析"],
        )
        node2 = create_intent_node(
            node_id="node_002",
            node_type=IntentNodeType.ATOMIC,
            name="生成报表",
            tags=["报表", "生成"],
        )
        node3 = create_intent_node(
            node_id="node_003",
            node_type=IntentNodeType.COMPOSITE,
            name="销售分析完整流程",
            tags=["销售", "分析", "报表"],
        )
        
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        
        # 添加边
        edge1 = create_intent_edge(
            edge_id="edge_001",
            source_id="node_003",
            target_id="node_001",
            edge_type=IntentEdgeType.COMPOSED_OF,
        )
        edge2 = create_intent_edge(
            edge_id="edge_002",
            source_id="node_003",
            target_id="node_002",
            edge_type=IntentEdgeType.COMPOSED_OF,
        )
        edge3 = create_intent_edge(
            edge_id="edge_003",
            source_id="node_001",
            target_id="node_002",
            edge_type=IntentEdgeType.TRIGGERS,
        )
        
        graph.add_edge(edge1)
        graph.add_edge(edge2)
        graph.add_edge(edge3)
        
        return graph
    
    def test_add_node(self, sample_graph):
        """测试添加节点"""
        assert len(sample_graph.nodes) == 3
        assert sample_graph.get_node("node_001") is not None
    
    def test_remove_node(self, sample_graph):
        """测试删除节点"""
        sample_graph.remove_node("node_001")
        
        assert sample_graph.get_node("node_001") is None
        # 相关边也应该被删除
        assert "node_001" not in sample_graph.adjacency
    
    def test_add_edge(self, sample_graph):
        """测试添加边"""
        edge = create_intent_edge(
            edge_id="edge_004",
            source_id="node_001",
            target_id="node_003",
            edge_type=IntentEdgeType.REFINES,
        )
        sample_graph.add_edge(edge)
        
        neighbors = sample_graph.get_neighbors("node_001")
        assert len(neighbors) >= 1
    
    def test_get_neighbors(self, sample_graph):
        """测试获取邻居节点"""
        neighbors = sample_graph.get_neighbors("node_003")
        
        # node_003 应该有两个邻居（node_001 和 node_002）
        assert len(neighbors) == 2
        
        neighbor_ids = [n.node_id for n in neighbors]
        assert "node_001" in neighbor_ids
        assert "node_002" in neighbor_ids
    
    def test_find_path(self, sample_graph):
        """测试多跳查询（查找路径）"""
        paths = sample_graph.find_path("node_003", "node_002", max_depth=3)
        
        # 应该找到至少一条路径
        assert len(paths) > 0
        
        # 每条路径都应该从 node_003 开始，到 node_002 结束
        for path in paths:
            assert path[0] == "node_003"
            assert path[-1] == "node_002"
    
    def test_search_by_name(self, sample_graph):
        """测试按名称搜索"""
        results = sample_graph.search_by_name("分析销售数据")
        
        assert len(results) == 1
        assert results[0].node_id == "node_001"
    
    def test_search_by_tag(self, sample_graph):
        """测试按标签搜索"""
        results = sample_graph.search_by_tag("销售")
        
        # 应该找到 2 个节点（node_001 和 node_003）
        assert len(results) == 2
        
        result_ids = [r.node_id for r in results]
        assert "node_001" in result_ids
        assert "node_003" in result_ids
    
    def test_search_by_keyword(self, sample_graph):
        """测试按关键词搜索"""
        results = sample_graph.search_by_keyword("报表")
        
        assert len(results) == 2
        
        result_ids = [r.node_id for r in results]
        assert "node_002" in result_ids
        assert "node_003" in result_ids
    
    def test_get_statistics(self, sample_graph):
        """测试获取图谱统计"""
        stats = sample_graph.get_statistics()
        
        assert stats["total_nodes"] == 3
        assert stats["total_edges"] == 3
        assert "atomic" in stats["node_types"]
        assert "composite" in stats["node_types"]


@pytest.fixture
def sample_graph() -> IntentGraph:
    """创建示例图谱（模块级 fixture）"""
    graph = IntentGraph()
    
    # 添加节点
    node1 = create_intent_node(
        node_id="node_001",
        node_type=IntentNodeType.ATOMIC,
        name="分析销售数据",
        tags=["销售", "分析"],
    )
    node2 = create_intent_node(
        node_id="node_002",
        node_type=IntentNodeType.ATOMIC,
        name="生成报表",
        tags=["报表", "生成"],
    )
    node3 = create_intent_node(
        node_id="node_003",
        node_type=IntentNodeType.COMPOSITE,
        name="销售分析完整流程",
        tags=["销售", "分析", "报表"],
    )
    
    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)
    
    # 添加边
    edge1 = create_intent_edge(
        edge_id="edge_001",
        source_id="node_003",
        target_id="node_001",
        edge_type=IntentEdgeType.COMPOSED_OF,
    )
    edge2 = create_intent_edge(
        edge_id="edge_002",
        source_id="node_003",
        target_id="node_002",
        edge_type=IntentEdgeType.COMPOSED_OF,
    )
    edge3 = create_intent_edge(
        edge_id="edge_003",
        source_id="node_001",
        target_id="node_002",
        edge_type=IntentEdgeType.TRIGGERS,
    )
    
    graph.add_edge(edge1)
    graph.add_edge(edge2)
    graph.add_edge(edge3)
    
    return graph


class TestIntentSimilarityCalculator:
    """测试意图相似度计算"""
    
    def test_jaccard_similarity(self):
        """测试 Jaccard 相似度"""
        calc = IntentSimilarityCalculator()
        
        # 完全相同
        assert calc.jaccard_similarity({1, 2, 3}, {1, 2, 3}) == 1.0
        
        # 完全不同
        assert calc.jaccard_similarity({1, 2}, {3, 4}) == 0.0
        
        # 部分重叠
        assert abs(calc.jaccard_similarity({1, 2, 3}, {2, 3, 4}) - 0.5) < 0.01
    
    def test_calculate_similarity(self):
        """测试相似度计算"""
        calc = IntentSimilarityCalculator()
        
        node1 = IntentNode(
            node_id="node_001",
            node_type=IntentNodeType.ATOMIC,
            name="分析销售数据",
            description="分析销售数据并生成报表",
            tags=["销售", "分析", "数据"],
        )
        
        node2 = IntentNode(
            node_id="node_002",
            node_type=IntentNodeType.ATOMIC,
            name="分析销售数据",
            description="分析销售数据并生成报表",
            tags=["销售", "分析", "数据"],
        )
        
        # 完全相同的节点
        similarity = calc.calculate(node1, node2)
        assert similarity == 1.0
        
        node3 = IntentNode(
            node_id="node_003",
            node_type=IntentNodeType.ATOMIC,
            name="生成财务报表",
            description="生成各种财务报表",
            tags=["财务", "报表", "生成"],
        )
        
        # 不同的节点
        similarity = calc.calculate(node1, node3)
        assert 0.0 <= similarity < 1.0
    
    def test_find_similar_intents(self, sample_graph):
        """测试查找相似意图"""
        calc = IntentSimilarityCalculator()
        
        node = sample_graph.get_node("node_001")
        similar = calc.find_similar_intents(node, sample_graph, threshold=0.1)
        
        # 应该找到至少一个相似节点
        assert len(similar) > 0


class TestIntentRecommender:
    """测试意图推荐"""
    
    def test_recommend_by_node(self, sample_graph):
        """测试基于节点的推荐"""
        recommender = IntentRecommender(sample_graph)
        
        recommendations = recommender.recommend_by_node("node_003", num_recommendations=2)
        
        # 应该推荐 2 个节点
        assert len(recommendations) == 2
        
        # 推荐的应该是 node_001 和 node_002
        rec_ids = [r.node_id for r in recommendations]
        assert "node_001" in rec_ids
        assert "node_002" in rec_ids
    
    def test_recommend_by_context(self, sample_graph):
        """测试基于上下文的推荐"""
        recommender = IntentRecommender(sample_graph)
        
        recommendations = recommender.recommend_by_context(
            context_tags=["销售", "报表"],
            num_recommendations=2,
        )
        
        # 应该推荐匹配的节点
        assert len(recommendations) > 0


class TestIntentGraphSerialization:
    """测试图谱序列化"""
    
    def test_graph_to_dict(self, sample_graph):
        """测试图谱序列化"""
        data = sample_graph.to_dict()
        
        assert "nodes" in data
        assert "edges" in data
        assert "statistics" in data
        
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 3
    
    def test_graph_from_dict(self, sample_graph):
        """测试图谱反序列化"""
        # 序列化
        data = sample_graph.to_dict()
        
        # 反序列化
        restored = IntentGraph()
        for node_data in data["nodes"].values():
            node = IntentNode.from_dict(node_data)
            restored.add_node(node)
        
        for edge_data in data["edges"].values():
            edge = IntentEdge.from_dict(edge_data)
            restored.add_edge(edge)
        
        # 验证
        assert len(restored.nodes) == len(sample_graph.nodes)
        assert len(restored.edges) == len(sample_graph.edges)


class TestIntentGraphEdgeCases:
    """测试边界情况"""
    
    def test_empty_graph(self):
        """测试空图谱"""
        graph = IntentGraph()
        
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
        
        stats = graph.get_statistics()
        assert stats["total_nodes"] == 0
        assert stats["total_edges"] == 0
    
    def test_bidirectional_edge(self):
        """测试双向边（无向关系）"""
        graph = IntentGraph()
        
        node1 = create_intent_node("n1", IntentNodeType.ATOMIC, "节点 1")
        node2 = create_intent_node("n2", IntentNodeType.ATOMIC, "节点 2")
        
        graph.add_node(node1)
        graph.add_node(node2)
        
        # 添加 SIMILAR_TO 关系（应该是双向的）
        edge = create_intent_edge(
            "e1", "n1", "n2", IntentEdgeType.SIMILAR_TO
        )
        graph.add_edge(edge)
        
        # 应该可以从两个方向访问
        neighbors_1 = graph.get_neighbors("n1")
        neighbors_2 = graph.get_neighbors("n2")
        
        assert len(neighbors_1) == 1
        assert len(neighbors_2) == 1
        assert neighbors_1[0].node_id == "n2"
        assert neighbors_2[0].node_id == "n1"
    
    def test_path_not_found(self, sample_graph):
        """测试路径不存在"""
        # 添加一个孤立节点
        isolated = create_intent_node("isolated", IntentNodeType.ATOMIC, "孤立节点")
        sample_graph.add_node(isolated)
        
        # 查找路径应该返回空列表
        paths = sample_graph.find_path("node_001", "isolated", max_depth=3)
        assert len(paths) == 0
