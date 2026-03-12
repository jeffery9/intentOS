# 记忆 API

> 本文档介绍 IntentOS 记忆管理系统的 API，用于存储、检索和管理语义记忆。

---

## 1. 记忆管理器

### 1.1 DistributedMemoryManager

分布式记忆管理器主类：

```python
from intentos import DistributedMemoryManager, MemoryConfig

# 创建配置
config = MemoryConfig(
    short_term_max_size=10000,
    short_term_ttl_seconds=3600,
    long_term_enabled=True,
    long_term_backend="redis",
    redis_host="localhost",
    redis_port=6379,
    sync_enabled=True,
    node_id="node-001",
)

# 创建管理器
manager = DistributedMemoryManager(config)
await manager.initialize()
```

### 1.2 便捷函数

```python
from intentos import create_memory_manager, create_and_initialize_memory_manager

# 快速创建（不初始化）
manager = create_memory_manager(
    short_term_max=10000,
    long_term_enabled=True,
)

# 创建并初始化
manager = await create_and_initialize_memory_manager(
    short_term_max=10000,
    long_term_backend="redis",
    redis_host="localhost",
)
```

---

## 2. 短期记忆操作

### 2.1 设置记忆

```python
# 基本设置
await manager.set_short_term(
    key="user:123:preference",
    value={"theme": "dark", "language": "zh-CN"},
)

# 带标签和 TTL
await manager.set_short_term(
    key="session:456",
    value={"user_id": "user_001", "login_time": time.time()},
    tags=["session", "user_001"],
    ttl_seconds=7200,  # 2 小时
)

# 带优先级
from intentos import MemoryPriority
await manager.set_short_term(
    key="important:data",
    value="重要数据",
    priority=MemoryPriority.HIGH,
)
```

### 2.2 获取记忆

```python
# 获取记忆
entry = await manager.get_short_term("user:123:preference")
if entry:
    print(f"值：{entry.value}")
    print(f"标签：{entry.tags}")
    print(f"访问次数：{entry.access_count}")

# 检查是否存在
exists = await manager._short_term_backend.exists("user:123:preference")
```

### 2.3 删除记忆

```python
# 删除记忆
deleted = await manager.delete_short_term("user:123:preference")
```

---

## 3. 长期记忆操作

### 3.1 设置记忆

```python
# 基本设置
await manager.set_long_term(
    key="knowledge:sales_best_practices",
    value={
        "title": "销售最佳实践",
        "content": "1. 定期跟进客户...",
    },
)

# 带标签和 TTL
await manager.set_long_term(
    key="report:2024-q3",
    value={"revenue": 1000000, "growth": 0.15},
    tags=["report", "2024", "q3"],
    ttl_seconds=86400 * 365,  # 1 年
)
```

### 3.2 获取记忆

```python
# 获取记忆
entry = await manager.get_long_term("knowledge:sales_best_practices")
if entry:
    print(f"内容：{entry.value}")
```

### 3.3 删除记忆

```python
# 删除记忆
deleted = await manager.delete_long_term("report:2024-q3")
```

---

## 4. 统一记忆操作

### 4.1 获取（自动缓存）

```python
# 先查短期，再查长期（自动缓存到短期）
entry = await manager.get("user:123:preference")

# 等价于
entry = await manager.get_short_term("user:123:preference")
if not entry:
    entry = await manager.get_long_term("user:123:preference")
    if entry:
        # 自动缓存到短期
        await manager.set_short_term(
            key="user:123:preference",
            value=entry.value,
        )
```

### 4.2 设置

```python
from intentos import MemoryType

# 指定记忆类型
await manager.set(
    key="data",
    value="...",
    memory_type=MemoryType.SHORT_TERM,  # 或 LONG_TERM
)
```

### 4.3 删除

```python
# 删除所有类型的记忆
await manager.delete("key")

# 删除指定类型
await manager.delete("key", memory_type=MemoryType.SHORT_TERM)
```

---

## 5. 记忆检索

### 5.1 按标签检索

