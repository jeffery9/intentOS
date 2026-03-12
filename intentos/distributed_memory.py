"""
分布式记忆管理系统

支持:
- 短期记忆 (Short-term Memory) - 进程内，快速访问
- 长期记忆 (Long-term Memory) - 持久化，支持分布式同步
- 分布式记忆同步 (Redis/共享存储)
- 记忆检索和索引
- 记忆过期和清理策略
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, AsyncIterator, Iterator, TypeVar, Generic, Union
from enum import Enum
import asyncio
import time
import uuid
import hashlib
import json
import os
import pickle
import weakref
from collections import OrderedDict, defaultdict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# 记忆核心定义
# =============================================================================

class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"     # 短期记忆（进程内）
    LONG_TERM = "long_term"       # 长期记忆（持久化）
    WORKING = "working"           # 工作记忆（当前任务）


class MemoryPriority(Enum):
    """记忆优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class MemoryEntry:
    """
    记忆条目
    所有记忆的基本单元
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    value: Any = None
    memory_type: MemoryType = MemoryType.SHORT_TERM
    priority: MemoryPriority = MemoryPriority.NORMAL
    
    # 元数据
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None  # 过期时间戳
    access_count: int = 0
    last_accessed: float = 0.0
    
    # 标签和索引
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # 版本控制
    version: int = 1
    parent_id: Optional[str] = None  # 父记忆 ID（用于版本链）
    
    # 分布式同步
    node_id: Optional[str] = None  # 创建节点 ID
    synced: bool = False  # 是否已同步到其他节点
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "memory_type": self.memory_type.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "tags": self.tags,
            "metadata": self.metadata,
            "version": self.version,
            "parent_id": self.parent_id,
            "node_id": self.node_id,
            "synced": self.synced,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            key=data.get("key", ""),
            value=data.get("value"),
            memory_type=MemoryType(data.get("memory_type", "short_term")),
            priority=MemoryPriority(data.get("priority", 2)),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            expires_at=data.get("expires_at"),
            access_count=data.get("access_count", 0),
            last_accessed=data.get("last_accessed", 0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
            parent_id=data.get("parent_id"),
            node_id=data.get("node_id"),
            synced=data.get("synced", False),
        )
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self) -> None:
        """更新访问时间"""
        self.access_count += 1
        self.last_accessed = time.time()
        self.updated_at = time.time()
    
    def set_expiry(self, seconds: float) -> None:
        """设置过期时间"""
        self.expires_at = time.time() + seconds


# =============================================================================
# 记忆存储后端
# =============================================================================

class MemoryBackend(ABC):
    """记忆存储后端抽象"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """获取记忆"""
        pass
    
    @abstractmethod
    async def set(self, entry: MemoryEntry) -> None:
        """设置记忆"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除记忆"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查记忆是否存在"""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        """获取匹配的键"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空所有记忆"""
        pass


class InMemoryBackend(MemoryBackend):
    """
    进程内记忆后端
    用于短期记忆存储
    """
    
    def __init__(self, max_size: int = 10000):
        self._store: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._max_size = max_size
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        async with self._lock:
            if key in self._store:
                entry = self._store[key]
                if entry.is_expired():
                    # 直接删除，不递归调用 delete
                    del self._store[key]
                    return None
                # LRU: 移到末尾
                self._store.move_to_end(key)
                return entry
            return None
    
    async def set(self, entry: MemoryEntry) -> None:
        async with self._lock:
            if entry.key in self._store:
                self._store.move_to_end(entry.key)
            self._store[entry.key] = entry

            # LRU 淘汰（直接删除，不递归调用 delete）
            while len(self._store) > self._max_size:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        async with self._lock:
            return key in self._store and not self._store[key].is_expired()
    
    async def keys(self, pattern: str = "*") -> list[str]:
        async with self._lock:
            if pattern == "*":
                return list(self._store.keys())
            
            # 简单通配符匹配
            import fnmatch
            return [k for k in self._store.keys() if fnmatch.fnmatch(k, pattern)]
    
    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()
    
    async def size(self) -> int:
        return len(self._store)
    
    async def get_all(self) -> list[MemoryEntry]:
        async with self._lock:
            return list(self._store.values())


