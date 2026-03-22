# 分布式记忆同步

> 在分布式环境中，多个 IntentOS 节点需要共享和同步记忆数据，Redis Pub/Sub 是实现同步的核心机制。

---

## 1. 概述

### 1.1 为什么需要同步

在分布式部署中，多个 IntentOS 节点需要共享记忆：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Node 1    │     │   Node 2    │     │   Node 3    │
│  Memory     │     │  Memory     │     │  Memory     │
│  Manager    │     │  Manager    │     │  Manager    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │  Pub/Sub    │
                    └─────────────┘
```

### 1.2 同步场景

| 场景 | 说明 | 示例 |
|------|------|------|
| **节点启动** | 新节点加入集群 | 扩容时 |
| **记忆更新** | 某节点更新了记忆 | 用户修改偏好 |
| **记忆删除** | 某节点删除了记忆 | GDPR 删除请求 |
| **节点故障** | 某节点宕机 | 故障转移 |

### 1.3 同步策略

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| **发布/订阅** | 实时更新推送 | 短期记忆同步 |
| **定期拉取** | 定期从中心拉取 | 长期记忆同步 |
| **混合模式** | 发布/订阅 + 定期拉取 | 生产环境 |

---

## 2. Redis Pub/Sub 机制

### 2.1 基本原理

```
┌─────────────┐      ┌─────────────┐
│  Publisher  │      │  Subscriber │
│  (Node 1)   │      │  (Node 2)   │
└──────┬──────┘      └──────▲──────┘
       │                    │
       │  1. PUBLISH        │
       │  "sync" channel    │
       │───────────────────>│
       │                    │
       │                    │  2. 接收消息
       │                    │  3. 更新本地记忆
```

### 2.2 消息格式

```python
@dataclass
class SyncMessage:
    """同步消息"""
    node_id: str           # 发送节点 ID
    action: str            # create | update | delete
    memory_type: str       # short_term | long_term
    key: str               # 记忆键
    value: Optional[dict]  # 记忆值 (删除时为空)
    timestamp: float       # 时间戳
    signature: str         # 签名 (验证来源)
```

### 2.3 发布消息

```python
class DistributedMemoryManager:
    async def _publish_sync(self, action: str, entry: MemoryEntry) -> None:
        """发布同步消息"""
        message = SyncMessage(
            node_id=self.node_id,
            action=action,
            memory_type=entry.memory_type.value,
            key=entry.key,
            value=entry.to_dict() if action != "delete" else None,
            timestamp=time.time(),
            signature=self._sign(entry.key),
        )
        
        await self.redis.publish(
            f"{self.key_prefix}sync",
            json.dumps(message.to_dict()),
        )
```

### 2.4 订阅消息

```python
async def _subscribe_sync(self) -> None:
    """订阅同步消息"""
    pubsub = self.redis.pubsub()
    await pubsub.subscribe(f"{self.key_prefix}sync")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            try:
                sync_msg = SyncMessage.from_dict(json.loads(message["data"]))
                
                # 忽略自己发布的消息
                if sync_msg.node_id == self.node_id:
                    continue
                
                # 验证签名
                if not self._verify_signature(sync_msg):
                    logger.warning(f"签名验证失败：{sync_msg.node_id}")
                    continue
                
                # 应用同步
                await self._apply_sync(sync_msg)
                
            except Exception as e:
                logger.error(f"处理同步消息失败：{e}")
```

---

## 3. 同步实现

### 3.1 创建同步

```python
async def set_long_term(
    self,
    key: str,
    value: Any,
    tags: list[str] = None,
    ttl_seconds: float = None,
) -> MemoryEntry:
    """设置长期记忆（带同步）"""
    entry = MemoryEntry(
        key=key,
        value=value,
        memory_type=MemoryType.LONG_TERM,
        tags=tags or [],
        expires_at=time.time() + (ttl_seconds or self.config.long_term_ttl),
        node_id=self.node_id,
        synced=False,
    )
    
    # 写入本地存储
    await self._long_term_backend.set(entry)
    
    # 发布同步消息
    if self.config.sync_enabled:
        await self._publish_sync("create", entry)
    
    return entry
```

### 3.2 应用同步

```python
async def _apply_sync(self, msg: SyncMessage) -> None:
    """应用同步消息"""
    if msg.action == "create" or msg.action == "update":
        entry = MemoryEntry.from_dict(msg.value)
        entry.synced = True
        
        if entry.memory_type == MemoryType.LONG_TERM:
            await self._long_term_backend.set(entry)
        
        elif entry.memory_type == MemoryType.SHORT_TERM:
            await self._short_term_backend.set(entry)
        
        logger.debug(f"同步记忆：{msg.key} from {msg.node_id}")
    
    elif msg.action == "delete":
        await self._long_term_backend.delete(msg.key)
        await self._short_term_backend.delete(msg.key)
        
        logger.debug(f"同步删除：{msg.key} from {msg.node_id}")
