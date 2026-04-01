# IntentOS 进化系统架构说明

> **两种进化机制：个人级 vs 系统级**

**版本**: 1.0  
**日期**: 2026-04-01  

---

## 双进化系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    IntentOS 进化架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐        ┌─────────────────────┐        │
│  │   Evolution 层      │        │   Bootstrap 层      │        │
│  │   (个人级进化)      │        │   (系统级进化)      │        │
│  │                     │        │                     │        │
│  │ 从对话经验学习      │        │ 修改 OS 规则         │        │
│  │ 提炼个人技能        │        │ 扩展指令集          │        │
│  │ 冥想整理记忆        │        │ 自复制到新节点      │        │
│  │                     │        │                     │        │
│  │ intentos/evolution/ │        │ intentos/bootstrap/ │        │
│  └─────────────────────┘        └─────────────────────┘        │
│           │                              │                      │
│           │ 技能注册为系统能力           │                      │
│           └─────────────────────────────▶│                      │
│                                          │                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 两种进化机制对比

| 维度 | Evolution (个人级) | Bootstrap (系统级) |
|------|-------------------|-------------------|
| **职责** | 从对话经验提炼技能 | 修改 OS 规则 |
| **修改对象** | 个人技能库 | 解析器、执行器、指令集 |
| **触发方式** | 会话结束自动回顾 | 元指令显式修改 |
| **时间尺度** | 长期积累（5 session 冥想） | 即时修改 |
| **持久化** | `~/.intentos/skills/` | 系统存储 |
| **核心类** | `EvolutionEngine` | `SelfBootstrapExecutor` |
| **子模块** | memory/meditation/skill | executor/meta_intent/dual_memory_os |

---

## Evolution 层（个人级进化）

### 模块结构
```
intentos/evolution/
├── evolution_engine.py    # 进化引擎
└── session_manager.py     # 会话管理器

intentos/memory/           # 记忆层
intentos/meditation/       # 冥想层
intentos/skill/            # 技能层
```

### 进化流程
```
会话 → 回顾 → 记忆 → 冥想 → 技能 → 复用
  │      │      │      │      │      │
  ▼      ▼      ▼      ▼      ▼      ▼
用户   影子    存储   合并   提炼   自动
输入   Agent  记忆   矛盾   技能   匹配
```

### 使用示例
```python
from intentos.evolution import EvolutionEngine

engine = EvolutionEngine()

# 会话 1
engine.start_session()
engine.add_message("user", "如何分析数据？")
engine.add_message("assistant", "使用 pandas 加载")
engine.end_session()  # 自动回顾

# ... 更多会话后自动冥想、提炼技能
```

---

## Bootstrap 层（系统级进化）

### 模块结构
```
intentos/bootstrap/
├── executor.py              # Self-Bootstrap 执行器
├── meta_intent_executor.py  # 元指令执行器
├── dual_memory_os.py        # 双内存自修改 OS
├── self_modifying_os.py     # 自修改 OS
└── template_grower.py       # 意图模板自生长
```

### 自修改能力
1. **修改解析规则** - `modify_parse_prompt`
2. **修改执行规则** - `modify_execute_prompt`
3. **扩展指令集** - `extend_instructions`
4. **复制自身** - `self_reproduction`
5. **模板生长** - `template_grower`

### 使用示例
```python
from intentos.bootstrap import SelfBootstrapExecutor

bootstrap = SelfBootstrapExecutor(vm)

# 修改解析规则
await bootstrap.execute_bootstrap(
    action="modify_parse_prompt",
    target="default_parse_prompt",
    new_value="新的解析提示词...",
)
```

---

## 交互点

### Evolution → Bootstrap
提炼的技能可注册为系统能力：

```python
from intentos.evolution import EvolutionEngine
from intentos.bootstrap import SelfBootstrapExecutor

evolution = EvolutionEngine()
bootstrap = SelfBootstrapExecutor(vm)

# 从冥想结果提炼技能
skills = await evolution._skillify_from_meditation(result)

# 注册为系统能力
for skill in skills:
    evolution.register_skill_to_bootstrap(skill, bootstrap)
```

### Bootstrap → Evolution
系统规则修改可触发技能更新：

```python
# 修改执行规则后，可能需要更新相关技能
await bootstrap.execute_bootstrap(
    action="modify_execute_prompt",
    target="data_analysis",
    new_value="新的执行规则...",
)

# Evolution 层可监听此类修改，自动更新技能
```

---

## 设计原则

### 1. 职责分离
- **Evolution**: 个人经验积累，不需要系统权限
- **Bootstrap**: 系统规则修改，需要严格验证

### 2. 安全边界
- Evolution 提炼的技能默认在个人沙箱执行
- 注册为系统能力需通过 Bootstrap 验证器

### 3. 互补而非重复
- Evolution 关注"从经验学习"
- Bootstrap 关注"修改系统规则"
- 两者服务不同目标，不应合并

---

## 测试验证

```bash
# Evolution 层测试
pytest tests/unit/test_evolution.py -v  # 20 测试通过

# Bootstrap 层测试
pytest tests/unit/test_bootstrap*.py -v
```

---

## 总结

**IntentOS 拥有双进化系统**：
1. **Evolution** - 个人级，从对话经验学习
2. **Bootstrap** - 系统级，修改 OS 规则

**两者关系**：
- 职责不同，互补而非重复
- Evolution 提炼的技能可通过 Bootstrap 注册为系统能力
- Bootstrap 修改的规则可触发 Evolution 更新技能

**无分裂，有边界，可交互** 🙏
