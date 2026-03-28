# IntentOS 双内存自修改系统

**版本**: 1.0  
**日期**: 2026-03-27  
**状态**: ✅ 已实现

---

## 🎯 核心架构

> **双内存设计：左脑运行，右脑升级，无缝切换**

灵感来源：
- 人类大脑：左右脑协同工作
- 航天系统：A/B 分区，热备份
- 数据库：影子复制，原子切换

```
┌─────────────────────────────────────────────────────────┐
│  IntentOS 双内存架构                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐         ┌─────────────┐               │
│  │   左脑      │         │   右脑      │               │
│  │  (Active)   │◄───────►│  (Standby)  │               │
│  │             │  同步    │             │               │
│  │ • 运行中    │         │ • 升级中    │               │
│  │ • 处理请求  │         │ • 安全修改  │               │
│  └─────────────┘         └─────────────┘               │
│         ▲                       ▲                       │
│         │                       │                       │
│         └───────────┬───────────┘                       │
│                     │                                   │
│              ┌──────▼──────┐                           │
│              │ 切换控制器   │                           │
│              │             │                           │
│              │ • 原子切换  │                           │
│              │ • 秒级回滚  │                           │
│              └─────────────┘                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 升级流程

### 完整流程

```
1. 开始升级
   ↓
   左脑：ACTIVE (运行中)
   右脑：UPGRADING (升级中)

2. 修改右脑
   - 添加新指令
   - 修改编译器规则
   - 修改执行器规则
   ↓
   左脑继续处理请求，不受影响

3. 验证升级
   - 检查必需指令
   - 计算校验和
   - 验证完整性
   ↓

4. 原子切换
   ↓
   左脑：STANDBY (备用)
   右脑：ACTIVE (运行中)

5. 完成
   - 新指令立即可用
   - 旧版本保留为备用
   - 可秒级回滚
```

---

## 📝 使用示例

### 示例 1: 基本升级流程

```python
from intentos.bootstrap import create_dual_memory_os

# 1. 创建系统
os = create_dual_memory_os()

print(f"活动内存库：{os.active_bank.name}")  # left
print(f"版本：{os.active_bank.version}")     # 1.0.0

# 2. 开始升级（右脑）
standby = os.start_upgrade()
print(f"开始升级：{standby.name}")  # right

# 3. 升级指令（不影响左脑运行）
def ar_render(**kwargs):
    return {"status": "ar_rendered", "data": kwargs}

os.upgrade_instruction("AR_RENDER", ar_render)
os.upgrade_instruction("VR_RENDER", lambda **kw: {"status": "vr"})

# 4. 升级规则
os.upgrade_compiler_rule("intent_parse", {"strategy": "llm_v2"})

# 5. 左脑仍在正常运行
result = os.left_bank.instructions["QUERY"](test="data")
print(f"左脑处理请求：{result}")

# 6. 完成升级并切换
success = os.complete_upgrade()

if success:
    print(f"✅ 切换到：{os.active_bank.name}")  # right
    print(f"新版本：{os.active_bank.version}")  # 1.0.1
    
    # 新指令立即可用
    result = os.active_bank.instructions["AR_RENDER"](data=[1,2,3])
    print(f"使用新指令：{result}")
```

### 示例 2: 升级失败自动回滚

```python
os = create_dual_memory_os()

# 开始升级
os.start_upgrade()

# 升级指令
os.upgrade_instruction("NEW_INSTR", lambda **kw: {"status": "new"})

# 完成升级（如果验证失败，自动回滚）
success = os.complete_upgrade()

if not success:
    print("❌ 升级失败，已自动回滚")
    print(f"当前活动库：{os.active_bank.name}")  # 仍然是 left
```

### 示例 3: 紧急切换（回滚）

```python
os = create_dual_memory_os()

# 假设新版本有问题
status = os.get_status()
print(f"活动库：{status['active_bank']}")

# 紧急切换回备用库
if os.can_switch_back():
    os.force_switch()
    print("✅ 已切换到备用库")
```

### 示例 4: 监控和审计

```python
os = create_dual_memory_os()

# 查看系统状态
status = os.get_status()
print(f"""
活动库：{status['active_bank']}
版本：{status['active_version']}
左脑指令数：{status['left_bank']['instructions_count']}
右脑指令数：{status['right_bank']['instructions_count']}
切换次数：{status['switch_count']}
""")

# 查看切换历史
history = os.get_switch_history(limit=10)
for h in history:
    print(f"{h.timestamp}: {h.from_bank} → {h.to_bank} ({'✓' if h.success else '✗'})")