```

---

## 4. 冲突解决

### 4.1 时间戳策略

```python
async def _apply_sync(self, msg: SyncMessage) -> None:
    """应用同步消息（带冲突解决）"""
    if msg.action in ["create", "update"]:
        # 检查本地是否有更新的版本
        local_entry = await self.get(msg.key)
        
        if local_entry:
            if local_entry.updated_at > msg.value["updated_at"]:
                # 本地版本更新，忽略远程更新
                logger.debug(f"忽略旧版本：{msg.key}")
                return
        
        # 远程版本更新，应用同步
        entry = MemoryEntry.from_dict(msg.value)
        await self._long_term_backend.set(entry)
```

### 4.2 向量时钟

```python
@dataclass
class VectorClock:
    """向量时钟"""
    clocks: dict[str, int] = field(default_factory=dict)
    
    def increment(self, node_id: str) -> None:
        """增加本节点的时钟"""
        self.clocks[node_id] = self.clocks.get(node_id, 0) + 1
    
    def merge(self, other: "VectorClock") -> None:
        """合并其他时钟"""
        for node_id, clock in other.clocks.items():
            self.clocks[node_id] = max(self.clocks.get(node_id, 0), clock)
    
    def happens_before(self, other: "VectorClock") -> bool:
        """判断是否发生在之前"""
        all_less_or_equal = all(
            self.clocks.get(k, 0) <= other.clocks.get(k, 0)
            for k in set(self.clocks.keys()) | set(other.clocks.keys())
        )
        any_less = any(
            self.clocks.get(k, 0) < other.clocks.get(k, 0)
            for k in set(self.clocks.keys()) | set(other.clocks.keys())
        )
        return all_less_or_equal and any_less
```

---

## 5. 节点管理

### 5.1 节点注册

```python
async def register_node(self) -> None:
    """注册节点到集群"""
    node_info = {
        "node_id": self.node_id,
        "host": self.config.node_host,
        "port": self.config.node_port,
        "started_at": time.time(),
        "heartbeat": time.time(),
    }
    
    # 写入节点列表
    await self.redis.hset(
        f"{self.key_prefix}nodes",
        self.node_id,
        json.dumps(node_info),
    )
    
    # 设置过期时间（自动清理宕机节点）
    await self.redis.expire(
        f"{self.key_prefix}nodes:{self.node_id}",
        30,  # 30 秒无心跳则移除
    )
```

### 5.2 心跳机制

```python
async def start_heartbeat(self) -> None:
    """启动心跳"""
    while True:
        await asyncio.sleep(5)  # 每 5 秒心跳一次
        
        await self.redis.hset(
            f"{self.key_prefix}nodes:{self.node_id}",
            "heartbeat",
            str(time.time()),
        )
```

### 5.3 节点发现

```python
async def discover_nodes(self) -> list[dict]:
    """发现其他节点"""
    nodes_data = await self.redis.hgetall(f"{self.key_prefix}nodes")
    
    nodes = []
    current_time = time.time()
    
    for node_id, data in nodes_data.items():
        node = json.loads(data)
        
        # 检查心跳是否过期
        if current_time - node["heartbeat"] > 30:
            # 节点宕机，移除
            await self.redis.hdel(f"{self.key_prefix}nodes", node_id)
            continue
        
        nodes.append(node)
    
    return nodes
```

---

## 6. 完整示例

### 6.1 配置

```python
from intentos import create_memory_manager

# 节点 1
manager1 = create_memory_manager(
    short_term_max=1000,
    long_term_enabled=True,
    long_term_backend="redis",
    redis_host="redis-cluster",
    redis_port=6379,
    sync_enabled=True,
    node_id="node-001",
)
await manager1.initialize()

# 节点 2
manager2 = create_memory_manager(
    short_term_max=1000,
    long_term_enabled=True,
    long_term_backend="redis",
    redis_host="redis-cluster",
    redis_port=6379,
    sync_enabled=True,
    node_id="node-002",
)
await manager2.initialize()
```

### 6.2 同步演示

```python
# 节点 1 设置记忆
await manager1.set_long_term(
    key="shared:config",
    value={"setting": "value", "version": 1},
    tags=["shared"],
)

# 节点 2 会自动同步到这个更新
# 因为订阅了同一个 Redis 频道

