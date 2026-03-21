# AI Native App 概述

> **语言即系统 · Prompt 即可执行文件 · 语义 VM**

**文档版本**: 2.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Release Candidate

---

## 一、什么是 AI Native App？

**AI Native App** 是运行在 IntentOS 上的应用程序，其核心特征是：

1. **自然语言交互** - 用户通过自然语言而非 GUI 进行操作
2. **语义编译执行** - 意图被编译为 LLM 可执行的 PEF (Prompt Executable File)
3. **动态能力组合** - 运行时动态匹配和组合能力
4. **按使用计费** - 基于 Token 消耗的计费模式
5. **Self-Bootstrap** - 应用可以自我演进和扩展

---

## 二、分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│              PaaS 服务层 (PaaS Service Layer)                   │
│  • 多租户管理 • 计费系统 • 应用市场 • 开发者工具                │
└────────────────────┬────────────────────────────────────────────┘
                     │ IntentOS API
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              IntentOS 核心层 (IntentOS Core)                    │
│  • 语义 VM • 意图编译 • 能力注册 • 执行引擎 • 记忆系统          │
└─────────────────────────────────────────────────────────────────┘
```

**IntentOS 核心层**: 语言即系统 · Prompt 即可执行文件 · 语义 VM

**PaaS 服务层**: 多租户、计费、应用市场、开发者工具

---

## 三、IntentOS 核心层

### 3.1 核心模块

| 模块 | 功能 |
|------|------|
| **语义 VM** | LLM 作为处理器，执行语义指令 |
| **意图编译器** | 自然语言 → PEF |
| **能力注册中心** | 注册和管理能力 |
| **执行引擎** | 执行 PEF，调用能力 |
| **记忆系统** | 短期/长期记忆 |
| **上下文管理** | 租户/用户上下文 |

### 3.2 使用示例

```python
from intentos import Agent, AgentContext

agent = Agent()
context = AgentContext(tenant_id="acme_corp", user_id="alice")

result = await agent.execute(
    intent="分析华东区 Q3 销售数据",
    context=context
)

print(result.message)      # 自然语言回复
print(result.data)         # 数据结果
print(result.usage)        # Token 使用
```

### 3.3 能力注册

```python
from intentos import register_capability

@register_capability(
    id="data_loader",
    name="数据加载",
    description="从文件/数据库加载数据",
    tags=["data", "io"],
)
def load_data(path: str, context: AgentContext) -> dict:
    db = context.tenant_config.get("database")
    # 加载数据
    ...
```

---

## 四、PaaS 服务层

### 4.1 PaaS 服务模块

| 模块 | 功能 |
|------|------|
| **多租户管理** | 租户隔离、资源配置、配额管理 |
| **计费系统** | 用量计量、账单生成、支付、分成 |
| **应用市场** | App 发布、审核、上架、评价 |
| **开发者工具** | SDK、CLI、调试器、文档 |

### 4.2 多租户管理

```python
from intentos.paas import TenantManager

manager = TenantManager()
tenant = manager.create_tenant(
    tenant_id="acme_corp",
    name="ACME 公司",
    plan="pro",
)
```

### 4.3 计费系统

```python
from intentos.paas import BillingEngine

billing = BillingEngine()
billing.record_usage(tenant_id="acme_corp", tokens=2500)
invoice = billing.generate_invoice(tenant_id="acme_corp", period="2026-03")
```

### 4.4 应用市场

```python
from intentos.paas import AppMarketplace

marketplace = AppMarketplace()
app_id = marketplace.publish_app(developer_id="dev_alice", app_package={...})
```

---

## 五、开发流程

```
1. 定义意图包 → 2. 注册能力 → 3. 测试 → 4. 发布到市场 → 5. 获得收益
```

### 意图包结构

```
my-app/
├── SKILL.md              # 元数据
├── intents/              # 意图模板
├── capabilities/         # 能力定义
└── pricing/              # 计费规则
```

### 快速开始

```bash
# 1. 创建意图包
mkdir my_app && cd my_app

# 2. 创建 SKILL.md
cat > SKILL.md << EOF
---
name: my_app
description: 我的应用
license: MIT
---
EOF

# 3. 创建能力
mkdir capabilities
cat > capabilities/main.py << EOF
from intentos import register_capability

@register_capability(id="my_capability", name="我的能力")
def my_capability(param: str) -> dict:
    return {"result": f"处理：{param}"}
EOF

# 4. 发布
intentos marketplace publish my_app
```

---

## 六、计费模式

| 模型 | 计费单位 | 示例 |
|------|---------|------|
| **按量计费** | Token | $0.02/1K tokens |
| **订阅制** | 月/年 | $9.99/月 |
| **配额制** | 配额包 | $49.99/500 次 |

### 收益分成

```
用户支付 $100 → 开发者 $80 (80%) + 平台 $15 (15%) + 推荐者 $5 (5%)
```

---

## 七、示范 App

| App | 功能 | 计费 |
|-----|------|------|
| 🤖 智能客服 Bot | 自动回答用户问题 | $0.01/次 |
| 📊 数据分析助手 | 自然语言数据分析 | $0.10/分钟 |
| 💻 代码生成工具 | 多语言代码生成 | $0.02/1K tokens |
| 📝 文档总结服务 | 长文档自动总结 | $0.05/页 |
| 🌐 多语言翻译 | 100+ 语言互译 | $0.01/100 字 |

---

## 八、参考文档

| 文档 | 说明 |
|------|------|
| [分层架构](./LAYERED_ARCHITECTURE.md) | ⭐ 总入口：IntentOS 核心层 + PaaS 服务层 |
| [AI Native 核心理念](./AI_NATIVE_CORE_PRINCIPLES.md) | 语言即系统 · Prompt 即可执行文件 · 语义 VM |
| [意图包格式规范](./INTENT_PACKAGE_SPEC.md) | manifest.yaml Schema |
| [应用开发指南](./APP_DEVELOPMENT_GUIDE.md) | 开发流程、最佳实践 |
| [计费与收益](./BILLING_AND_REVENUE.md) | 计费模式、收益分成 |
| [安全与权限](./SECURITY_AND_PERMISSIONS.md) | 权限模型、安全策略 |
| [性能优化策略](./PERFORMANCE_OPTIMIZATION.md) | 缓存策略、并行执行 |
| [测试与调试指南](./TESTING_AND_DEBUGGING.md) | 单元测试、集成测试 |

---

**文档版本**: 2.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Release Candidate