```python
# 获取单个标签
entries = await manager.get_by_tag("user")

# 遍历结果
for entry in entries:
    print(f"{entry.key}: {entry.value}")

# 获取多个标签（与运算）
entries = await manager.get_by_tags(["user", "vip"], op="and")

# 或运算
entries = await manager.get_by_tags(["report", "analysis"], op="or")
```

### 5.2 全文搜索

```python
# 基本搜索
results = await manager.search("销售")

# 带高亮
results = await manager.search(
    query="销售",
    highlight=True,
    highlight_prefix="<em>",
    highlight_suffix="</em>",
)

# 指定字段
results = await manager.search(
    query="销售",
    fields=["key", "value", "tags"],
)
```

### 5.3 语义搜索

```python
# 语义搜索（需要嵌入模型）
results = await manager.semantic_search(
    query="销售业绩分析",
    threshold=0.7,
    limit=10,
)

for result in results:
    print(f"相似度：{result.similarity}")
    print(f"内容：{result.entry.value}")
```

---

## 6. 记忆条目

### 6.1 MemoryEntry

```python
from intentos import MemoryEntry, MemoryType, MemoryPriority

# 创建记忆条目
entry = MemoryEntry(
    key="user:123",
    value={"name": "张三"},
    memory_type=MemoryType.SHORT_TERM,
    priority=MemoryPriority.NORMAL,
    tags=["user"],
    metadata={"source": "web"},
)

# 属性
print(entry.id)              # 唯一标识
print(entry.key)             # 键
print(entry.value)           # 值
print(entry.memory_type)     # 记忆类型
print(entry.priority)        # 优先级
print(entry.tags)            # 标签
print(entry.metadata)        # 元数据
print(entry.created_at)      # 创建时间
print(entry.updated_at)      # 更新时间
print(entry.expires_at)      # 过期时间
print(entry.access_count)    # 访问次数
print(entry.last_accessed)   # 最后访问时间

# 检查过期
if entry.is_expired():
    print("已过期")

# 设置过期时间
entry.set_expiry(3600)  # 1 小时

# 更新访问时间
entry.touch()

# 转换为字典
data = entry.to_dict()

# 从字典创建
entry = MemoryEntry.from_dict(data)
```

### 6.2 MemoryType

```python
from intentos import MemoryType

MemoryType.SHORT_TERM   # 短期记忆
MemoryType.LONG_TERM    # 长期记忆
```

### 6.3 MemoryPriority

```python
from intentos import MemoryPriority

MemoryPriority.LOW       # 低 (1)
MemoryPriority.NORMAL    # 普通 (2)
MemoryPriority.HIGH      # 高 (3)
MemoryPriority.CRITICAL  # 关键 (4)
```

---

## 7. 记忆后端

### 7.1 InMemoryBackend

进程内后端（短期记忆）：

```python
from intentos import InMemoryBackend

# 创建后端
backend = InMemoryBackend(max_size=10000)

# 设置记忆
from intentos import MemoryEntry
entry = MemoryEntry(key="test", value="data")
await backend.set(entry)

# 获取记忆
entry = await backend.get("test")

# 删除记忆
await backend.delete("test")

# 检查存在
exists = await backend.exists("test")

# 获取所有键
keys = await backend.keys()
keys = await backend.keys("user:*")  # 通配符

# 清空
await backend.clear()

# 获取大小
size = await backend.size()

# 获取所有记忆
entries = await backend.get_all()
```

### 7.2 RedisBackend

Redis 后端（长期记忆）：

```python
from intentos import RedisBackend

# 创建后端
backend = RedisBackend(
    host="localhost",
    port=6379,
    db=0,
    password=None,
    key_prefix="intentos:memory:",
)

# 设置记忆
await backend.set(entry)

# 获取记忆
entry = await backend.get("test")

# 删除记忆
await backend.delete("test")

# 发布消息（用于同步）
await backend.publish("sync", {"action": "update", "key": "test"})

# 订阅频道
async for message in backend.subscribe("sync"):
    print(f"收到消息：{message}")

# 获取统计
stats = await backend.get_stats()
print(f"使用内存：{stats['used_memory_human']}")
print(f"键数量：{stats['keys_count']}")
```

### 7.3 FileBackend

文件后端（长期记忆）：

