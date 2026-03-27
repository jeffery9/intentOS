# VM 社区单归属约束架构设计

**文档版本**: 1.0  
**创建日期**: 2026-03-27  
**状态**: 已实现

---

## 1. 核心约束

### 1.1 单归属约束（Single Homing Constraint）

在 IntentOS 分布式架构中，语义 VM 节点的集群成员资格遵循以下约束：

> **节点可以加入任意 VM 集群/社区，但在任意时刻只能属于一个集群。**

这是一个**互斥约束**，类似于：
- 一个人在同一时间只能有一个合法婚姻
- 一个进程在同一时间只能有一个父进程
- 一个集合中的元素在同一时间只能属于一个划分

### 1.2 设计原则

| 原则 | 说明 |
|------|------|
| **去中心化** | 没有专门的 ClusterManager，节点通过共识形成社区 |
| **自由加入** | 节点可以自由选择加入任何社区 |
| **单一归属** | 同时只能属于一个社区（单归属约束） |
| **优雅迁移** | 从一个社区迁移到另一个社区需要优雅切换 |
| **共识验证** | 成员资格由社区共识验证 |

---

## 2. 架构组件

### 2.1 核心数据结构

```
┌─────────────────────────────────────────────────────────────────┐
│  ClusterMembership (集群成员资格)                                │
├─────────────────────────────────────────────────────────────────┤
│  - node_id: str            # 节点 ID                             │
│  - cluster_id: Optional[str]  # 当前所属集群 ID（None=无）        │
│  - status: MembershipStatus  # 成员状态                          │
│  - joined_at: datetime     # 加入时间                            │
│  - last_heartbeat: datetime  # 最后心跳时间                      │
│  - metadata: dict          # 元数据                              │
├─────────────────────────────────────────────────────────────────┤
│  方法：                                                           │
│  - is_member() -> bool     # 是否属于某个集群                     │
│  - can_join() -> bool      # 是否可以加入新集群                   │
│  - can_leave() -> bool     # 是否可以离开当前集群                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 成员状态机

```
┌──────────────────────────────────────────────────────────────────┐
│                    MembershipStatus 状态机                        │
│                                                                   │
│    ┌─────────┐                                                   │
│    │  NONE   │◄────────────────────────┐                         │
│    │ (未加入) │                         │                         │
│    └────┬────┘                         │                         │
│         │ join_community()              │                         │
│         ▼                               │                         │
│    ┌─────────┐     leave_community()    │                         │
│    │ ACTIVE  │─────────────────────────►┘                         │
│    │ (活跃)  │                                                   │
│    └─────────┘                                                   │
│         ▲                                                        │
│         │                                                        │
│    ┌────┴────┐                                                   │
│    │JOINING  │  中间状态：正在加入                                │
│    └─────────┘                                                   │
│                                                                   │
│    ┌─────────┐                                                   │
│    │ LEAVING │  中间状态：正在离开                                │
│    └─────────┘                                                   │
│                                                                   │
│    ┌─────────┐                                                   │
│    │SUSPENDED│  特殊状态：被暂停（可以加入新社区）                 │
│    └─────────┘                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 VM 社区（VMCommunity）

```python
@dataclass
class VMCommunity:
    """
    VM 社区（去中心化的集群）
    
    社区由节点共识形成，没有中央管理器
    """
    community_id: str           # 社区 ID
    name: str                   # 社区名称
    description: str            # 社区描述
    created_at: datetime        # 创建时间
    founder_id: str             # 创始节点 ID
    consensus_threshold: float  # 共识阈值（默认 2/3）
    members: dict[str, ClusterMembership]  # 成员列表
```

### 2.4 节点成员（VMCommunityMember）

```python
class VMCommunityMember:
    """
    VM 社区成员节点
    
    每个节点独立维护自己的成员资格，通过共识与社区同步
    """
    node_id: str
    membership: ClusterMembership
    known_communities: dict[str, VMCommunity]
```

---

## 3. 单归属约束实现

### 3.1 约束检查逻辑

```python
async def join_community(
    self,
    community: VMCommunity,
    metadata: Optional[dict[str, Any]] = None,
) -> ClusterMembership:
    """
    加入社区
    
    单归属约束：节点在加入新社区前必须离开当前社区
    """
    async with self._lock:
        # 检查单归属约束
        if not self.membership.can_join():
            raise SingleHomingViolationError(
                self.node_id,
                self.membership.cluster_id or "unknown",
                community.community_id,
            )
        
        # 检查社区容量
        if not community.has_capacity():
            raise CommunityFullError(community.community_id, 100)
        
        # 更新本地成员资格
        self.membership.cluster_id = community.community_id
        self.membership.status = MembershipStatus.ACTIVE
        self.membership.joined_at = datetime.now()
        
        return self.membership
```

