# 过期策略

> 记忆过期策略管理记忆的生命周期，包括 TTL 设置、惰性清理、定期清理等机制。

---

## 1. TTL (Time To Live)

### 1.1 设置 TTL

```python
# 短期记忆 TTL
await manager.set_short_term(
    key="session:123",
    value={"user_id": "user_001"},
    ttl_seconds=3600,  # 1 小时
)

# 长期记忆 TTL
await manager.set_long_term(
    key="report:monthly",
    value={"data": "..."},
    ttl_seconds=86400 * 30,  # 30 天
)
```

### 1.2 默认 TTL

```python
manager = create_memory_manager(
    short_term_max=1000,
    short_term_ttl_seconds=3600,    # 短期记忆默认 1 小时
    long_term_ttl_seconds=86400*30, # 长期记忆默认 30 天
)
```

### 1.3 更新 TTL

```python
# 刷新过期时间
async def refresh_ttl(manager, key: str, ttl_seconds: float) -> None:
    entry = await manager.get(key)
    if entry:
        entry.expires_at = time.time() + ttl_seconds
        await manager.set(key, entry.value, ttl_seconds=ttl_seconds)

# 使用
await refresh_ttl(manager, "session:123", 3600)
```

---

## 2. 过期检查

### 2.1 惰性清理

获取记忆时检查是否过期：

```python
async def get(self, key: str) -> Optional[Any]:
    entry = self._store.get(key)
    
    if not entry:
        return None
    
    # 检查过期
    if entry.is_expired():
        # 惰性删除
        await self.delete(key)
        return None
    
    return entry.value
```

### 2.2 定期清理

后台任务定期清理过期记忆：

```python
async def cleanup_task(manager, interval: int = 3600) -> None:
    """定期清理任务"""
    while True:
        await asyncio.sleep(interval)
        
        # 清理短期记忆
        keys = await manager._short_term_backend.keys()
        for key in keys:
            entry = await manager._short_term_backend.get(key)
            if entry and entry.is_expired():
                await manager.delete(key)
        
        # 清理长期记忆
        keys = await manager._long_term_backend.keys()
        for key in keys:
            entry = await manager._long_term_backend.get(key)
            if entry and entry.is_expired():
                await manager.delete(key)
        
        logger.info(f"清理完成，当前记忆数：{len(keys)}")
```

### 2.3 Redis 原生过期

使用 Redis 的过期功能：

```python
class RedisBackend:
    async def set(self, entry: MemoryEntry) -> None:
        client = await self._get_async_client()
        data = pickle.dumps(entry.to_dict())
        
        if entry.expires_at:
            ttl = int(entry.expires_at - time.time())
            if ttl > 0:
                # Redis 自动过期
                await client.setex(
                    self._make_key(entry.key),
                    ttl,
                    data,
                )
            else:
                await client.set(self._make_key(entry.key), data)
        else:
            await client.set(self._make_key(entry.key), data)
```

---

## 3. 过期策略配置

### 3.1 分层 TTL

```python
TTL_CONFIG = {
    "session": 3600,           # 会话：1 小时
    "preference": 86400 * 7,   # 偏好：7 天
    "cache:query": 3600,       # 查询缓存：1 小时
    "cache:report": 86400,     # 报告缓存：1 天
    "knowledge": 86400 * 365,  # 知识：1 年
    "default": 86400 * 30,     # 默认：30 天
}

def get_ttl(key: str) -> int:
    """根据键获取 TTL"""
    prefix = key.split(":")[0]
    return TTL_CONFIG.get(key, TTL_CONFIG.get(prefix, TTL_CONFIG["default"]))
```

### 3.2 永不过期

```python
# 设置永不过期的记忆
await manager.set_long_term(
    key="system:config",
    value={"version": "1.0"},
    ttl_seconds=None,  # 永不过期
)
```

---

## 4. 过期通知

### 4.1 注册回调

