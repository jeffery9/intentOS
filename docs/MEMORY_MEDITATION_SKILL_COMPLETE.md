# IntentOS 记忆 - 冥想 - 技能三位一体系统

> **记忆是进化的秘密 · 涌现的来源 · 硅基得道的不二法门**

**版本**: 1.0  
**完成日期**: 2026-04-01  
**状态**: Phase 1-4 完成

---

## 系统概述

```
┌─────────────────────────────────────────────────────────────────┐
│                    IntentOS 进化架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   记忆层     │      │   冥想层     │      │   技能层     │ │
│  │   Memory     │─────▶│  Meditation  │─────▶│   Skill      │ │
│  │              │      │              │      │              │ │
│  │ • 会话回顾   │      │ • 合并重复   │      │ • /skillify  │ │
│  │ • 成功/失败  │      │ • 删除矛盾   │      │ • 工作流提炼 │ │
│  │ • 影子 Agent │      │ • 淘汰过时   │      │ • 自动复用   │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│         │                     │                     │          │
│         └─────────────────────┼─────────────────────┘          │
│                               │                                │
│                    ┌──────────▼──────────┐                     │
│                    │   进化引擎          │                     │
│                    │   Evolution Engine  │                     │
│                    │                     │                     │
│                    │ • 会话管理          │                     │
│                    │ • 自动触发          │                     │
│                    │ • 完整循环          │                     │
│                    └─────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心哲学

### 记：不拣择
- 成功做法要记录
- 失败教训也要记录
- 每次对话后自动回顾

### 定：不散乱
- 攒够 5 个 session 自动冥想
- 合并重复、删除矛盾、淘汰过时
- 控制记忆不膨胀

### 慧：不执着
- 重复的工作流自动提炼为技能
- 技能可复用、可执行
- 新会话自动匹配技能

---

## Phase 1: 记忆层 ✅

### 模块结构
```
intentos/memory/
├── __init__.py
├── models.py           # MemoryEntry, SessionMemory, Pattern
├── shadow_agent.py     # 影子 Agent 回顾机制
├── store.py            # 记忆存储和检索
└── cli.py              # /memory 命令
```

### 核心功能

**影子 Agent 回顾**
```python
from intentos.memory import ShadowAgent

shadow = ShadowAgent(session_id="session_001")
shadow.add_message("user", "如何分析数据？")
shadow.add_message("assistant", "使用 pandas 加载数据")
shadow.end_session()  # 自动回顾，提取成功/失败/模式
```

**记忆存储**
```python
from intentos.memory import get_memory_store

store = get_memory_store()
memories = store.query_memories(MemoryQuery(
    memory_type=MemoryType.SUCCESS,
    limit=10,
))
```

### 测试
- 16 个测试用例全部通过

---

## Phase 2: 冥想层 ✅

### 模块结构
```
intentos/meditation/
├── __init__.py
├── engine.py           # 冥想引擎
├── merger.py           # 合并重复
├── conflict_resolver.py # 解决矛盾
└── pruner.py           # 淘汰过时
```

### 核心功能

**冥想引擎**
```python
from intentos.meditation import MeditationEngine, MeditationConfig

config = MeditationConfig(session_threshold=5)
engine = MeditationEngine(config)

# 添加会话
engine.add_session(session1)
engine.add_session(session2)
# ... 达到阈值后

# 执行冥想
result = await engine.meditate()
print(f"合并：{result.memories_merged}")
print(f"矛盾：{result.conflicts_resolved}")
print(f"淘汰：{result.memories_pruned}")
print(f"新原则：{len(result.new_memories)}")
```

**冥想四步骤**
1. 合并重复 - 相似度检测，合并为一条
2. 解决矛盾 - 检测否定词冲突，保留更重要的
3. 淘汰过时 - 时间/重要性/质量三维度剪枝
4. 提炼核心 - 从经验中提炼原则

### 测试
- 19 个测试用例全部通过

---

## Phase 3: 技能层 ✅

### 模块结构
```
intentos/skill/
├── __init__.py
├── models.py           # Skill, SkillStep, SkillTrigger
├── skillifier.py       # 技能提炼器
├── matcher.py          # 技能匹配器
├── store.py            # 技能存储
└── cli.py              # /skillify 命令
```

### 核心功能

**技能提炼**
```python
from intentos.skill import Skillifier

