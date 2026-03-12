# 记忆分层架构

> IntentOS 的记忆系统分为三层：工作记忆、短期记忆、长期记忆，模拟人类记忆系统，每层有不同的存储策略和生命周期。

---

## 1. 概述

### 1.1 为什么需要分层

IntentOS 的记忆系统**模拟人类记忆**，而非传统计算机的内存层次：

| 人类记忆类型 | IntentOS 记忆 | 传统 OS 内存 |
|-------------|--------------|-------------|
| **工作记忆** | 工作记忆 | 寄存器/缓存 |
| **短期记忆** | 短期记忆 | RAM |
| **长期记忆** | 长期记忆 | 磁盘/SSD |

**关键区别**：
- **传统 OS 内存**: 存储**数据和指令**，按字节寻址
- **IntentOS 记忆**: 存储**意图、上下文、知识**，按语义检索

### 1.2 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│  工作记忆 (Working Memory)                                  │
│  • 存储：当前任务的中间结果                                 │
│  • 生命周期：任务执行期间                                   │
│  • 容量：有限 (7±2 个项目)                                  │
│  • 示例：DAG 执行的变量绑定、临时计算结果                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  短期记忆 (Short-term Memory)                               │
│  • 存储：用户会话、临时偏好、对话历史                       │
│  • 生命周期：分钟 - 小时 (TTL)                              │
│  • 容量：可配置 (默认 10000 条)                             │
│  • 示例：用户说"华东"通常指"华东三省一市"                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  长期记忆 (Long-term Memory)                                │
│  • 存储：知识库、历史报告、学到的意图模板                   │
│  • 生命周期：天 - 年 (可配置)                               │
│  • 容量：取决于存储后端 (Redis/文件)                        │
│  • 示例：销售最佳实践、客户画像、行业知识                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 工作记忆 (Working Memory)

### 2.1 特征

| 特征 | 说明 |
|------|------|
| **存储内容** | 当前任务的中间结果、变量绑定 |
| **生命周期** | 任务执行期间 |
| **访问速度** | 最快 (进程内) |
| **容量限制** | 受任务复杂度限制 |
| **同步** | 无 (仅当前任务访问) |

### 2.2 使用场景

- DAG 执行中的变量绑定
- 临时计算结果
- 当前对话的上下文

### 2.3 实现示例

```python
@dataclass
class WorkingMemory:
    """工作记忆"""
    task_id: str
    variables: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    
    def set(self, key: str, value: Any) -> None:
        """设置变量"""
        self.variables[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取变量"""
        return self.variables.get(key, default)
    
    def clear(self) -> None:
        """清空工作记忆"""
        self.variables.clear()
        self.results.clear()
```

### 2.4 使用示例

```python
# DAG 执行中的工作记忆
working_mem = WorkingMemory(task_id="task_123")

# 步骤 1: 查询销售数据
sales_data = await query_sales(region="华东")
working_mem.set("sales_data", sales_data)

# 步骤 2: 使用步骤 1 的结果
data = working_mem.get("sales_data")
analysis = await analyze(data)
working_mem.set("analysis", analysis)

# 步骤 3: 生成报告
report = await generate_report(working_mem.get("analysis"))

# 任务完成，工作记忆自动清空
```

---

## 3. 短期记忆 (Short-term Memory)

### 3.1 特征

| 特征 | 说明 |
|------|------|
| **存储内容** | 用户会话、临时偏好、对话历史 |
| **生命周期** | 分钟 - 小时 (TTL) |
| **访问速度** | 快 (内存 LRU Cache) |
| **容量限制** | 可配置 (默认 10000 条) |
| **同步** | 可选 Redis |

### 3.2 使用场景

- 用户会话状态
- 临时偏好设置（如"华东"指代范围）
- 对话历史
- 缓存的查询结果

### 3.3 实现示例

```python
class ShortTermMemory:
    """短期记忆"""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: float = 3600):
        self._store: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
    
    async def set(
        self,
        key: str,
        value: Any,
        tags: list[str] = None,
        ttl: float = None,
    ) -> None:
        """设置记忆"""
        async with self._lock:
            entry = MemoryEntry(
                key=key,
                value=value,
                memory_type=MemoryType.SHORT_TERM,
                expires_at=time.time() + (ttl or self._ttl),
                tags=tags or [],
            )
            
            # LRU: 移到末尾
            if key in self._store:
                self._store.move_to_end(key)
            
            self._store[key] = entry
            
            # 淘汰最旧的
            while len(self._store) > self._max_size:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
    
    async def get(self, key: str) -> Optional[Any]:
        """获取记忆"""
        async with self._lock:
            if key not in self._store:
                return None
            
            entry = self._store[key]
            
            # 检查过期
            if entry.is_expired():
                del self._store[key]
                return None
            
            # LRU: 移到末尾
            self._store.move_to_end(key)
            
            return entry.value
```

### 3.4 使用示例

```python
from intentos import create_memory_manager

manager = create_memory_manager(
    short_term_max=1000,
    short_term_ttl_seconds=3600,
)
await manager.initialize()

# 设置用户偏好
await manager.set_short_term(
    key="user:123:preference",
    value={"theme": "dark", "language": "zh-CN"},
    tags=["user", "preference"],
    ttl_seconds=7200,  # 2 小时
)

# 获取偏好
entry = await manager.get_short_term("user:123:preference")
print(entry.value)  # {"theme": "dark", "language": "zh-CN"}

# 按标签检索
entries = await manager.get_by_tag("user")
for e in entries:
    print(e.key, e.value)
```

---

## 4. 长期记忆 (Long-term Memory)

### 4.1 特征

