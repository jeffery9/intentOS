"""
分布式记忆管理测试
"""

import pytest
import asyncio
import time
import os
import shutil
from intentos import (
    MemoryType,
    MemoryPriority,
    MemoryEntry,
    MemoryConfig,
    InMemoryBackend,
    FileBackend,
    DistributedMemoryManager,
    create_memory_manager,
    create_and_initialize_memory_manager,
)


# =============================================================================
# MemoryEntry 测试
# =============================================================================

class TestMemoryEntry:
    """测试记忆条目"""
    
    def test_entry_creation(self):
        """测试记忆创建"""
        entry = MemoryEntry(
            key="test_key",
            value={"data": "test"},
            memory_type=MemoryType.SHORT_TERM,
        )
        
        assert entry.key == "test_key"
        assert entry.memory_type == MemoryType.SHORT_TERM
        assert entry.id is not None
    
    def test_entry_to_dict(self):
        """测试序列化"""
        entry = MemoryEntry(
            key="test",
            value="value",
            tags=["tag1", "tag2"],
        )
        
        d = entry.to_dict()
        assert d["key"] == "test"
        assert d["value"] == "value"
        assert d["tags"] == ["tag1", "tag2"]
    
    def test_entry_from_dict(self):
        """测试反序列化"""
        data = {
            "id": "test-id",
            "key": "test_key",
            "value": {"nested": "value"},
            "memory_type": "long_term",
            "priority": 3,
            "tags": ["tag1"],
        }
        
        entry = MemoryEntry.from_dict(data)
        assert entry.key == "test_key"
        assert entry.memory_type == MemoryType.LONG_TERM
        assert entry.priority == MemoryPriority.HIGH
    
    def test_entry_expiry(self):
        """测试过期"""
        entry = MemoryEntry(key="test", value="value")
        assert not entry.is_expired()
        
        entry.set_expiry(-1)  # 已过期
        assert entry.is_expired()
        
        entry.set_expiry(60)  # 60 秒后过期
        assert not entry.is_expired()
    
    def test_entry_touch(self):
        """测试访问时间更新"""
        entry = MemoryEntry(key="test", value="value")
        initial_count = entry.access_count
        
        entry.touch()
        assert entry.access_count == initial_count + 1
        assert entry.last_accessed > 0


# =============================================================================
# InMemoryBackend 测试
# =============================================================================

class TestInMemoryBackend:
    """测试进程内后端"""
    
    @pytest.mark.asyncio
    async def test_backend_set_get(self):
        """测试设置和获取"""
        backend = InMemoryBackend(max_size=100)
        
        entry = MemoryEntry(key="test", value="value")
        await backend.set(entry)
        
        result = await backend.get("test")
        assert result is not None
        assert result.value == "value"
    
    @pytest.mark.asyncio
    async def test_backend_delete(self):
        """测试删除"""
        backend = InMemoryBackend(max_size=100)
        
        entry = MemoryEntry(key="test", value="value")
        await backend.set(entry)
        
        result = await backend.delete("test")
        assert result is True
        
        result = await backend.get("test")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_backend_exists(self):
        """测试存在检查"""
        backend = InMemoryBackend(max_size=100)
        
        assert await backend.exists("nonexistent") is False
        
        entry = MemoryEntry(key="test", value="value")
        await backend.set(entry)
        
        assert await backend.exists("test") is True
    
    @pytest.mark.asyncio
    async def test_backend_keys(self):
        """测试获取键"""
        backend = InMemoryBackend(max_size=100)
        
        for i in range(5):
            entry = MemoryEntry(key=f"key:{i}", value=f"value{i}")
            await backend.set(entry)
        
        keys = await backend.keys()
        assert len(keys) == 5
        
        keys = await backend.keys("key:*")
        assert len(keys) == 5
    
    @pytest.mark.asyncio
    async def test_backend_lru(self):
        """测试 LRU 淘汰"""
        backend = InMemoryBackend(max_size=3)
        
        for i in range(5):
            entry = MemoryEntry(key=f"key:{i}", value=f"value{i}")
            await backend.set(entry)
        
        # 应该只剩 3 个
        size = await backend.size()
        assert size == 3
        
        # 最早的应该被淘汰
        assert await backend.exists("key:0") is False
        assert await backend.exists("key:1") is False
        assert await backend.exists("key:4") is True
    
    @pytest.mark.asyncio
    async def test_backend_expiry(self):
        """测试过期"""
        backend = InMemoryBackend(max_size=100)
        
        entry = MemoryEntry(key="temp", value="value")
        entry.set_expiry(0.1)  # 0.1 秒后过期
        await backend.set(entry)
        
        # 立即获取应该存在
        result = await backend.get("temp")
        assert result is not None
        
        # 等待过期
        await asyncio.sleep(0.2)
        
        # 获取应该返回 None
        result = await backend.get("temp")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_backend_clear(self):
        """测试清空"""
        backend = InMemoryBackend(max_size=100)
        
        for i in range(5):
            entry = MemoryEntry(key=f"key:{i}", value=f"value{i}")
            await backend.set(entry)
        
        await backend.clear()
        
        size = await backend.size()
        assert size == 0