skillifier = Skillifier()
skill = await skillifier.skillify(session_id, memories)

# 技能包含:
# - 触发器（关键词 + 意图模式）
# - 步骤（从工作流提取）
# - 参数（自动参数化）
# - 质量评分
```

**/skillify 命令**
```bash
# CLI 中使用
/skillify <session_id>

# 输出:
✓ 成功提炼技能:
  名称：数据分析工作流
  步骤：4 步
  触发器：5 个关键词
  质量评分：0.85
```

**技能匹配**
```python
from intentos.skill import get_skill_store

store = get_skill_store()
matches = store.find_skills_by_trigger("帮我分析销售数据")

for skill, confidence in matches:
    print(f"{skill.name}: {confidence:.2f}")
```

### 测试
- 20 个测试用例全部通过

---

## Phase 4: 进化层 ✅

### 模块结构
```
intentos/evolution/
├── __init__.py
├── evolution_engine.py   # 进化引擎
└── session_manager.py    # 会话管理器
```

### 核心功能

**完整进化循环**
```python
from intentos.evolution import EvolutionEngine

engine = EvolutionEngine()

# 会话 1
engine.start_session(user_id="user_001")
engine.add_message("user", "如何分析数据？")
engine.add_message("assistant", "使用 pandas 加载")
engine.end_session()  # 自动回顾→记忆

# 会话 2-5...
# ...

# 达到阈值自动冥想
# 从冥想结果自动提炼技能

# 新会话自动匹配技能
engine.start_session(user_id="user_001")
engine.add_message("user", "帮我分析销售数据")

# 自动匹配
skills = engine.find_matching_skills("帮我分析销售数据")
for skill, confidence in skills:
    print(f"匹配技能：{skill.name} ({confidence:.2f})")
```

**进化统计**
```python
stats = engine.get_stats()
print(stats)
# {
#   "total_sessions": 10,
#   "completed_sessions": 10,
#   "total_memories": 45,
#   "meditations_triggered": 2,
#   "skills_created": 5,
#   "skills_executed": 12,
#   "skill_success_rate": 0.95
# }
```

### 测试
- 20 个测试用例全部通过

---

## 完整使用示例

### 1. 基础使用
```python
from intentos.evolution import EvolutionEngine

# 创建引擎
engine = EvolutionEngine()

# 开始对话
engine.start_session()
engine.add_message("user", "如何创建文件？")
engine.add_message("assistant", "使用 touch 命令")
engine.end_session()  # 自动回顾
```

### 2. 多会话进化
```python
# 多个会话后
for i in range(5):
    engine.start_session()
    engine.add_message("user", f"问题 {i}")
    engine.add_message("assistant", f"回答 {i}")
    engine.end_session()

# 自动触发冥想
# 自动提炼技能
```

### 3. 技能复用
```python
# 新会话自动匹配技能
engine.start_session()
engine.add_message("user", "帮我分析数据")

# 系统自动匹配之前提炼的"数据分析"技能
skills = engine.find_matching_skills("帮我分析数据")
```

---

## 测试总结

| Phase | 模块 | 测试数 | 通过率 |
|-------|------|--------|--------|
| Phase 1 | 记忆层 | 16 | 100% |
| Phase 2 | 冥想层 | 19 | 100% |
| Phase 3 | 技能层 | 20 | 100% |
| Phase 4 | 进化层 | 20 | 100% |
| **总计** | - | **75** | **100%** |

---

## 运行所有测试
```bash
cd /Users/jeffery/_project/IntentOS

# 运行所有相关测试
pytest tests/unit/test_memory.py -v
pytest tests/unit/test_meditation.py -v
pytest tests/unit/test_skill.py -v
pytest tests/unit/test_evolution.py -v

# 或运行全部
pytest tests/unit/test_*.py -v
```

---

## 下一步

1. **集成到 Runtime Agent** - 将进化引擎集成到节点
2. **用户界面** - Web UI 查看记忆、技能
3. **技能执行器** - 实际执行技能步骤
4. **分布式同步** - 跨节点共享记忆和技能

---

**阿弥陀佛 🙏**

记忆是进化的秘密，涌现的来源，硅基得道的不二法门。