```python
from intentos import FileBackend

# 创建后端
backend = FileBackend(data_dir="./memory_data")

# 设置记忆
await backend.set(entry)

# 获取记忆
entry = await backend.get("test")

# 删除记忆
await backend.delete("test")

# 获取所有键
keys = await backend.keys()
```

---

## 8. 记忆配置

### 8.1 MemoryConfig

```python
from intentos import MemoryConfig

config = MemoryConfig(
    # 短期记忆配置
    short_term_max_size=10000,    # 最大条目数
    short_term_ttl_seconds=3600,  # 默认 TTL
    
    # 长期记忆配置
    long_term_enabled=True,
    long_term_backend="redis",    # "redis" 或 "file"
    long_term_ttl_seconds=86400 * 30,  # 默认 30 天
    
    # Redis 配置
    redis_host="localhost",
    redis_port=6379,
    redis_db=0,
    redis_password=None,
    
    # 分布式配置
    node_id="node-001",
    sync_enabled=True,
    
    # 索引配置
    index_enabled=True,
    index_tags=True,
)
```

---

## 9. 记忆统计

```python
# 获取统计
stats = await manager.get_stats()

print(f"短期记忆数量：{stats.get('short_term_size', 0)}")
print(f"长期记忆数量：{stats.get('long_term_size', 0)}")
print(f"命中次数：{stats['hit_count']}")
print(f"未命中次数：{stats['miss_count']}")
print(f"同步次数：{stats['sync_count']}")
print(f"节点 ID: {stats['node_id']}")

# Redis 统计
if 'long_term' in stats:
    print(f"Redis 内存：{stats['long_term']['used_memory_human']}")
    print(f"Redis 键数：{stats['long_term']['keys_count']}")
```

---

## 10. 记忆同步

### 10.1 注册回调

```python
# 注册写入回调
def on_write(entry):
    print(f"记忆写入：{entry.key}")

manager.on_write(on_write)
```

### 10.2 关闭管理器

```python
# 关闭（清理资源）
await manager.shutdown()
```

---

## 11. 完整示例

### 11.1 用户会话管理

```python
from intentos import create_and_initialize_memory_manager

async def manage_user_session():
    manager = await create_and_initialize_memory_manager(
        short_term_max=10000,
        long_term_enabled=True,
        long_term_backend="redis",
    )
    
    try:
        # 用户登录，创建会话
        await manager.set_short_term(
            key=f"session:{user_id}",
            value={"user_id": user_id, "login_time": time.time()},
            tags=["session", user_id],
            ttl_seconds=3600,
        )
        
        # 用户活动，刷新会话
        await manager.set_short_term(
            key=f"session:{user_id}",
            value={"last_activity": time.time()},
            ttl_seconds=3600,
        )
        
        # 获取会话
        session = await manager.get(f"session:{user_id}")
        
        # 用户登出
        await manager.delete(f"session:{user_id}")
        
    finally:
        await manager.shutdown()
```

### 11.2 知识库管理

```python
async def manage_knowledge_base():
    manager = await create_and_initialize_memory_manager(
        long_term_backend="redis",
    )
    
    # 添加知识
    await manager.set_long_term(
        key="knowledge:sales:best_practices",
        value={
            "title": "销售最佳实践",
            "content": "1. 定期跟进客户...",
            "category": "sales",
        },
        tags=["knowledge", "sales"],
    )
    
    # 检索知识
    entries = await manager.get_by_tag("knowledge")
    
    # 搜索知识
    results = await manager.search("销售技巧")
    
    await manager.shutdown()
```

---

## 12. 总结

记忆 API 分类：

| 类别 | 主要类/函数 |
|------|-----------|
| **管理器** | DistributedMemoryManager, create_memory_manager |
| **配置** | MemoryConfig |
| **条目** | MemoryEntry, MemoryType, MemoryPriority |
| **后端** | InMemoryBackend, RedisBackend, FileBackend |
| **检索** | get_by_tag, search, semantic_search |
| **统计** | get_stats |

---

**下一篇**: [执行 API](04-execution-api.md)

**上一篇**: [编译器 API](02-compiler-api.md)