class RedisBackend(MemoryBackend):
    """
    Redis 记忆后端
    用于长期记忆和分布式同步
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "intentos:memory:",
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self._client = None
        self._async_client = None
    
    def _get_client(self):
        """获取同步客户端"""
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=False,
                )
            except ImportError:
                raise ImportError("请安装 redis: pip install redis")
        return self._client
    
    async def _get_async_client(self):
        """获取异步客户端"""
        if self._async_client is None:
            try:
                import redis.asyncio as redis
                self._async_client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=False,
                )
            except ImportError:
                raise ImportError("请安装 redis: pip install redis")
        return self._async_client
    
    def _make_key(self, key: str) -> str:
        """生成完整键"""
        return f"{self.key_prefix}{key}"
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        client = await self._get_async_client()
        data = await client.get(self._make_key(key))
        if data:
            entry_dict = pickle.loads(data)
            return MemoryEntry.from_dict(entry_dict)
        return None
    
    async def set(self, entry: MemoryEntry) -> None:
        client = await self._get_async_client()
        data = pickle.dumps(entry.to_dict())
        
        if entry.expires_at:
            ttl = int(entry.expires_at - time.time())
            if ttl > 0:
                await client.setex(self._make_key(entry.key), ttl, data)
            else:
                await client.set(self._make_key(entry.key), data)
        else:
            await client.set(self._make_key(entry.key), data)
    
    async def delete(self, key: str) -> bool:
        client = await self._get_async_client()
        result = await client.delete(self._make_key(key))
        return result > 0
    
    async def exists(self, key: str) -> bool:
        client = await self._get_async_client()
        return await client.exists(self._make_key(key))
    
    async def keys(self, pattern: str = "*") -> list[str]:
        client = await self._get_async_client()
        full_pattern = self._make_key(pattern)
        keys = await client.keys(full_pattern)
        # 移除前缀
        prefix_len = len(self.key_prefix)
        return [k.decode()[prefix_len:] for k in keys]
    
    async def clear(self) -> None:
        client = await self._get_async_client()
        keys = await self.keys("*")
        if keys:
            full_keys = [self._make_key(k) for k in keys]
            await client.delete(*full_keys)
    
    async def publish(self, channel: str, message: dict) -> None:
        """发布消息到频道（用于分布式同步）"""
        client = await self._get_async_client()
        await client.publish(f"{self.key_prefix}{channel}", json.dumps(message))
    
    async def subscribe(self, channel: str) -> AsyncIterator[dict]:
        """订阅频道"""
        client = await self._get_async_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(f"{self.key_prefix}{channel}")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
    
    async def get_stats(self) -> dict:
        """获取 Redis 统计信息"""
        client = await self._get_async_client()
        info = await client.info("memory")
        return {
            "used_memory": info.get("used_memory", 0),
            "used_memory_human": info.get("used_memory_human", ""),
            "keys_count": await client.dbsize(),
        }


class FileBackend(MemoryBackend):
    """
    文件记忆后端
    用于长期记忆持久化（无 Redis 时）
    """
    
    def __init__(self, data_dir: str = "./memory_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._index: dict[str, str] = {}  # key -> file_path
        self._lock = asyncio.Lock()
        self._load_index()
    
    def _get_file_path(self, key: str) -> str:
        """获取文件路径"""
        # 使用哈希避免特殊字符
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.data_dir, f"{key_hash}.json")
    
    def _load_index(self) -> None:
        """加载索引"""
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        self._index[data.get("key", "")] = filepath
                except Exception:
                    pass
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        async with self._lock:
            if key not in self._index:
                return None
            
            filepath = self._index[key]
            if not os.path.exists(filepath):
                del self._index[key]
                return None
            
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    entry = MemoryEntry.from_dict(data)
                    
                    if entry.is_expired():
                        await self.delete(key)
                        return None
                    
                    return entry
            except Exception:
                return None
    
    async def set(self, entry: MemoryEntry) -> None:
        async with self._lock:
            filepath = self._get_file_path(entry.key)
            self._index[entry.key] = filepath
            
            with open(filepath, "w") as f:
                json.dump(entry.to_dict(), f, indent=2)
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key not in self._index:
                return False
            
            filepath = self._index.get(key)
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                del self._index[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        async with self._lock:
            if key not in self._index:
                return False
            filepath = self._index[key]
            return os.path.exists(filepath)
    
    async def keys(self, pattern: str = "*") -> list[str]:
        async with self._lock:
            if pattern == "*":
                return list(self._index.keys())
            
            import fnmatch
            return [k for k in self._index.keys() if fnmatch.fnmatch(k, pattern)]
    
    async def clear(self) -> None:
        async with self._lock:
            for filepath in self._index.values():
                if os.path.exists(filepath):
                    os.remove(filepath)
            self._index.clear()


# =============================================================================
# 记忆管理器
# =============================================================================

@dataclass
class MemoryConfig:
    """记忆配置"""
    # 短期记忆配置
    short_term_max_size: int = 10000
    short_term_ttl_seconds: float = 3600  # 1 小时
    
    # 长期记忆配置
    long_term_enabled: bool = True
    long_term_backend: str = "redis"  # redis, file
    long_term_ttl_seconds: float = 86400 * 30  # 30 天
    
    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # 分布式配置
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sync_enabled: bool = True
    
    # 索引配置
    index_enabled: bool = True
    index_tags: bool = True


class DistributedMemoryManager:
    """
    分布式记忆管理器
    
    管理短期记忆和长期记忆，支持分布式同步
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.node_id = self.config.node_id
        
        # 后端初始化
        self._short_term_backend: MemoryBackend = InMemoryBackend(
            max_size=self.config.short_term_max_size
        )
        self._long_term_backend: Optional[MemoryBackend] = None
        
        # 索引
        self._tag_index: defaultdict[str, set[str]] = defaultdict(set)  # tag -> keys
        self._key_tags: dict[str, set[str]] = {}  # key -> tags
        
        # 分布式同步
        self._sync_subscribers: list[asyncio.Task] = []
        self._pending_sync: asyncio.Queue = asyncio.Queue()
        
        # 统计
        self._stats = {
            "short_term_count": 0,
            "long_term_count": 0,
            "sync_count": 0,
            "hit_count": 0,
            "miss_count": 0,
        }
        
        # 回调
        self._on_write_callbacks: list[Callable] = []
    
    async def initialize(self) -> None:
        """初始化记忆管理器"""
        # 初始化长期记忆后端
        if self.config.long_term_enabled:
            if self.config.long_term_backend == "redis":
                try:
                    self._long_term_backend = RedisBackend(
                        host=self.config.redis_host,
                        port=self.config.redis_port,
                        db=self.config.redis_db,
                        password=self.config.redis_password,
                    )
                    # 测试连接
                    await self._long_term_backend.exists("_test")
                    logger.info(f"Redis 后端已连接：{self.config.redis_host}:{self.config.redis_port}")
                except Exception as e:
                    logger.warning(f"Redis 连接失败，使用文件后端：{e}")
                    self._long_term_backend = FileBackend()
            else:
                self._long_term_backend = FileBackend()
        
        # 启动同步任务
        if self.config.sync_enabled and isinstance(self._long_term_backend, RedisBackend):
            await self._start_sync()
        
        logger.info(f"记忆管理器已初始化，节点 ID: {self.node_id}")
    
    async def shutdown(self) -> None:
        """关闭记忆管理器"""
        # 停止同步任务
        for task in self._sync_subscribers:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # 清空待同步队列（避免无限等待）
        while not self._pending_sync.empty():
            try:
                self._pending_sync.get_nowait()
                self._pending_sync.task_done()
            except asyncio.QueueEmpty:
                break

        logger.info("记忆管理器已关闭")
    
    # ========== 短期记忆操作 ==========
    
    async def get_short_term(self, key: str) -> Optional[MemoryEntry]:
        """获取短期记忆"""
        entry = await self._short_term_backend.get(key)
        
        if entry:
            entry.touch()
            self._stats["hit_count"] += 1
        else:
            self._stats["miss_count"] += 1
        
        return entry
    
    async def set_short_term(
        self,
        key: str,
        value: Any,
        tags: Optional[list[str]] = None,
        priority: MemoryPriority = MemoryPriority.NORMAL,
        ttl_seconds: Optional[float] = None,
        metadata: Optional[dict] = None,
    ) -> MemoryEntry:
        """设置短期记忆"""
        entry = MemoryEntry(
            key=key,
            value=value,
            memory_type=MemoryType.SHORT_TERM,
            priority=priority,
            tags=tags or [],
            metadata=metadata or {},
            node_id=self.node_id,
        )
        
        if ttl_seconds is not None:
            entry.set_expiry(ttl_seconds)
        else:
            entry.set_expiry(self.config.short_term_ttl_seconds)
        
        await self._short_term_backend.set(entry)
        await self._update_index(entry)
        await self._notify_write(entry)
        
        if self.config.sync_enabled:
            await self._queue_sync(entry, "short_term")
        
        return entry
    
    async def delete_short_term(self, key: str) -> bool:
        """删除短期记忆"""
        result = await self._short_term_backend.delete(key)
        if result:
            await self._remove_from_index(key)
        return result
    
    # ========== 长期记忆操作 ==========
    
    async def get_long_term(self, key: str) -> Optional[MemoryEntry]:
        """获取长期记忆"""
        if not self._long_term_backend:
            return None
        
        entry = await self._long_term_backend.get(key)
        
        if entry:
            entry.touch()
            self._stats["hit_count"] += 1
            
            # 缓存到短期记忆
            entry.memory_type = MemoryType.LONG_TERM
            await self._short_term_backend.set(entry)
        else:
            self._stats["miss_count"] += 1
        
        return entry
    
    async def set_long_term(
        self,
        key: str,
        value: Any,
        tags: Optional[list[str]] = None,
        priority: MemoryPriority = MemoryPriority.NORMAL,
        ttl_seconds: Optional[float] = None,
        metadata: Optional[dict] = None,
    ) -> MemoryEntry:
        """设置长期记忆"""
        if not self._long_term_backend:
            raise RuntimeError("长期记忆未启用")
        
        entry = MemoryEntry(
            key=key,
            value=value,
            memory_type=MemoryType.LONG_TERM,
            priority=priority,
            tags=tags or [],
            metadata=metadata or {},
            node_id=self.node_id,
        )
        
        if ttl_seconds is not None:
            entry.set_expiry(ttl_seconds)
        else:
            entry.set_expiry(self.config.long_term_ttl_seconds)
        
        await self._long_term_backend.set(entry)
        await self._update_index(entry)
        await self._notify_write(entry)
        
        if self.config.sync_enabled:
            await self._queue_sync(entry, "long_term")
        
        return entry
    
    async def delete_long_term(self, key: str) -> bool:
        """删除长期记忆"""
        if not self._long_term_backend:
            return False
        
        result = await self._long_term_backend.delete(key)
        if result:
            await self._remove_from_index(key)
            await self._short_term_backend.delete(key)
        return result
    
    # ========== 统一记忆操作 ==========
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        """获取记忆（先短期，后长期）"""
        # 先查短期记忆
        entry = await self.get_short_term(key)
        if entry:
            return entry
        
        # 再查长期记忆
        entry = await self.get_long_term(key)
        if entry:
            return entry
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        **kwargs,
    ) -> MemoryEntry:
        """设置记忆"""
        if memory_type == MemoryType.SHORT_TERM:
            return await self.set_short_term(key, value, **kwargs)
        elif memory_type == MemoryType.LONG_TERM:
            return await self.set_long_term(key, value, **kwargs)
        else:
            raise ValueError(f"未知记忆类型：{memory_type}")
    
    async def delete(self, key: str, memory_type: Optional[MemoryType] = None) -> bool:
        """删除记忆"""
        deleted = False
        
        if memory_type is None or memory_type == MemoryType.SHORT_TERM:
            deleted = await self.delete_short_term(key) or deleted
        
        if memory_type is None or memory_type == MemoryType.LONG_TERM:
            deleted = await self.delete_long_term(key) or deleted
        
        return deleted
    
    # ========== 索引和检索 ==========
    
    async def _update_index(self, entry: MemoryEntry) -> None:
        """更新索引"""
        if not self.config.index_enabled:
            return
        
        key = entry.key
        
        # 移除旧标签
        if key in self._key_tags:
            old_tags = self._key_tags[key]
            for tag in old_tags:
                self._tag_index[tag].discard(key)
        
        # 添加新标签
        self._key_tags[key] = set(entry.tags)
        for tag in entry.tags:
            self._tag_index[tag].add(key)
    
    async def _remove_from_index(self, key: str) -> None:
        """从索引中移除"""
        if key in self._key_tags:
            for tag in self._key_tags[key]:
                self._tag_index[tag].discard(key)
            del self._key_tags[key]
    
    async def get_by_tag(self, tag: str) -> list[MemoryEntry]:
        """根据标签获取记忆"""
        keys = self._tag_index.get(tag, set())
        entries = []
        
        for key in keys:
            entry = await self.get(key)
            if entry and tag in entry.tags:
                entries.append(entry)
        
        return entries
    
    async def search(self, query: str) -> list[MemoryEntry]:
        """搜索记忆（简单文本匹配）"""
        results = []
        
        async for entry in self._iterate_all():
            # 匹配键、值、标签
            if (query.lower() in entry.key.lower() or
                (isinstance(entry.value, str) and query.lower() in entry.value.lower()) or
                any(query.lower() in tag.lower() for tag in entry.tags)):
                results.append(entry)
        
        return results
    
    async def _iterate_all(self) -> AsyncIterator[MemoryEntry]:
        """遍历所有记忆"""
        # 短期记忆
        if isinstance(self._short_term_backend, InMemoryBackend):
            for entry in await self._short_term_backend.get_all():
                yield entry
        
        # 长期记忆
        if self._long_term_backend:
            keys = await self._long_term_backend.keys()
            for key in keys:
                entry = await self._long_term_backend.get(key)
                if entry:
                    yield entry
    
    # ========== 分布式同步 ==========
    
    async def _start_sync(self) -> None:
        """启动分布式同步"""
        if not isinstance(self._long_term_backend, RedisBackend):
            return
        
        # 订阅其他节点的更新
        task = asyncio.create_task(self._sync_listener())
        self._sync_subscribers.append(task)
    
    async def _sync_listener(self) -> None:
        """监听同步消息"""
        redis = self._long_term_backend
        async for message in redis.subscribe("sync"):
            try:
                if message.get("node_id") != self.node_id:
                    # 来自其他节点的更新
                    entry_data = message.get("entry")
                    if entry_data:
                        entry = MemoryEntry.from_dict(entry_data)
                        entry.synced = True
                        
                        # 本地存储
                        if entry.memory_type == MemoryType.LONG_TERM:
                            await self._long_term_backend.set(entry)
                        
                        self._stats["sync_count"] += 1
                        logger.debug(f"同步记忆：{entry.key} from {message.get('node_id')}")
            except Exception as e:
                logger.error(f"同步失败：{e}")
    
    async def _queue_sync(self, entry: MemoryEntry, scope: str) -> None:
        """将记忆加入同步队列"""
        if not isinstance(self._long_term_backend, RedisBackend):
            return
        
        await self._pending_sync.put({
            "node_id": self.node_id,
            "scope": scope,
            "entry": entry.to_dict(),
            "timestamp": time.time(),
        })
        
        # 异步处理
        asyncio.create_task(self._process_sync())
    
    async def _process_sync(self) -> None:
        """处理同步队列"""
        while not self._pending_sync.empty():
            message = await self._pending_sync.get()
            
            try:
                await self._long_term_backend.publish("sync", message)
                self._pending_sync.task_done()
            except Exception as e:
                logger.error(f"同步发布失败：{e}")
                await self._pending_sync.put(message)
                break
    
    # ========== 统计和管理 ==========
    
    async def get_stats(self) -> dict:
        """获取统计信息"""
        stats = {
            **self._stats,
            "node_id": self.node_id,
            "short_term_size": await self._short_term_backend.size() if isinstance(self._short_term_backend, InMemoryBackend) else 0,
        }
        
        if self._long_term_backend and isinstance(self._long_term_backend, RedisBackend):
            try:
                redis_stats = await self._long_term_backend.get_stats()
                stats["long_term"] = redis_stats
            except Exception:
                pass
        
        return stats
    
    async def clear(self, memory_type: Optional[MemoryType] = None) -> None:
        """清空记忆"""
        if memory_type is None or memory_type == MemoryType.SHORT_TERM:
            await self._short_term_backend.clear()
        
        if memory_type is None or memory_type == MemoryType.LONG_TERM:
            if self._long_term_backend:
                await self._long_term_backend.clear()
        
        self._tag_index.clear()
        self._key_tags.clear()
    
    def on_write(self, callback: Callable) -> None:
        """注册写入回调"""
        self._on_write_callbacks.append(callback)
    
    async def _notify_write(self, entry: MemoryEntry) -> None:
        """通知写入事件"""
        for callback in self._on_write_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(entry)
                else:
                    callback(entry)
            except Exception as e:
                logger.error(f"写入回调失败：{e}")


# =============================================================================
# 便捷函数
# =============================================================================

def create_memory_manager(
    short_term_max: int = 10000,
    long_term_enabled: bool = True,
    long_term_backend: str = "redis",
    redis_host: str = "localhost",
    redis_port: int = 6379,
    sync_enabled: bool = True,
) -> DistributedMemoryManager:
    """创建记忆管理器"""
    config = MemoryConfig(
        short_term_max_size=short_term_max,
        long_term_enabled=long_term_enabled,
        long_term_backend=long_term_backend,
        redis_host=redis_host,
        redis_port=redis_port,
        sync_enabled=sync_enabled,
    )
    return DistributedMemoryManager(config)


async def create_and_initialize_memory_manager(**kwargs) -> DistributedMemoryManager:
    """创建并初始化记忆管理器"""
    manager = create_memory_manager(**kwargs)
    await manager.initialize()
    return manager
