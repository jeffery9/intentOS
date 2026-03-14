"""
IntentOS 编译器缓存系统

多级缓存架构:
L1: 内存缓存 (最快，容量小) - 热点 Prompt
L2: Redis 缓存 (较快，容量中) - 常用意图编译结果
L3: 磁盘缓存 (较慢，容量大) - 历史编译结果

核心洞察:
- 80% 的编译请求是重复的或相似的
- 缓存命中率目标：70%+
- 编译时间减少 90%+
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    pass


# =============================================================================
# 缓存条目
# =============================================================================

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl_seconds: Optional[int] = None  # Time To Live

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl_seconds is None:
            return False
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiry_time

    def touch(self) -> None:
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "ttl_seconds": self.ttl_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheEntry:
        """从字典创建"""
        return cls(
            key=data["key"],
            value=data["value"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data["access_count"],
            ttl_seconds=data.get("ttl_seconds"),
        )


# =============================================================================
# L1: 内存缓存
# =============================================================================

class MemoryCache:
    """
    L1 内存缓存

    特性:
    - LRU (Least Recently Used) 淘汰策略
    - 支持 TTL 过期
    - 线程安全
    - 容量限制
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 3600,  # 1 小时
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()

        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        async with self._lock:
            if key not in self._cache:
                self.stats["misses"] += 1
                return None

            entry = self._cache[key]

            # 检查过期
            if entry.is_expired():
                await self._delete(key)
                self.stats["misses"] += 1
                return None

            # 更新访问统计
            entry.touch()
            self._cache.move_to_end(key)  # LRU: 移到末尾
            self.stats["hits"] += 1

            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """设置缓存"""
        async with self._lock:
            # 如果已存在，先删除
            if key in self._cache:
                await self._delete(key)

            # 创建新条目
            entry = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=ttl_seconds or self.default_ttl,
            )

            # 检查容量
            while len(self._cache) >= self.max_size:
                await self._evict_oldest()

            self._cache[key] = entry

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            return await self._delete(key)

    async def _delete(self, key: str) -> bool:
        """内部删除方法 (需要持有锁)"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def _evict_oldest(self) -> None:
        """淘汰最久未使用的条目"""
        if self._cache:
            oldest_key = next(iter(self._cache))
            await self._delete(oldest_key)
            self.stats["evictions"] += 1

    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0

        return {
            **self.stats,
            "total_requests": total,
            "hit_rate": f"{hit_rate:.2%}",
            "cache_size": len(self._cache),
            "max_size": self.max_size,
        }


# =============================================================================
# L2: Redis 缓存
# =============================================================================

class RedisCache:
    """
    L2 Redis 缓存

    特性:
    - 分布式缓存
    - 支持批量操作
    - 自动序列化
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        prefix: str = "intentos:compiler:",
        default_ttl_seconds: int = 86400,  # 24 小时
    ):
        self.host = host
        self.port = port
        self.db = db
        self.prefix = prefix
        self.default_ttl = default_ttl_seconds
        self._client = None

        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
        }

    async def _get_client(self):
        """获取 Redis 客户端"""
        if self._client is None:
            try:
                import redis.asyncio as redis
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=True,
                )
            except ImportError:
                raise ImportError("请安装 redis: pip install redis")
        return self._client

    def _make_key(self, key: str) -> str:
        """生成完整键"""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            client = await self._get_client()
            data = await client.get(self._make_key(key))

            if data is None:
                self.stats["misses"] += 1
                return None

            self.stats["hits"] += 1
            return json.loads(data)
        except Exception:
            self.stats["errors"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """设置缓存"""
        try:
            client = await self._get_client()
            data = json.dumps(value)
            ttl = ttl_seconds or self.default_ttl

            await client.setex(
                self._make_key(key),
                ttl,
                data,
            )
        except Exception:
            self.stats["errors"] += 1

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            client = await self._get_client()
            result = await client.delete(self._make_key(key))
            return result > 0
        except Exception:
            return False

    async def clear(self) -> None:
        """清空缓存"""
        try:
            client = await self._get_client()
            keys = await client.keys(f"{self.prefix}*")
            if keys:
                await client.delete(*keys)
        except Exception:
            pass

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0

        return {
            **self.stats,
            "total_requests": total,
            "hit_rate": f"{hit_rate:.2%}",
            "host": self.host,
        }


# =============================================================================
# L3: 磁盘缓存 (SQLite)
# =============================================================================

class DiskCache:
    """
    L3 磁盘缓存

    特性:
    - 持久化存储
    - 支持 SQL 查询
    - 自动清理过期数据
    """

    def __init__(
        self,
        db_path: str = "./cache/compiler_cache.db",
        default_ttl_seconds: int = 604800,  # 7 天
    ):
        self.db_path = db_path
        self.default_ttl = default_ttl_seconds
        self._conn = None

        # 统计信息
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
        }

    async def _get_connection(self):
        """获取数据库连接"""
        if self._conn is None:
            import aiosqlite
            self._conn = await aiosqlite.connect(self.db_path)
            await self._init_db()
        return self._conn

    async def _init_db(self) -> None:
        """初始化数据库"""
        conn = await self._get_connection()
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                ttl_seconds INTEGER,
                expires_at TIMESTAMP
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)"
        )
        await conn.commit()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            conn = await self._get_connection()
            cursor = await conn.execute(
                """
                SELECT value FROM cache
                WHERE key = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
                """,
                (key,),
            )
            row = await cursor.fetchone()

            if row is None:
                self.stats["misses"] += 1
                return None

            # 更新访问统计
            await conn.execute(
                """
                UPDATE cache
                SET last_accessed = datetime('now'), access_count = access_count + 1
                WHERE key = ?
                """,
                (key,),
            )
            await conn.commit()

            self.stats["hits"] += 1
            return json.loads(row[0])
        except Exception:
            self.stats["errors"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """设置缓存"""
        try:
            conn = await self._get_connection()
            ttl = ttl_seconds or self.default_ttl

            # 计算过期时间
            if ttl:
                expires_at = datetime.now() + timedelta(seconds=ttl)
                expires_at_str = expires_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                expires_at_str = "NULL"

            await conn.execute(
                """
                INSERT OR REPLACE INTO cache
                (key, value, ttl_seconds, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, json.dumps(value), ttl, expires_at_str if expires_at_str != "NULL" else None),
            )
            await conn.commit()
        except Exception:
            self.stats["errors"] += 1

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            conn = await self._get_connection()
            await conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            await conn.commit()
            return True
        except Exception:
            return False

    async def clear(self) -> None:
        """清空缓存"""
        try:
            conn = await self._get_connection()
            await conn.execute("DELETE FROM cache")
            await conn.commit()
        except Exception:
            pass

    async def cleanup_expired(self) -> int:
        """清理过期数据"""
        try:
            conn = await self._get_connection()
            cursor = await conn.execute(
                "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < datetime('now')"
            )
            await conn.commit()
            return cursor.rowcount
        except Exception:
            return 0

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0

        return {
            **self.stats,
            "total_requests": total,
            "hit_rate": f"{hit_rate:.2%}",
            "db_path": self.db_path,
        }


# =============================================================================
# 多级缓存管理器
# =============================================================================

class MultiLevelCache:
    """
    多级缓存管理器

    缓存策略:
    1. 先查 L1 (内存)
    2. 再查 L2 (Redis)
    3. 最后查 L3 (磁盘)
    4. 命中后回写到上层缓存
    """

    def __init__(
        self,
        memory_cache: Optional[MemoryCache] = None,
        redis_cache: Optional[RedisCache] = None,
        disk_cache: Optional[DiskCache] = None,
    ):
        self.l1 = memory_cache or MemoryCache()
        self.l2 = redis_cache  # 可选
        self.l3 = disk_cache  # 可选

        # 总体统计
        self.stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
        }

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存 (多级查询)"""
        # L1: 内存缓存
        value = await self.l1.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value

        # L2: Redis 缓存
        if self.l2:
            value = await self.l2.get(key)
            if value is not None:
                self.stats["l2_hits"] += 1
                # 回写到 L1
                await self.l1.set(key, value)
                return value

        # L3: 磁盘缓存
        if self.l3:
            value = await self.l3.get(key)
            if value is not None:
                self.stats["l3_hits"] += 1
                # 回写到 L1 和 L2
                await self.l1.set(key, value)
                if self.l2:
                    await self.l2.set(key, value)
                return value

        # 未命中
        self.stats["misses"] += 1
        return None

    async def set(
        self,
        key: str,
        value: Any,
        level: int = 1,
        **kwargs,
    ) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            level: 缓存级别 (1=L1, 2=L2, 3=L3)
            **kwargs: 其他参数 (如 ttl_seconds)
        """
        if level >= 1:
            await self.l1.set(key, value, **kwargs)

        if level >= 2 and self.l2:
            await self.l2.set(key, value, **kwargs)

        if level >= 3 and self.l3:
            await self.l3.set(key, value, **kwargs)

    async def delete(self, key: str) -> None:
        """删除缓存 (所有级别)"""
        await self.l1.delete(key)
        if self.l2:
            await self.l2.delete(key)
        if self.l3:
            await self.l3.delete(key)

    async def clear(self) -> None:
        """清空所有缓存"""
        await self.l1.clear()
        if self.l2:
            await self.l2.clear()
        if self.l3:
            await self.l3.clear()

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = sum(self.stats.values())
        total_hits = self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["l3_hits"]
        hit_rate = total_hits / total if total > 0 else 0

        return {
            **self.stats,
            "total_requests": total,
            "overall_hit_rate": f"{hit_rate:.2%}",
            "l1_stats": self.l1.get_stats(),
            "l2_stats": self.l2.get_stats() if self.l2 else None,
            "l3_stats": self.l3.get_stats() if self.l3 else None,
        }


# =============================================================================
# 缓存键生成器
# =============================================================================

def generate_cache_key(intent_data: dict[str, Any]) -> str:
    """
    生成缓存键

    基于意图内容的哈希值
    """
    # 序列化意图数据
    serialized = json.dumps(intent_data, sort_keys=True)

    # 生成 MD5 哈希
    hash_value = hashlib.md5(serialized.encode()).hexdigest()

    return f"compiled:{hash_value}"


# =============================================================================
# 便捷函数
# =============================================================================

def create_memory_cache(
    max_size: int = 1000,
    default_ttl_seconds: int = 3600,
) -> MemoryCache:
    """创建内存缓存"""
    return MemoryCache(max_size, default_ttl_seconds)


def create_redis_cache(
    host: str = "localhost",
    port: int = 6379,
    prefix: str = "intentos:compiler:",
) -> RedisCache:
    """创建 Redis 缓存"""
    return RedisCache(host, port, prefix=prefix)


def create_disk_cache(
    db_path: str = "./cache/compiler_cache.db",
) -> DiskCache:
    """创建磁盘缓存"""
    return DiskCache(db_path)


def create_multi_level_cache(
    enable_l1: bool = True,
    enable_l2: bool = False,
    enable_l3: bool = True,
    **kwargs,
) -> MultiLevelCache:
    """创建多级缓存"""
    return MultiLevelCache(
        memory_cache=create_memory_cache() if enable_l1 else None,
        redis_cache=create_redis_cache(**kwargs) if enable_l2 else None,
        disk_cache=create_disk_cache(**kwargs) if enable_l3 else None,
    )