| 特征 | 说明 |
|------|------|
| **存储内容** | 知识库、历史报告、学到的意图模板 |
| **生命周期** | 天 - 年 (可配置 TTL) |
| **访问速度** | 中等 (Redis/文件) |
| **容量限制** | 取决于存储后端 |
| **同步** | 分布式同步 |

### 4.2 使用场景

- 知识库（销售最佳实践、行业知识）
- 历史报告
- 学习到的意图模板
- 用户画像

### 4.3 后端选择

#### Redis 后端

```python
class RedisBackend:
    """Redis 长期记忆后端"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: str = None,
        key_prefix: str = "intentos:memory:",
    ):
        self.host = host
        self.port = port
        self.key_prefix = key_prefix
    
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
```

#### 文件后端

```python
class FileBackend:
    """文件长期记忆后端"""
    
    def __init__(self, data_dir: str = "./memory_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._index: dict[str, str] = {}
    
    async def get(self, key: str) -> Optional[MemoryEntry]:
        if key not in self._index:
            return None
        
        filepath = self._index[key]
        with open(filepath, "r") as f:
            data = json.load(f)
            return MemoryEntry.from_dict(data)
    
    async def set(self, entry: MemoryEntry) -> None:
        filepath = self._get_file_path(entry.key)
        self._index[entry.key] = filepath
        
        with open(filepath, "w") as f:
            json.dump(entry.to_dict(), f, indent=2)
```

### 4.4 使用示例

```python
manager = create_memory_manager(
    short_term_max=1000,
    long_term_enabled=True,
    long_term_backend="redis",  # 或 "file"
    redis_host="localhost",
    redis_port=6379,
)
await manager.initialize()

# 设置长期记忆（知识库）
await manager.set_long_term(
    key="knowledge:sales_best_practices",
    value={
        "title": "销售最佳实践",
        "content": "1. 定期跟进客户...",
        "category": "sales",
    },
    tags=["knowledge", "sales"],
    ttl_seconds=86400 * 30,  # 30 天
)

# 获取长期记忆（会自动缓存到短期记忆）
entry = await manager.get("knowledge:sales_best_practices")
print(entry.value)

# 搜索
results = await manager.search("销售")
for r in results:
    print(r.key, r.value)
```

---

## 5. 记忆流转

### 5.1 从短期到长期（巩固）

```python
async def consolidate_to_long_term(
    manager,
    key: str,
    reason: str = "important",
) -> None:
    """将短期记忆巩固为长期记忆"""
    entry = await manager.get_short_term(key)
    if entry:
        await manager.set_long_term(
            key=key,
            value=entry.value,
            tags=entry.tags + [reason],
            ttl_seconds=86400 * 30,  # 30 天
        )
```

### 5.2 从长期到短期（激活）

```python
# 获取长期记忆时，自动激活到短期记忆
async def get_with_activation(manager, key: str) -> Optional[Any]:
    # 先查短期
    entry = await manager.get_short_term(key)
    if entry:
        return entry.value
    
    # 再查长期
    entry = await manager.get_long_term(key)
    if entry:
        # 激活到短期
        await manager.set_short_term(
            key=key,
            value=entry.value,
            tags=entry.tags,
        )
        return entry.value
    
    return None
```

---

## 6. 记忆过期策略

### 6.1 TTL 策略

```python
# 设置时指定 TTL
await manager.set_short_term(
    key="temp:data",
    value="临时数据",
    ttl_seconds=300,  # 5 分钟
)

# 长期记忆的 TTL
await manager.set_long_term(
    key="report:monthly",
    value={"data": "..."},
    ttl_seconds=86400 * 30,  # 30 天
)
```

### 6.2 惰性清理

```python
# 获取时检查过期
async def get(self, key: str) -> Optional[Any]:
    entry = self._store.get(key)
    if entry and entry.is_expired():
        await self.delete(key)  # 惰性删除
        return None
    return entry.value if entry else None
```

### 6.3 定期清理

```python
async def cleanup_expired(manager, interval_seconds: int = 3600) -> None:
    """定期清理过期记忆"""
    while True:
        await asyncio.sleep(interval_seconds)
        
        # 清理短期记忆
        keys = await manager._short_term_backend.keys()
        for key in keys:
            entry = await manager._short_term_backend.get(key)
            if entry and entry.is_expired():
                await manager.delete_short_term(key)
```

---

## 7. 与人类记忆的类比

| 人类记忆 | IntentOS 记忆 | 示例 |
|---------|--------------|------|
| **工作记忆** | 工作记忆 | 心算过程中的中间结果 |
| **短期记忆** | 短期记忆 | 刚听到的电话号码（几分钟后忘记） |
| **长期记忆** | 长期记忆 | 母语、专业技能、历史知识 |

### 记忆巩固

人类睡眠时，短期记忆巩固为长期记忆：
```python
# 定期将重要的短期记忆巩固为长期记忆
async def sleep_consolidation(manager):
    """睡眠巩固（定期执行）"""
    important_entries = await manager.get_by_tag("important")
    for entry in important_entries:
        await consolidate_to_long_term(manager, entry.key)
```

---

## 8. 总结

IntentOS 记忆系统的核心价值：

1. **模拟人类记忆**: 工作/短期/长期三层结构
2. **语义检索**: 按标签、关键词、语义检索
3. **自动管理**: TTL 和清理策略
4. **分布式同步**: 多节点共享记忆

**注意**: IntentOS 的记忆是**语义记忆**，不是传统 OS 的**物理内存 (RAM)**。

---

**下一篇**: [分布式记忆同步](02-distributed-sync.md)

**上一篇**: [链接器](../03-compiler/04-linker.md)