# 节点 2 获取记忆
entry = await manager2.get("shared:config")
print(entry.value)  # {"setting": "value", "version": 1}
print(entry.node_id)  # "node-001"
print(entry.synced)  # True
```

---

## 7. 性能优化

### 7.1 批量同步

```python
async def _batch_sync(self, entries: list[MemoryEntry]) -> None:
    """批量同步"""
    if not entries:
        return
    
    # 打包多个更新为一个消息
    message = {
        "node_id": self.node_id,
        "action": "batch_update",
        "entries": [e.to_dict() for e in entries],
        "timestamp": time.time(),
    }
    
    await self.redis.publish(
        f"{self.key_prefix}sync",
        json.dumps(message),
    )
```

### 7.2 增量同步

```python
async def _incremental_sync(self, since: float) -> list[MemoryEntry]:
    """增量同步"""
    # 只同步 since 时间戳之后的更新
    entries = []
    
    async for entry in self._iterate_all():
        if entry.updated_at > since:
            entries.append(entry)
    
    return entries
```

---

## 8. 总结

分布式记忆同步的核心机制：

1. **Redis Pub/Sub**: 实时更新推送
2. **冲突解决**: 时间戳或向量时钟
3. **节点管理**: 注册、心跳、发现
4. **性能优化**: 批量、增量同步

---

## 附录 A: 混合同步模式

### A.1 混合模式架构

```python
class HybridSyncManager(MemorySyncManager):
    """混合同步管理器：Pub/Sub + 定期拉取"""

    def __init__(self, node_id: str, redis_url: str, pull_interval: int = 60):
        super().__init__(node_id, redis_url)
        self.pull_interval = pull_interval

    async def start(self):
        """启动混合同步"""
        # 1. 启动发布/订阅
        asyncio.create_task(self.subscribe_updates())

        # 2. 启动定期拉取
        asyncio.create_task(self.periodic_pull())

    async def periodic_pull(self):
        """定期从中心拉取记忆"""
        while True:
            try:
                # 从 Redis 拉取所有记忆
                all_memories = await self.redis.hgetall("intentos:memory:all")

                # 更新本地记忆
                for key, value in all_memories.items():
                    await self.update_local_memory(key, json.loads(value))

                logger.info(f"定期拉取完成：{len(all_memories)} 条记忆")

            except Exception as e:
                logger.error(f"定期拉取失败：{e}")

            await asyncio.sleep(self.pull_interval)
```

### A.2 适用场景

| 同步模式 | 适用场景 | 优点 | 缺点 |
|---------|---------|------|------|
| **Pub/Sub** | 短期记忆、实时更新 | 低延迟、即时同步 | 可能丢失消息 |
| **定期拉取** | 长期记忆、批量同步 | 可靠、不丢数据 | 延迟较高 |
| **混合模式** | 生产环境 | 兼顾实时性和可靠性 | 实现复杂 |

---

## 附录 B: 多区域部署

### B.1 区域架构

```python
regions = {
    "us-east": ["node1.us", "node2.us", "node3.us"],
    "eu-west": ["node1.eu", "node2.eu", "node3.eu"],
    "ap-east": ["node1.ap", "node2.ap", "node3.ap"],
}

# 数据本地化：每个区域的数据存储在本区域
for region, nodes in regions.items():
    await deploy_nodes(nodes, region=region)

# 跨区域同步：使用混合同步模式
sync_manager = HybridSyncManager(
    node_id="node1.us",
    redis_url="redis://redis.us:6379",
    pull_interval=300,  # 5 分钟拉取一次
)
await sync_manager.start()
```

### B.2 GDPR 合规

```python
class GDPRCompliantSync(MemorySyncManager):
    """GDPR 合规的同步管理器"""

    async def _apply_sync(self, msg: SyncMessage) -> None:
        """应用同步（检查数据出境限制）"""
        # 检查是否是跨境数据
        if self.is_cross_border(msg):
            # GDPR 数据不得出境
            if msg.value and "eu_user" in msg.value.get("tags", []):
                logger.warning(f"阻止 GDPR 数据出境：{msg.key}")
                return

        # 正常应用同步
        await super()._apply_sync(msg)

    def is_cross_border(self, msg: SyncMessage) -> bool:
        """检查是否跨境"""
        return msg.node_id.split(".")[-1] != self.node_id.split(".")[-1]
```

---

## 参考文档

- [分布式架构](../02-architecture/04-distributed-architecture.md)
- [记忆分层架构](01-memory-layers.md)
- [记忆检索](03-memory-retrieval.md)
- [性能优化策略](../PERFORMANCE_OPTIMIZATION.md)