```python
def on_expire(manager, callback: Callable) -> None:
    """注册过期回调"""
    manager._on_expire_callbacks.append(callback)

async def notify_expire(entry: MemoryEntry) -> None:
    """通知过期"""
    for callback in manager._on_expire_callbacks:
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(entry)
            else:
                callback(entry)
        except Exception as e:
            logger.error(f"过期回调失败：{e}")
```

### 4.2 使用示例

```python
# 注册过期回调
def on_entry_expire(entry):
    print(f"记忆过期：{entry.key}")
    # 可以在这里做清理工作

manager.on_expire(on_entry_expire)

# 设置记忆
await manager.set_short_term(
    key="temp:data",
    value="临时数据",
    ttl_seconds=5,  # 5 秒后过期
)

# 5 秒后会自动调用 on_entry_expire
```

---

## 5. 内存管理

### 5.1 LRU 淘汰

当内存达到上限时，淘汰最久未使用的记忆：

```python
class ShortTermMemory:
    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            # LRU: 移到末尾（最近使用）
            if key in self._store:
                self._store.move_to_end(key)
            
            self._store[key] = value
            
            # 淘汰最旧的
            while len(self._store) > self._max_size:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
                logger.debug(f"LRU 淘汰：{oldest_key}")
```

### 5.2 LFU 淘汰

淘汰最少使用的记忆：

```python
class LFUCache:
    def __init__(self, max_size: int):
        self._store: dict[str, Any] = {}
        self._freq: dict[str, int] = {}  # 访问频率
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        
        # 增加频率
        self._freq[key] += 1
        return self._store[key]
    
    def set(self, key: str, value: Any) -> None:
        if key in self._store:
            self._freq[key] += 1
        else:
            # 淘汰频率最低的
            if len(self._store) >= self._max_size:
                min_freq_key = min(self._freq, key=self._freq.get)
                del self._store[min_freq_key]
                del self._freq[min_freq_key]
            
            self._freq[key] = 1
        
        self._store[key] = value
```

---

## 6. 使用示例

### 6.1 会话管理

```python
# 用户登录，创建会话
await manager.set_short_term(
    key=f"session:{user_id}",
    value={"user_id": user_id, "login_time": time.time()},
    ttl_seconds=3600,  # 1 小时过期
)

# 用户活动，刷新会话
async def refresh_session(user_id: str) -> None:
    await refresh_ttl(manager, f"session:{user_id}", 3600)

# 用户登出，删除会话
await manager.delete(f"session:{user_id}")
```

### 6.2 缓存管理

```python
# 缓存查询结果
async def get_with_cache(query: str):
    cache_key = f"cache:query:{hashlib.md5(query.encode()).hexdigest()}"
    
    # 尝试从缓存获取
    cached = await manager.get_short_term(cache_key)
    if cached:
        return cached
    
    # 执行查询
    result = await execute_query(query)
    
    # 缓存结果
    await manager.set_short_term(
        key=cache_key,
        value=result,
        ttl_seconds=3600,  # 1 小时
    )
    
    return result
```

### 6.3 临时数据

```python
# 设置临时数据
await manager.set_short_term(
    key="temp:import:123",
    value={"status": "processing", "progress": 0},
    ttl_seconds=600,  # 10 分钟后自动清理
)

# 注册过期回调，清理相关资源
def on_import_expire(entry):
    # 清理临时文件
    temp_file = f"/tmp/import_{entry.key.split(':')[2]}.csv"
    if os.path.exists(temp_file):
        os.remove(temp_file)

manager.on_expire(on_import_expire)
```

---

## 7. 总结

过期策略的核心机制：

1. **TTL 设置**: 灵活的生命周期管理
2. **惰性清理**: 获取时检查过期
3. **定期清理**: 后台任务清理
4. **LRU/LFU**: 内存淘汰策略
5. **过期通知**: 回调机制

---

**下一篇**: [DAG 执行引擎](../05-execution/01-dag-engine.md)

**上一篇**: [记忆检索](03-memory-retrieval.md)