### 3.2 状态转换条件

| 当前状态 | 目标状态 | 允许 | 条件 |
|----------|----------|------|------|
| NONE | ACTIVE | ✅ | 无 |
| NONE | JOINING | ✅ | 无 |
| ACTIVE | LEAVING | ✅ | 无 |
| ACTIVE | JOINING (新社区) | ❌ | 违反单归属约束 |
| LEAVING | NONE | ✅ | 无 |
| SUSPENDED | ACTIVE (新社区) | ✅ | 特殊状态允许 |

### 3.3 异常处理

```python
class SingleHomingViolationError(Exception):
    """
    单归属约束违反异常
    
    当节点尝试加入新集群但尚未离开原集群时抛出
    """
    def __init__(self, node_id: str, current_community_id: str, target_community_id: str):
        self.node_id = node_id
        self.current_community_id = current_community_id
        self.target_community_id = target_community_id
        super().__init__(
            f"节点 {node_id} 已属于社区 {current_community_id}，"
            f"无法加入社区 {target_community_id}。请先离开当前社区。"
        )
```

---

## 4. 社区共识协议

### 4.1 共识流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    社区共识流程                                  │
│                                                                  │
│  1. 提议                                                         │
│     节点 A 提议新成员 N 加入                                       │
│     ─────────────────────────────────────►                       │
│                                                                  │
│  2. 投票                                                         │
│     所有活跃成员投票（APPROVE/REJECT/ABSTAIN）                    │
│     ◄─────────────────────────────────────                       │
│                                                                  │
│  3. 计票                                                         │
│     统计票数，检查是否达到共识阈值                                │
│     - 批准票 >= 2/3 → 通过                                       │
│     - 拒绝票 >= 2/3 → 拒绝                                       │
│     - 其他 → 继续投票                                            │
│                                                                  │
│  4. 结果                                                         │
│     达成共识后，新成员可以正式加入                                │
│     ─────────────────────────────────────►                       │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 共识阈值

```python
consensus_threshold: float = 0.67  # 默认 2/3 多数

def check_consensus(proposal_id: str) -> tuple[bool, str]:
    """检查是否达成共识"""
    approve_votes = len([v for v in votes if v.result == APPROVE])
    active_members = len(community.get_active_members())
    required_votes = int(active_members * consensus_threshold)
    
    if approve_votes >= required_votes:
        return (True, "approved")
    
    return (False, "pending")
```

---

## 5. 社区发现协议（Gossip）

### 5.1 Gossip 传播

```python
class CommunityDiscoveryProtocol:
    """
    社区发现协议
    
    使用 Gossip 协议在节点间传播社区信息
    """
    
    def add_peer(self, node_id: str, address: str) -> None:
        """添加对等节点"""
        self.peers[node_id] = address
    
    async def gossip_community_info(self, community: VMCommunity) -> None:
        """Gossip 传播社区信息"""
        # 向已知对等节点广播社区信息
        for peer_id, peer_address in self.peers.items():
            await self._send_to_peer(peer_address, community)
```

### 5.2 社区发现流程

```
节点 A                      节点 B                      节点 C
  │                          │                          │
  │──── 加入 Community1 ────►│                          │
  │                          │                          │
  │◄──── Gossip 消息 ────────│                          │
  │  (Community1 信息)        │                          │
  │                          │                          │
  │─────────────────────────►│──── Gossip 消息 ────────►│
  │                          │  (Community1 信息)        │
  │                          │                          │
  │                          │                          │◄── 发现 Community1
```

---

## 6. 使用示例

### 6.1 基本用法

```python
from intentos.distributed import (
    create_community,
    create_community_member,
    SingleHomingViolationError,
)

# 创建节点
node = create_community_member(node_id="node_001")

# 创建社区
community1 = create_community(name="社区 A", founder_id="founder_001")
community2 = create_community(name="社区 B", founder_id="founder_002")

# 加入社区 A
await node.join_community(community1)
print(f"已加入：{node.membership.cluster_id}")

# 尝试加入社区 B（违反单归属约束）
try:
    await node.join_community(community2)
except SingleHomingViolationError as e:
    print(f"违反单归属约束：{e}")

# 正确方式：先离开，再加入
await node.leave_community()
await node.join_community(community2)
print(f"已迁移到：{node.membership.cluster_id}")
```

