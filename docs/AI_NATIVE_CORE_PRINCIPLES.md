# AI Native App 核心理念

> **语言即系统 · Prompt 即可执行文件 · 语义 VM**

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: Draft

---

## 一、核心理念

### 1.1 语言即系统 (Language is the System)

**传统 OS**:
```
用户 → GUI/API → 系统调用 → 内核 → 硬件
```

**IntentOS**:
```
用户 → 自然语言 → 语义 VM → LLM → 执行
```

**关键区别**:
- 传统 OS: 用户学习系统（命令、API、界面）
- IntentOS: 系统理解用户（自然语言即接口）

### 1.2 Prompt 即可执行文件 (Prompt is Executable)

**传统 OS**:
```
源代码 → 编译器 → 二进制 (.exe) → CPU 执行
```

**IntentOS**:
```
意图 → 语义编译 → Prompt → LLM 执行
```

**PEF (Prompt Executable File)**:
```yaml
# PEF 示例
version: "1.0"
id: "pef_20260321140000"
intent: "分析华东区 Q3 销售数据"
system_prompt: "你是一个数据分析助手..."
user_prompt: "请分析华东区 Q3 销售数据"
capabilities: ["数据加载", "数据分析", "报告生成"]
execution_plan:
  - step: 1
    capability: "数据加载"
    input: "华东区 Q3 销售数据"
  - step: 2
    capability: "数据分析"
    input: "${step1.output}"
  - step: 3
    capability: "报告生成"
    input: "${step2.output}"
```

### 1.3 语义 VM (Semantic Virtual Machine)

**传统 VM**:
```
CPU → 取指 → 解码 → 执行 → 写回
      (指令：ADD, SUB, MOV...)
```

**语义 VM**:
```
LLM → 理解意图 → 任务规划 → 能力绑定 → 执行
      (语义指令：分析、创建、查询...)
```

**语义指令集**:
| 指令类型 | 指令 | 说明 |
|---------|------|------|
| 数据操作 | CREATE/MODIFY/DELETE/QUERY | 创建/修改/删除/查询 |
| 控制流 | IF/ELSE/LOOP/WHILE/JUMP | 条件/循环/跳转 |
| 能力调用 | CALL_CAPABILITY | 调用注册能力 |
| 记忆操作 | STORE/RETRIEVE | 存储/检索记忆 |

---

## 二、重新设计的架构

### 2.1 简化的三层架构

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: 应用层 (Application Layer)                        │
│  • 用户输入自然语言                                          │
│  • 系统输出自然语言 + 结果                                   │
│  • 无 GUI，语言即界面                                        │
└───────────────┬─────────────────────────────────────────────┘
                │ 意图 (Intent)
                ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: 意图层 (Intent Layer)                             │
│  • 意图解析 → 任务规划 → 能力绑定 → 执行                     │
│  • 输出：PEF (Prompt Executable File)                       │
└───────────────┬─────────────────────────────────────────────┘
                │ PEF (Prompt)
                ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: 模型层 (Model Layer)                              │
│  • LLM 作为语义 CPU                                          │
│  • 执行 PEF 中的语义指令                                     │
│  • 调用能力 (Capabilities)                                  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 什么不是 AI Native App

❌ **不是**：
- 传统 App + AI 功能
- 需要学习界面和操作
- 预定义流程和按钮
- 数据隔离靠数据库权限

❌ **不需要**：
- 复杂的多租户管理系统
- 应用市场和应用发布流程
- 复杂的计费系统
- 用户版本偏好管理

### 2.3 什么是 AI Native App

✅ **是**：
- 自然语言即界面
- 意图即应用
- 能力即词汇
- 语义编译即执行

✅ **核心机制**：
- **意图包** - 定义意图模板和能力
- **能力注册** - 注册可调用的能力
- **语义编译** - 将意图编译为 PEF
- **语义执行** - LLM 执行 PEF

---

## 三、简化的实现

### 3.1 意图包 (Intent Package)

```yaml
# SKILL.md - 意图包元数据
---
name: data_analyst
description: 数据分析助手
version: 1.0.0
---

# 数据分析助手

用自然语言分析数据，生成洞察和报告。

## 意图

- 分析数据
- 生成报告
- 查询趋势

## 能力

- 数据加载
- 数据分析
- 报告生成
```

### 3.2 能力注册

```python
from intentos.agent import register_capability

@register_capability(
    id="data_loader",
    name="数据加载",
    description="从文件/数据库加载数据",
    tags=["data", "io"],
)
def load_data(path: str) -> dict:
    """加载数据"""
    with open(path) as f:
        return {"data": f.read()}

@register_capability(
    id="data_analyzer",
    name="数据分析",
    description="分析数据并生成洞察",
    tags=["data", "analysis"],
)
def analyze_data(data: str) -> dict:
    """分析数据"""
    # 分析逻辑
    return {"insights": [...]}
```

### 3.3 语义执行流程

