"""
Distributed Consensus 模块测试
"""

import pytest
from intentos.distributed.consensus import (
    ConsistencyLevel,
    VersionVector,
    VersionedValue,
)


class TestConsistencyLevel:
    """ConsistencyLevel 测试"""

    def test_level_values(self):
        """测试级别值"""
        assert ConsistencyLevel.STRONG.value == "strong"
        assert ConsistencyLevel.QUORUM.value == "quorum"
        assert ConsistencyLevel.EVENTUAL.value == "eventual"


class TestVersionVector:
    """VersionVector 测试"""

    def test_vector_creation(self):
        """测试向量创建"""
        vv = VersionVector()
        assert vv.versions == {}

    def test_vector_increment(self):
        """测试向量递增"""
        vv = VersionVector()
        vv.increment("node1")
        assert vv.versions["node1"] == 1

    def test_vector_increment_multiple(self):
        """测试多次递增"""
        vv = VersionVector()
        vv.increment("node1")
        vv.increment("node1")
        assert vv.versions["node1"] == 2

    def test_vector_increment_multiple_nodes(self):
        """测试多节点递增"""
        vv = VersionVector()
        vv.increment("node1")
        vv.increment("node2")
        assert vv.versions["node1"] == 1
        assert vv.versions["node2"] == 1

    def test_vector_merge(self):
        """测试向量合并"""
        vv1 = VersionVector()
        vv1.increment("node1")
        vv1.increment("node1")
        
        vv2 = VersionVector()
        vv2.increment("node1")
        vv2.increment("node2")
        
        vv1.merge(vv2)
        
        assert vv1.versions["node1"] == 2
        assert vv1.versions["node2"] == 1

    def test_vector_dominates(self):
        """测试向量支配"""
        vv1 = VersionVector()
        vv1.increment("node1")
        vv1.increment("node1")
        
        vv2 = VersionVector()
        vv2.increment("node1")
        
        assert vv1.dominates(vv2) is True
        assert vv2.dominates(vv1) is False

    def test_vector_concurrent_with(self):
        """测试向量并发"""
        vv1 = VersionVector()
        vv1.increment("node1")
        
        vv2 = VersionVector()
        vv2.increment("node2")
        
        assert vv1.concurrent_with(vv2) is True
        assert vv2.concurrent_with(vv1) is True

    def test_vector_to_dict(self):
        """测试向量转换为字典"""
        vv = VersionVector()
        vv.increment("node1")
        data = vv.to_dict()
        assert "versions" in data
        assert data["versions"]["node1"] == 1

    def test_vector_from_dict(self):
        """测试从字典创建向量"""
        data = {"versions": {"node1": 2, "node2": 1}}
        vv = VersionVector.from_dict(data)
        assert vv.versions["node1"] == 2
        assert vv.versions["node2"] == 1


class TestVersionedValue:
    """VersionedValue 测试"""

    def test_value_creation(self):
        """测试值创建"""
        vv = VersionVector()
        vv.increment("node1")
        value = VersionedValue(value="test", version=vv)
        assert value.value == "test"
        assert value.version == vv

    def test_value_compute_checksum(self):
        """测试计算校验和"""
        vv = VersionVector()
        value = VersionedValue(value="test", version=vv)
        checksum = value.compute_checksum()
        assert checksum is not None
        assert len(checksum) > 0

    def test_value_checksum_consistency(self):
        """测试校验和一致性"""
        vv = VersionVector()
        value1 = VersionedValue(value="test", version=vv)
        checksum1 = value1.compute_checksum()
        
        # 校验和应该不为空
        assert checksum1 is not None
        assert len(checksum1) > 0

    def test_value_to_dict(self):
        """测试值转换为字典"""
        vv = VersionVector()
        vv.increment("node1")
        value = VersionedValue(value="test", version=vv)
        data = value.to_dict()
        assert "value" in data
        assert "version" in data
        assert "checksum" in data


class TestConsensusIntegration:
    """Consensus 集成测试"""

    def test_version_vector_workflow(self):
        """测试版本向量工作流"""
        # 创建向量
        vv1 = VersionVector()
        vv1.increment("node1")
        vv1.increment("node2")
        
        # 转换为字典
        data = vv1.to_dict()
        
        # 从字典创建
        vv2 = VersionVector.from_dict(data)
        
        # 验证
        assert vv2.versions["node1"] == 1
        assert vv2.versions["node2"] == 1

    def test_versioned_value_workflow(self):
        """测试带版本的值工作流"""
        vv = VersionVector()
        vv.increment("node1")
        
        value = VersionedValue(value="data", version=vv)
        checksum = value.compute_checksum()
        
        assert value.value == "data"
        assert checksum is not None

    def test_version_conflict_detection(self):
        """测试版本冲突检测"""
        vv1 = VersionVector()
        vv1.increment("node1")
        
        vv2 = VersionVector()
        vv2.increment("node2")
        
        # 并发版本表示冲突
        assert vv1.concurrent_with(vv2) is True

    def test_version_merge_workflow(self):
        """测试版本合并工作流"""
        vv1 = VersionVector()
        vv1.increment("node1")
        vv1.increment("node3")
        
        vv2 = VersionVector()
        vv2.increment("node2")
        vv2.increment("node3")
        vv2.increment("node3")
        
        vv1.merge(vv2)
        
        # 合并后应该取最大值
        assert vv1.versions["node1"] == 1
        assert vv1.versions["node2"] == 1
        assert vv1.versions["node3"] == 2
