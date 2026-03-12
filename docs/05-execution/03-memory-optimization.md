# 记忆优化

> 记忆优化确保 IntentOS 在处理大规模数据时不会耗尽存储资源，支持流式处理、磁盘溢出和自动清理。

**注意**: 这里的"记忆"是指 IntentOS 的**语义记忆系统**（工作记忆、短期记忆、长期记忆），**不是**传统 OS 的物理内存 (RAM)。

---

## 1. 记忆管理策略

### 1.1 记忆分层优化

```
┌─────────────────────────────────────────┐
│  工作记忆 (进程内)                       │
│  • 最快访问                              │
│  • 任务结束自动清空                      │
│  • 无需优化                              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  短期记忆 (LRU Cache)                    │
│  • 快速访问                              │
│  • TTL + LRU 淘汰                        │
│  • 容量限制                              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  长期记忆 (Redis/文件)                   │
│  • 持久化存储                            │
│  • 磁盘溢出                              │
│  • 分布式同步                            │
└─────────────────────────────────────────┘
```

### 1.2 优化策略

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| **流式处理** | 逐块处理记忆，不一次性加载 | 大批量记忆更新 |
| **磁盘溢出** | 短期记忆溢出到磁盘 | 记忆数量超限制 |
| **自动清理** | 定期清理过期记忆 | 所有场景 |
| **记忆压缩** | 压缩大型记忆值 | 大型报告/文档 |

---

## 2. 流式记忆处理

### 2.1 流式记忆更新

```python
async def stream_memory_update(
    manager,
    entries: list[MemoryEntry],
    chunk_size: int = 100,
) -> None:
    """流式更新记忆"""
    for i in range(0, len(entries), chunk_size):
        chunk = entries[i:i + chunk_size]
        
        # 处理 chunk
        for entry in chunk:
            await manager.set(entry.key, entry.value, tags=entry.tags)
        
        # 释放 chunk
        chunk.clear()
        
        # 定期 GC（清理 Python 对象内存，不是 IntentOS 记忆）
        if i % (chunk_size * 10) == 0:
            gc.collect()
```

### 2.2 流式记忆检索

```python
async def stream_search(
    manager,
    query: str,
    batch_size: int = 100,
) -> AsyncIterator[SearchResult]:
    """流式搜索记忆"""
    all_keys = await manager._long_term_backend.keys()
    
    for i in range(0, len(all_keys), batch_size):
        batch_keys = all_keys[i:i + batch_size]
        
        for key in batch_keys:
            entry = await manager.get(key)
            if entry and query.lower() in str(entry.value).lower():
                yield SearchResult(entry=entry, query=query)
        
        # 释放批次
        batch_keys.clear()
```

---

## 3. 短期记忆淘汰策略

### 3.1 LRU 淘汰

```python
class ShortTermMemory:
    """短期记忆（LRU 淘汰）"""
    
    def __init__(self, max_size: int = 10000):
        self._store: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._max_size = max_size
    
    async def set(self, key: str, entry: MemoryEntry) -> None:
        async with self._lock:
            # LRU: 移到末尾（最近使用）
            if key in self._store:
                self._store.move_to_end(key)
            
            self._store[key] = entry
            
            # 淘汰最久未使用的记忆
            while len(self._store) > self._max_size:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
                logger.debug(f"LRU 淘汰记忆：{oldest_key}")
```

### 3.2 LFU 淘汰

```python
class LFUMemory:
    """短期记忆（LFU 淘汰 - 最少使用）"""
    
    def __init__(self, max_size: int = 10000):
        self._store: dict[str, MemoryEntry] = {}
        self._freq: dict[str, int] = {}  # 访问频率
        self._max_size = max_size
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        if key not in self._store:
            return None
        
        # 增加频率
        self._freq[key] += 1
        return self._store[key]
    
    async def set(self, key: str, entry: MemoryEntry) -> None:
        if key in self._store:
            self._freq[key] += 1
        else:
            # 淘汰频率最低的记忆
            if len(self._store) >= self._max_size:
                min_freq_key = min(self._freq, key=self._freq.get)
                del self._store[min_freq_key]
                del self._freq[min_freq_key]
            
            self._freq[key] = 1
        
        self._store[key] = entry
```

---

## 4. 长期记忆磁盘溢出

### 4.1 溢出策略

```python
class SpillManager:
    """记忆溢出管理器"""
    
    def __init__(
        self,
        spill_threshold_count: int = 100000,  # 记忆数量阈值
        temp_dir: str = "/tmp/intentos",
    ):
        self.spill_threshold = spill_threshold_count
        self.temp_dir = temp_dir
        self._spill_files: list[str] = []
    
    async def maybe_spill(
        self,
        backend: FileBackend,
        current_count: int,
    ) -> None:
        """检查并溢出记忆到磁盘"""
        if current_count < self.spill_threshold:
            return
        
        # 溢出 50% 的旧记忆
        spill_count = len(backend._index) // 2
        spill_keys = list(backend._index.keys())[:spill_count]
        
        # 批量导出
        spill_data = {}
        for key in spill_keys:
            entry = await backend.get(key)
            if entry:
                spill_data[key] = entry.to_dict()
        
        # 写入溢出文件
        spill_path = await self._write_spill(spill_data)
        self._spill_files.append(spill_path)
        
        # 从主存储中移除
        for key in spill_keys:
            del backend._index[key]
            filepath = backend._get_file_path(key)
            if os.path.exists(filepath):
                os.remove(filepath)
        
        logger.info(f"溢出 {spill_count} 条记忆到 {spill_path}")
```

### 4.2 溢出文件管理