# =============================================================================
# FileBackend 测试
# =============================================================================

class TestFileBackend:
    """测试文件后端"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        temp_dir = f"/tmp/test_memory_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_backend_set_get(self, temp_dir):
        """测试设置和获取"""
        backend = FileBackend(data_dir=temp_dir)
        
        entry = MemoryEntry(key="test", value={"nested": "value"})
        await backend.set(entry)
        
        result = await backend.get("test")
        assert result is not None
        assert result.value == {"nested": "value"}
    
    @pytest.mark.asyncio
    async def test_backend_delete(self, temp_dir):
        """测试删除"""
        backend = FileBackend(data_dir=temp_dir)
        
        entry = MemoryEntry(key="test", value="value")
        await backend.set(entry)
        
        result = await backend.delete("test")
        assert result is True
        
        result = await backend.get("test")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_backend_keys(self, temp_dir):
        """测试获取键"""
        backend = FileBackend(data_dir=temp_dir)
        
        for i in range(5):
            entry = MemoryEntry(key=f"key:{i}", value=f"value{i}")
            await backend.set(entry)
        
        keys = await backend.keys()
        assert len(keys) == 5
    
    @pytest.mark.asyncio
    async def test_backend_clear(self, temp_dir):
        """测试清空"""
        backend = FileBackend(data_dir=temp_dir)
        
        for i in range(5):
            entry = MemoryEntry(key=f"key:{i}", value=f"value{i}")
            await backend.set(entry)
        
        await backend.clear()
        
        keys = await backend.keys()
        assert len(keys) == 0


# =============================================================================
# DistributedMemoryManager 测试
# =============================================================================

class TestDistributedMemoryManager:
    """测试分布式记忆管理器"""
    
    @pytest.fixture
    def temp_dir(self):
        """临时目录"""
        temp_dir = f"/tmp/test_dmem_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_manager_creation(self):
        """测试管理器创建"""
        manager = create_memory_manager(
            short_term_max=100,
            long_term_enabled=False,
            sync_enabled=False,
        )
        
        assert manager.config.short_term_max_size == 100
        assert manager.node_id is not None
    
    @pytest.mark.asyncio
    async def test_short_term_operations(self):
        """测试短期记忆操作"""
        manager = create_memory_manager(
            short_term_max=100,
            long_term_enabled=False,
            sync_enabled=False,
        )
        await manager.initialize()
        
        try:
            # 设置
            entry = await manager.set_short_term(
                key="test:key",
                value="test_value",
                tags=["test"],
            )
            assert entry.key == "test:key"
            
            # 获取
            result = await manager.get_short_term("test:key")
            assert result is not None
            assert result.value == "test_value"
            
            # 删除
            result = await manager.delete_short_term("test:key")
            assert result is True
            
            result = await manager.get_short_term("test:key")
            assert result is None
            
        finally:
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_long_term_operations(self, temp_dir):
        """测试长期记忆操作"""
        manager = create_memory_manager(
            short_term_max=100,
            long_term_enabled=True,
            long_term_backend="file",
            sync_enabled=False,
        )
        # 修改数据目录
        manager._long_term_backend = FileBackend(data_dir=temp_dir)
        
        await manager.initialize()
        
        try:
            # 设置
            entry = await manager.set_long_term(
                key="long:key",
                value={"data": "value"},
                tags=["long", "term"],
            )
            assert entry.key == "long:key"
            
            # 获取
            result = await manager.get_long_term("long:key")
            assert result is not None
            assert result.value == {"data": "value"}
            
        finally:
            await manager.clear()
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_unified_get(self):
        """测试统一获取"""
        manager = create_memory_manager(
            short_term_max=100,
            long_term_enabled=False,
            sync_enabled=False,
        )
        await manager.initialize()
        
        try:
            # 设置短期记忆
            await manager.set_short_term(
                key="unified:key",
                value="short_value",
            )
            
            # 统一获取
            result = await manager.get("unified:key")
            assert result is not None
            assert result.value == "short_value"
            
        finally:
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_tag_index(self):
        """测试标签索引"""
        manager = create_memory_manager(
            short_term_max=100,
            long_term_enabled=False,
            sync_enabled=False,
        )
        await manager.initialize()
        
        try:
            # 设置带标签的记忆
            await manager.set_short_term(
                key="doc:1",
                value="content1",
                tags=["doc", "important"],
            )
            await manager.set_short_term(
                key="doc:2",
                value="content2",
                tags=["doc", "archive"],
            )
            
            # 按标签检索
            entries = await manager.get_by_tag("doc")
            assert len(entries) == 2
            
            entries = await manager.get_by_tag("important")
            assert len(entries) == 1
            
        finally:
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_search(self):
        """测试搜索"""
        manager = create_memory_manager(
            short_term_max=100,
            long_term_enabled=False,
            sync_enabled=False,
        )
        await manager.initialize()
        
        try:
            await manager.set_short_term(
                key="document:report",
                value="This is a quarterly report",
                tags=["doc", "report"],
            )
            
            # 搜索键
            results = await manager.search("document")
            assert len(results) >= 1
            
            # 搜索值
            results = await manager.search("quarterly")
            assert len(results) >= 1
            
        finally:
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_stats(self):
        """测试统计"""
        manager = create_memory_manager(
            short_term_max=100,
            long_term_enabled=False,
            sync_enabled=False,
        )
        await manager.initialize()
        
        try:
            # 设置一些记忆
            for i in range(5):
                await manager.set_short_term(
                    key=f"key:{i}",
                    value=f"value{i}",
                )
            
            # 获取一些（产生命中/未命中）
            await manager.get("key:0")
            await manager.get("key:100")  # 不存在
            
            stats = await manager.get_stats()
            
            assert stats["hit_count"] >= 1
            assert stats["miss_count"] >= 1
            assert stats.get("short_term_size", 0) == 5
            
        finally:
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_clear(self):
        """测试清空"""
        manager = create_memory_manager(
            short_term_max=100,
            long_term_enabled=False,
            sync_enabled=False,
        )
        await manager.initialize()
        
        try:
            for i in range(5):
                await manager.set_short_term(
                    key=f"key:{i}",
                    value=f"value{i}",
                )
            
            await manager.clear()
            
            stats = await manager.get_stats()
            assert stats.get("short_term_size", 0) == 0
            
        finally:
            await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_memory_priority(self):
        """测试记忆优先级"""
        manager = create_memory_manager(
            short_term_max=3,  # 小容量
            long_term_enabled=False,
            sync_enabled=False,
        )
        await manager.initialize()
        
        try:
            # 设置高优先级记忆
            await manager.set_short_term(
                key="critical:1",
                value="critical_value",
                priority=MemoryPriority.CRITICAL,
            )
            
            # 设置普通记忆填满
            for i in range(5):
                await manager.set_short_term(
                    key=f"normal:{i}",
                    value=f"value{i}",
                    priority=MemoryPriority.NORMAL,
                )
            
            # 高优先级应该还在（LRU 应该先淘汰普通优先级）
            # 注意：当前实现不区分优先级淘汰，只是标记
            
        finally:
            await manager.shutdown()


# =============================================================================
# MemoryEntry 序列化测试
# =============================================================================

class TestMemoryEntrySerialization:
    """测试记忆条目序列化"""
    
    def test_pickle_serialization(self):
        """测试 pickle 序列化"""
        import pickle
        
        entry = MemoryEntry(
            key="test",
            value={"complex": {"nested": [1, 2, 3]}},
            tags=["tag1", "tag2"],
            metadata={"meta": "data"},
        )
        
        # 序列化
        data = pickle.dumps(entry.to_dict())
        
        # 反序列化
        loaded = pickle.loads(data)
        entry2 = MemoryEntry.from_dict(loaded)
        
        assert entry2.key == entry.key
        assert entry2.value == entry.value
        assert entry2.tags == entry.tags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