### 6.2 原子迁移

```python
# 原子迁移（自动先离开原社区，再加入新社区）
await node.migrate_to_community(community2)
```

### 6.3 共识投票

```python
from intentos.distributed import (
    create_consensus_protocol,
    ConsensusVotingResult,
)

# 创建共识协议
protocol = create_consensus_protocol(community)

# 提议新成员
proposal_id = await protocol.propose_new_member(
    node_id="new_node_001",
    proposer_id="node_000",
)

# 投票
await protocol.vote(
    proposal_id=proposal_id,
    voter_id="node_000",
    result=ConsensusVotingResult.APPROVE,
    reason="欢迎新成员",
)

# 检查共识
reached, result = await protocol.check_consensus(proposal_id)
if reached and result == "approved":
    print("共识达成，新成员可以加入")
```

---

## 7. 测试覆盖

### 7.1 核心测试用例

| 测试用例 | 说明 | 状态 |
|----------|------|------|
| `test_node_can_join_community` | 节点可以加入社区 | ✅ |
| `test_node_cannot_join_two_communities_simultaneously` | 节点不能同时加入两个社区 | ✅ |
| `test_node_must_leave_before_joining_new` | 节点必须先离开原社区才能加入新社区 | ✅ |
| `test_atomic_migration` | 原子迁移操作 | ✅ |
| `test_consensus_voting` | 共识投票 | ✅ |
| `test_consensus_rejected` | 共识被拒绝 | ✅ |

### 7.2 运行测试

```bash
# 运行单归属约束测试
PYTHONPATH=. python -m pytest tests/unit/test_cluster_manager.py -v
```

---

## 8. 与现有架构集成

### 8.1 与 DistributedSemanticVM 集成

```python
from intentos.distributed import DistributedSemanticVM, VMCommunityMember

# 分布式 VM 节点同时也是社区成员
class DistributedVMNode(VMCommunityMember):
    """
    分布式 VM 节点
    
    继承社区成员能力，同时具备语义 VM 功能
    """
    def __init__(self, node_id: str):
        super().__init__(node_id=node_id)
        self.vm = DistributedSemanticVM(node_id=node_id)
```

### 8.2 与 Self-Bootstrap 集成

```python
from intentos.bootstrap import SelfBootstrapExecutor

# 自举执行器可以修改社区成员资格规则
class CommunityBootstrapExecutor(SelfBootstrapExecutor):
    """
    社区自举执行器
    
    支持修改社区成员资格规则
    """
    async def modify_membership_rules(self, new_rules: dict) -> None:
        """修改成员资格规则"""
        # 通过共识修改单归属约束参数
        pass
```

---

## 9. 性能考虑

### 9.1 时间复杂度

| 操作 | 时间复杂度 | 说明 |
|------|------------|------|
| `join_community()` | O(1) | 本地状态更新 |
| `leave_community()` | O(1) | 本地状态更新 |
| `migrate_to_community()` | O(1) | 本地状态更新 |
| `check_consensus()` | O(n) | n 为活跃成员数 |
| `gossip_community_info()` | O(n) | n 为对等节点数 |

### 9.2 空间复杂度

| 数据结构 | 空间复杂度 |
|----------|------------|
| `ClusterMembership` | O(1) |
| `VMCommunity.members` | O(n) |
| `pending_proposals` | O(p) |
| `votes` | O(p × n) |

---

## 10. 安全考虑

### 10.1 单归属约束的安全性

单归属约束提供了以下安全保障：

1. **身份唯一性**：节点在集群中的身份唯一，防止身份伪造
2. **资源隔离**：防止节点同时占用多个集群的资源
3. **冲突避免**：避免节点在不同集群间执行冲突操作

### 10.2 共识安全性

共识协议提供以下安全保障：

1. **拜占庭容错**：2/3 共识阈值可容忍 1/3 的恶意节点
2. **投票审计**：所有投票记录可追溯
3. **提案验证**：提案必须经过验证才能进入投票流程

---

## 11. 未来工作

1. **持久化**：将成员资格持久化到 Redis/MongoDB
2. **跨社区通信**：实现不同社区间的节点通信
3. **社区联盟**：支持社区联盟（节点可以同时属于联盟中的多个社区）
4. **动态共识阈值**：根据社区规模动态调整共识阈值

---

**文档状态**: 已完成  
**下次审查日期**: 2026-04-10