```
用户：分析华东区 Q3 销售数据

1. 意图解析
   → 意图：数据分析
   → 参数：区域=华东区，时间=Q3，数据类型=销售

2. 任务规划
   → 步骤 1: 加载数据
   → 步骤 2: 分析数据
   → 步骤 3: 生成报告

3. 能力绑定
   → 数据加载 → load_data()
   → 数据分析 → analyze_data()
   → 报告生成 → generate_report()

4. 生成 PEF
   → system_prompt: "你是一个数据分析助手..."
   → user_prompt: "请分析华东区 Q3 销售数据"
   → capabilities: ["数据加载", "数据分析", "报告生成"]

5. LLM 执行
   → 理解 PEF
   → 调用能力
   → 生成结果

6. 返回结果
   → 自然语言回复
   → 数据结果
```

---

## 四、多租户的简化理解

### 4.1 传统多租户 (复杂)

```
租户 A → 独立数据库 → 独立配置 → 独立应用实例
租户 B → 独立数据库 → 独立配置 → 独立应用实例
```

### 4.2 语义 VM 的多租户 (简化)

```
租户 A → 上下文 (Context) → 能力绑定到租户 A 的资源
租户 B → 上下文 (Context) → 能力绑定到租户 B 的资源
```

**关键区别**:
- 传统：物理隔离（数据库、配置、实例）
- 语义 VM：逻辑隔离（上下文、能力绑定）

### 4.3 简化实现

```python
# 上下文包含租户信息
context = AgentContext(
    tenant_id="acme_corp",
    user_id="alice",
    resources={
        "database": "acme_db",
        "api_key": "acme_api_key",
    }
)

# 能力根据上下文绑定
@register_capability(
    id="data_loader",
    name="数据加载",
)
def load_data(path: str, context: AgentContext) -> dict:
    # 使用租户的资源
    db = context.resources["database"]
    # 加载数据
    ...
```

---

## 五、计费的简化理解

### 5.1 传统计费 (复杂)

```
用量计量 → 计费引擎 → 账单生成 → 支付网关 → 收益分成
```

### 5.2 语义 VM 的计费 (简化)

```
执行 PEF → 记录 Token 使用 → 按 Token 计费
```

**关键理解**:
- Token 是语义 VM 的"CPU 周期"
- 按 Token 计费 = 按 CPU 使用计费

### 5.3 简化实现

```python
# 执行后自动记录 Token 使用
result = await agent.execute(intent, context)

# Token 使用
usage = {
    "input_tokens": result.usage.input_tokens,
    "output_tokens": result.usage.output_tokens,
    "total_tokens": result.usage.total_tokens,
}

# 计费
cost = usage["total_tokens"] * price_per_token
```

---

## 六、什么应该删除

### 6.1 过度设计的模块

| 模块 | 问题 | 简化方案 |
|------|------|---------|
| **租户管理** | 复杂的租户/资源/配额管理 | 简化为上下文 (Context) |
| **能力绑定** | 能力模板/绑定器/注入器 | 简化为能力注册 + 上下文 |
| **App 生成器** | 即时生成 App 实例 | 不需要，意图即应用 |
| **版本管理** | 多版本/灰度/回滚 | 简化为意图包版本 |
| **个性化配置** | 配置 Schema/合并 | 简化为记忆系统 |
| **应用市场** | 发布/审核/上架 | 简化为意图包注册 |

### 6.2 应该保留的核心

| 模块 | 说明 |
|------|------|
| **意图编译器** | 意图 → PEF |
| **能力注册中心** | 注册和管理能力 |
| **执行引擎** | 执行 PEF |
| **记忆系统** | 短期/长期记忆 |
| **上下文管理** | 租户/用户上下文 |

---

## 七、重新设计的路线图

### v13.0 - 回归核心理念

**目标**: 简化架构，回归"语言即系统 · Prompt 即可执行文件 · 语义 VM"

**核心功能**:
- [ ] 简化租户管理为上下文管理
- [ ] 简化能力绑定为能力注册 + 上下文
- [ ] 删除 App 生成器（意图即应用）
- [ ] 简化版本管理为意图包版本
- [ ] 简化计费为按 Token 计费

**删除模块**:
- [ ] intentos/agent/tenant.py (简化为 context)
- [ ] intentos/agent/capability_binding.py (简化为 registry)
- [ ] intentos/agent/app_generator.py (删除)
- [ ] intentos/agent/versioning.py (简化)
- [ ] intentos/agent/personalization.py (简化为记忆)

**保留模块**:
- [ ] intentos/agent/registry.py (能力注册)
- [ ] intentos/agent/compiler.py (意图编译)
- [ ] intentos/agent/executor.py (执行引擎)
- [ ] intentos/agent/context.py (上下文管理)
- [ ] intentos/agent/memory.py (记忆系统)

---

## 八、总结

### 核心理念检查清单

在设计任何功能时，问自己：

1. **是否符合"语言即系统"**?
   - 用户是否用自然语言交互？
   - 是否需要学习界面或 API？

2. **是否符合"Prompt 即可执行文件"**?
   - 意图是否编译为 PEF？
   - PEF 是否可独立执行？

3. **是否符合"语义 VM"**?
   - LLM 是否作为处理器？
   - 语义指令是否作为"机器码"？

### 简化原则

- **少即是多** - 删除不必要的抽象
- **回归本质** - 语言即系统，不是"系统 + 语言"
- **语义优先** - 用语义理解代替复杂逻辑

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Draft
