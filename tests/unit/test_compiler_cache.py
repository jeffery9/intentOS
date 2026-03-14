"""
Compiler Cache 模块测试 - 修复版本
"""

import asyncio
from datetime import datetime, timedelta

import pytest

from intentos.compiler.cache import (
    CacheEntry,
    MemoryCache,
    generate_cache_key,
)


class TestGenerateCacheKey:
    """generate_cache_key 测试"""

    def test_generate_simple_key(self):
        key = generate_cache_key("test")
        assert key is not None
        assert len(key) > 0


class TestCacheEntry:
    """CacheEntry 测试"""

    def test_entry_creation(self):
        entry = CacheEntry(key="test_key", value={"data": "test"})
        assert entry.key == "test_key"
        assert entry.access_count == 0

    def test_entry_with_ttl(self):
        entry = CacheEntry(key="ttl_key", value="value", ttl_seconds=3600)
        assert entry.ttl_seconds == 3600

    def test_entry_is_expired_no_ttl(self):
        entry = CacheEntry(key="key", value="value")
        assert entry.is_expired() is False

    def test_entry_is_expired_with_ttl(self):
        entry = CacheEntry(key="key", value="value", ttl_seconds=1)
        entry.created_at = datetime.now() - timedelta(seconds=2)
        assert entry.is_expired() is True

    def test_entry_touch(self):
        entry = CacheEntry(key="key", value="value")
        initial_access = entry.access_count
        entry.touch()
        assert entry.access_count == initial_access + 1

    def test_entry_to_dict(self):
        entry = CacheEntry(key="dict_key", value={"nested": "data"}, ttl_seconds=1800)
        data = entry.to_dict()
        assert data["key"] == "dict_key"
        assert data["ttl_seconds"] == 1800

    def test_entry_from_dict(self):
        now = datetime.now()
        data = {
            "key": "restored_key",
            "value": [1, 2, 3],
            "created_at": now.isoformat(),
            "last_accessed": now.isoformat(),
            "access_count": 5,
            "ttl_seconds": 7200,
        }
        entry = CacheEntry.from_dict(data)
        assert entry.key == "restored_key"
        assert entry.access_count == 5


class TestMemoryCacheAsync:
    """MemoryCache 异步测试"""

    @pytest.mark.asyncio
    async def test_cache_creation(self):
        cache = MemoryCache()
        assert cache.max_size == 1000
        assert cache.default_ttl == 3600

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        cache = MemoryCache()
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"

    @pytest.mark.asyncio
    async def test_cache_get_nonexistent(self):
        cache = MemoryCache()
        value = await cache.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        cache = MemoryCache()
        await cache.set("to_delete", "value")
        result = await cache.delete("to_delete")
        assert result is True

    @pytest.mark.asyncio
    async def test_cache_clear(self):
        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        assert len(cache._cache) == 0

    @pytest.mark.asyncio
    async def test_cache_get_stats(self):
        cache = MemoryCache()
        await cache.set("key1", "value1")
        stats = cache.get_stats()
        assert "cache_size" in stats
        assert stats["cache_size"] == 1

    @pytest.mark.asyncio
    async def test_cache_max_size_limit(self):
        cache = MemoryCache(max_size=3)
        for i in range(4):
            await cache.set(f"key{i}", f"value{i}")
        assert len(cache._cache) <= 3

    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self):
        cache = MemoryCache(max_size=3)
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        await cache.get("key1")
        await cache.set("key4", "value4")
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        cache = MemoryCache(default_ttl_seconds=1)
        await cache.set("expires", "value")
        await asyncio.sleep(1.1)
        value = await cache.get("expires")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_size_via_cache_dict(self):
        cache = MemoryCache()
        await cache.set("key1", "value1")
        assert len(cache._cache) == 1

    @pytest.mark.asyncio
    async def test_cache_multiple_operations(self):
        cache = MemoryCache(max_size=100)
        for i in range(50):
            await cache.set(f"key{i}", f"value{i}")
        for i in range(50):
            assert await cache.get(f"key{i}") == f"value{i}"
        assert len(cache._cache) == 50

    @pytest.mark.asyncio
    async def test_cache_stats_tracking(self):
        cache = MemoryCache()
        await cache.set("key1", "value1")
        await cache.get("key1")
        assert cache.stats["hits"] == 1
        await cache.get("nonexistent")
        assert cache.stats["misses"] == 1


class TestCacheIntegration:
    """缓存集成测试"""

    @pytest.mark.asyncio
    async def test_cache_workflow(self):
        cache = MemoryCache(max_size=10)
        await cache.set("workflow", "data")
        value = await cache.get("workflow")
        assert value == "data"
        await cache.delete("workflow")
        value = await cache.get("workflow")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_with_complex_values(self):
        cache = MemoryCache()
        complex_value = {"nested": {"data": [1, 2, 3]}}
        await cache.set("complex", complex_value)
        retrieved = await cache.get("complex")
        assert retrieved["nested"]["data"] == [1, 2, 3]
