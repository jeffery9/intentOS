"""
Compiler Cache 模块测试

覆盖 MemoryCache 和 CacheEntry（异步版本）
"""

import pytest
import asyncio
from intentos.compiler.cache import (
    CacheEntry,
    MemoryCache,
    generate_cache_key,
)
from datetime import datetime, timedelta


# =============================================================================
# generate_cache_key Tests
# =============================================================================

class TestGenerateCacheKey:
    """generate_cache_key 测试"""

    def test_generate_simple_key(self):
        """测试生成简单键"""
        key = generate_cache_key("test")
        
        assert key is not None
        assert len(key) > 0
        assert isinstance(key, str)

    def test_generate_key_with_params(self):
        """测试生成带参数的键"""
        key1 = generate_cache_key("test", {"a": 1})
        key2 = generate_cache_key("test", {"a": 1})
        
        assert key1 == key2

    def test_generate_key_different_params(self):
        """测试不同参数生成不同键"""
        key1 = generate_cache_key("test", {"a": 1})
        key2 = generate_cache_key("test", {"a": 2})
        
        assert key1 != key2


# =============================================================================
# CacheEntry Tests
# =============================================================================

class TestCacheEntry:
    """CacheEntry 测试"""

    def test_entry_creation(self):
        """测试缓存条目创建"""
        entry = CacheEntry(
            key="test_key",
            value={"data": "test"}
        )
        
        assert entry.key == "test_key"
        assert entry.value == {"data": "test"}
        assert entry.access_count == 0
        assert entry.ttl_seconds is None

    def test_entry_with_ttl(self):
        """测试带 TTL 的缓存条目"""
        entry = CacheEntry(
            key="ttl_key",
            value="value",
            ttl_seconds=3600
        )
        
        assert entry.ttl_seconds == 3600

    def test_entry_is_expired_no_ttl(self):
        """测试无 TTL 的条目不过期"""
        entry = CacheEntry(key="key", value="value")
        assert entry.is_expired() is False

    def test_entry_is_expired_with_ttl(self):
        """测试带 TTL 的条目过期"""
        entry = CacheEntry(key="key", value="value", ttl_seconds=1)
        entry.created_at = datetime.now() - timedelta(seconds=2)
        assert entry.is_expired() is True

    def test_entry_touch(self):
        """测试 touch 方法"""
        entry = CacheEntry(key="key", value="value")
        initial_access = entry.access_count
        entry.touch()
        assert entry.access_count == initial_access + 1

    def test_entry_to_dict(self):
        """测试转换为字典"""
        entry = CacheEntry(key="dict_key", value={"nested": "data"}, ttl_seconds=1800)
        data = entry.to_dict()
        assert data["key"] == "dict_key"
        assert data["ttl_seconds"] == 1800

    def test_entry_from_dict(self):
        """测试从字典创建"""
        now = datetime.now()
        data = {
            "key": "restored_key",
            "value": [1, 2, 3],
            "created_at": now.isoformat(),
            "last_accessed": now.isoformat(),
            "access_count": 5,
            "ttl_seconds": 7200
        }
        entry = CacheEntry.from_dict(data)
        assert entry.key == "restored_key"
        assert entry.access_count == 5


# =============================================================================
# MemoryCache Tests (Async)
# =============================================================================

class TestMemoryCacheAsync:
    """MemoryCache 异步测试"""

    @pytest.mark.asyncio
    async def test_cache_creation(self):
        """测试缓存创建"""
        cache = MemoryCache()
        assert cache.max_size == 1000
        assert cache.default_ttl == 3600

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """测试设置和获取"""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_cache_get_nonexistent(self):
        """测试获取不存在的键"""
        cache = MemoryCache()
        value = await cache.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """测试删除"""
        cache = MemoryCache()
        await cache.set("to_delete", "value")
        result = await cache.delete("to_delete")
        assert result is True
        assert await cache.get("to_delete") is None

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """测试清空"""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert cache.size == 0

    @pytest.mark.asyncio
    async def test_cache_contains(self):
        """测试包含检查"""
        cache = MemoryCache()
        await cache.set("exists", "value")
        assert cache.contains("exists") is True
        assert cache.contains("not_exists") is False

    @pytest.mark.asyncio
    async def test_cache_get_stats(self):
        """测试获取统计"""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        stats = cache.get_stats()
        assert "size" in stats
        assert stats["size"] == 1

    @pytest.mark.asyncio
    async def test_cache_max_size_limit(self):
        """测试最大大小限制"""
        cache = MemoryCache(max_size=3)
        for i in range(4):
            await cache.set(f"key{i}", f"value{i}")
        assert cache.size <= 3

    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self):
        """测试 LRU 淘汰"""
        cache = MemoryCache(max_size=3)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        await cache.get("key1")  # 访问 key1
        await cache.set("key4", "value4")  # 应该淘汰 key2
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """测试 TTL 过期"""
        cache = MemoryCache(default_ttl_seconds=1)
        await cache.set("expires", "value")
        await asyncio.sleep(1.1)
        value = await cache.get("expires")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_size_property(self):
        """测试 size 属性"""
        cache = MemoryCache()
        assert cache.size == 0
        await cache.set("key1", "value1")
        assert cache.size == 1

    @pytest.mark.asyncio
    async def test_cache_multiple_operations(self):
        """测试多次操作"""
        cache = MemoryCache(max_size=100)
        for i in range(50):
            await cache.set(f"key{i}", f"value{i}")
        for i in range(50):
            assert await cache.get(f"key{i}") == f"value{i}"
        assert cache.size == 50

    @pytest.mark.asyncio
    async def test_cache_stats_tracking(self):
        """测试统计追踪"""
        cache = MemoryCache()
        await cache.set("key1", "value1")
        
        # Hit
        await cache.get("key1")
        assert cache.stats["hits"] == 1
        
        # Miss
        await cache.get("nonexistent")
        assert cache.stats["misses"] == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestCacheIntegration:
    """缓存集成测试"""

    @pytest.mark.asyncio
    async def test_cache_workflow(self):
        """测试缓存工作流"""
        cache = MemoryCache(max_size=10)
        await cache.set("workflow", "data")
        assert cache.contains("workflow") is True
        value = await cache.get("workflow")
        assert value == "data"
        await cache.delete("workflow")
        assert cache.contains("workflow") is False

    @pytest.mark.asyncio
    async def test_cache_with_complex_values(self):
        """测试带复杂值的缓存"""
        cache = MemoryCache()
        complex_value = {"nested": {"data": [1, 2, 3]}}
        await cache.set("complex", complex_value)
        retrieved = await cache.get("complex")
        assert retrieved["nested"]["data"] == [1, 2, 3]