```

---

## 🏗️ 核心 API

### DualMemoryOS

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `get_active_bank()` | 获取活动内存库 | MemoryBank |
| `get_standby_bank()` | 获取备用内存库 | MemoryBank |
| `start_upgrade()` | 开始升级流程 | MemoryBank |
| `upgrade_instruction(name, handler)` | 升级指令 | None |
| `upgrade_compiler_rule(name, rule)` | 升级编译器规则 | None |
| `upgrade_executor_rule(name, rule)` | 升级执行器规则 | None |
| `complete_upgrade()` | 完成升级并切换 | bool |
| `force_switch()` | 强制切换（回滚） | bool |
| `get_status()` | 获取系统状态 | dict |
| `get_switch_history(limit)` | 获取切换历史 | list |

### MemoryBank

| 属性 | 说明 | 类型 |
|------|------|------|
| `bank_id` | 内存库 ID | str |
| `name` | 名称（left/right） | str |
| `status` | 状态 | MemoryBankStatus |
| `version` | 版本号 | str |
| `instructions` | 指令集 | dict |
| `compiler_rules` | 编译器规则 | dict |
| `executor_rules` | 执行器规则 | dict |

---

## 🔐 安全机制

### 1. 隔离升级

```
左脑（运行中）          右脑（升级中）
    ↓                      ↓
处理用户请求          安全修改
    ↓                      ↓
不受升级影响          验证后才切换
```

### 2. 原子切换

```python
def complete_upgrade(self) -> bool:
    """原子切换：要么全成功，要么全失败"""
    try:
        # 验证
        if not self._verify_upgrade(standby):
            raise RuntimeError("验证失败")
        
        # 切换（原子操作）
        old_active.status = STANDBY
        standby.status = ACTIVE
        self.active_bank = standby
        
        return True
    except Exception:
        # 失败自动回滚
        self._rollback_upgrade()
        return False
```

### 3. 校验和验证

```python
def compute_checksum(self) -> str:
    """计算校验和，确保完整性"""
    import hashlib
    data = str({
        "instructions": list(self.instructions.keys()),
        "compiler_rules": list(self.compiler_rules.keys()),
        "version": self.version,
    })
    return hashlib.md5(data.encode()).hexdigest()
```

### 4. 审计轨迹

```python
@dataclass
class SwitchHistory:
    switch_id: str
    from_bank: str
    to_bank: str
    timestamp: datetime
    reason: str
    success: bool
    error: Optional[str]
    rolled_back: bool
```

---

## 📊 性能对比

| 操作 | 传统单内存 | 双内存架构 |
|------|------------|------------|
| **升级停机时间** | 需要停机 | 0 秒 |
| **升级风险** | 高（直接修改） | 低（隔离升级） |
| **回滚时间** | 分钟级 | 秒级 |
| **可用性** | 升级时不可用 | 100% 可用 |

---

## 🎯 实际应用场景

### 场景 1: 生产环境热升级

```python
# 凌晨 2 点，系统负载低
os = get_production_os()

# 开始升级（不影响用户）
os.start_upgrade()

# 添加新功能
os.upgrade_instruction("NEW_FEATURE", new_feature_handler)
os.upgrade_compiler_rule("parse_v2", new_parse_rule)

# 验证后切换
if os.complete_upgrade():
    send_notification("升级成功！")
else:
    send_notification("升级失败，已回滚", level="alert")
```

### 场景 2: A/B 测试

```python
# 左脑：版本 A（当前生产版本）
# 右脑：版本 B（新版本）

os.start_upgrade()
# ... 升级右脑到版本 B

# 切换后观察
os.complete_upgrade()

# 如果有问题，立即回滚
if monitor_error_rate() > threshold:
    os.force_switch()  # 切回版本 A
```

### 场景 3: 紧急修复

```python
# 发现严重 bug
os = get_production_os()

# 立即在备用库修复
os.start_upgrade()
os.upgrade_instruction("BUGGY_INSTR", fixed_handler)

# 快速切换
os.complete_upgrade()

# 总耗时：< 1 秒
```

---

## 📈 系统状态示例

```python
status = os.get_status()
print(status)

# 输出:
{
    "active_bank": "right",
    "active_version": "1.0.5",
    "left_bank": {
        "name": "left",
        "status": "standby",
        "version": "1.0.4",
        "instructions_count": 15,
        "compiler_rules_count": 8,
    },
    "right_bank": {
        "name": "right",
        "status": "active",
        "version": "1.0.5",
        "instructions_count": 17,
        "compiler_rules_count": 9,
    },
    "switch_count": 12,
    "pending_modifications": 0,
}
```

---

## 📚 相关文档

- [Self-Modifying OS](./SELF_MODIFYING_OS.md) - 单内存自修改
- [Self-Bootstrap](./SELF_BOOTSTRAP.md) - 自举机制
- [Meta-Intent](./META_INTENT_SPEC.md) - 元意图规范

---

**文档版本**: 1.0.0  
**最后更新**: 2026-03-27  
**维护者**: IntentOS Team