```python
class SpillFileManager:
    """溢出文件管理"""
    
    def __init__(self, temp_dir: str = "/tmp/intentos"):
        self.temp_dir = temp_dir
        self._files: list[str] = []
        self._index: dict[str, str] = {}  # key -> spill_file
    
    async def create_spill_file(self, entries: dict) -> str:
        """创建溢出文件"""
        filename = f"spill_{uuid.uuid4()}.json"
        path = os.path.join(self.temp_dir, filename)
        
        # 异步写入
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: json.dump(entries, open(path, 'w'), indent=2),
        )
        
        # 建立索引
        for key in entries.keys():
            self._index[key] = path
        
        self._files.append(path)
        return path
    
    async def load_spill(self, key: str) -> Optional[MemoryEntry]:
        """从溢出文件加载记忆"""
        if key not in self._index:
            return None
        
        path = self._index[key]
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None,
            lambda: json.load(open(path, 'r')),
        )
        
        return MemoryEntry.from_dict(data.get(key))
    
    async def cleanup(self) -> None:
        """清理所有溢出文件"""
        for path in self._files:
            try:
                os.remove(path)
            except Exception as e:
                logger.error(f"清理溢出文件失败：{path}, 错误：{e}")
        self._files.clear()
        self._index.clear()
```

---

## 5. 自动清理

### 5.1 过期记忆清理

```python
async def cleanup_expired_memories(
    manager,
    interval_seconds: int = 3600,
) -> None:
    """定期清理过期记忆"""
    while True:
        await asyncio.sleep(interval_seconds)
        
        cleaned_count = 0
        
        # 清理短期记忆
        keys = await manager._short_term_backend.keys()
        for key in keys:
            entry = await manager._short_term_backend.get(key)
            if entry and entry.is_expired():
                await manager.delete_short_term(key)
                cleaned_count += 1
        
        # 清理长期记忆
        keys = await manager._long_term_backend.keys()
        for key in keys:
            entry = await manager._long_term_backend.get(key)
            if entry and entry.is_expired():
                await manager.delete_long_term(key)
                cleaned_count += 1
        
        logger.info(f"清理完成，删除 {cleaned_count} 条过期记忆")
```

### 5.2 低优先级记忆淘汰

```python
async def evict_low_priority_memories(
    manager,
    target_count: int,
) -> int:
    """淘汰低优先级记忆"""
    # 获取所有记忆
    entries = []
    keys = await manager._short_term_backend.keys()
    for key in keys:
        entry = await manager._short_term_backend.get(key)
        if entry:
            entries.append(entry)
    
    # 按优先级排序
    entries.sort(key=lambda e: e.priority.value)
    
    # 淘汰低优先级
    evicted_count = 0
    for entry in entries:
        if len(entries) - evicted_count <= target_count:
            break
        
        await manager.delete_short_term(entry.key)
        evicted_count += 1
    
    logger.info(f"淘汰 {evicted_count} 条低优先级记忆")
    return evicted_count
```

---

## 6. 记忆压缩

### 6.1 大型记忆压缩

```python
import gzip
import pickle

class CompressedMemoryBackend:
    """压缩记忆后端"""
    
    def __init__(self, backend: MemoryBackend, compress_threshold: int = 1024):
        self.backend = backend
        self.compress_threshold = compress_threshold  # 超过 1KB 压缩
    
    async def set(self, entry: MemoryEntry) -> None:
        # 序列化
        data = pickle.dumps(entry.to_dict())
        
        # 大型记忆压缩
        if len(data) > self.compress_threshold:
            compressed_data = gzip.compress(data)
            entry.metadata["compressed"] = True
            data = compressed_data
        else:
            entry.metadata["compressed"] = False
        
        # 存储
        await self.backend.set(entry)
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        entry = await self.backend.get(key)
        if not entry:
            return None
        
        # 解压缩
        if entry.metadata.get("compressed"):
            data = entry.value
            if isinstance(data, bytes):
                data = gzip.decompress(data)
            entry.value = pickle.loads(data)
        
        return entry
```

---

## 7. 完整示例

### 7.1 记忆优化配置

```python
from intentos import create_memory_manager

manager = create_memory_manager(
    # 短期记忆配置
    short_term_max=10000,       # 最多 10000 条
    short_term_ttl_seconds=3600, # TTL 1 小时
    
    # 长期记忆配置
    long_term_enabled=True,
    long_term_backend="redis",
    redis_host="localhost",
    redis_port=6379,
    
    # 优化配置
    sync_enabled=True,          # 启用分布式同步
)
await manager.initialize()

# 启动自动清理任务
asyncio.create_task(cleanup_expired_memories(manager, interval_seconds=3600))
```

### 7.2 大批量记忆更新

```python
# 大批量记忆更新（流式处理）
async def bulk_update_memories(manager, entries: list[MemoryEntry]):
    """大批量记忆更新"""
    await stream_memory_update(manager, entries, chunk_size=100)
    logger.info(f"完成 {len(entries)} 条记忆更新")
```

---

## 8. 总结

IntentOS 记忆优化的核心策略：

1. **流式处理**: 逐块处理记忆更新
2. **LRU/LFU 淘汰**: 自动淘汰不常用的记忆
3. **磁盘溢出**: 大量记忆溢出到磁盘
4. **自动清理**: 定期清理过期记忆
5. **记忆压缩**: 大型记忆压缩存储

**重要**: 这些优化针对的是**语义记忆**，不是传统 OS 的物理内存。

---

**下一篇**: [LLM 后端](../05-execution/04-llm-backends.md)

**上一篇**: [Map/Reduce](../05-execution/02-map-reduce.md)
