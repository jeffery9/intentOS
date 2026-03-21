# IntentOS 租户架构 (v2.1 融合版)

> **多租户隔离 · 混合资源配额 · 私有能力嫁接 · 自动权限合成**

---

## 一、概述

### 1.1 什么是租户？

**租户 (Tenant)** 是 IntentOS 中资源隔离和配置管理的基本单位。每个租户拥有：

- **独立的资源** - 数据库、API、存储等
- **独立的能力** - 可用的功能列表
- **独立的配置** - 租户级配置项
- **独立的配额** - 物理资源（CPU/内存）与语义资源（Gas）的混合配额

### 1.2 租户 vs 用户

| 维度 | 租户 | 用户 |
|------|------|------|
| **定义** | 组织/公司/团队 | 个人 |
| **资源** | 拥有资源 | 使用租户资源 |
| **配置** | 租户级配置 | 个人偏好 |
| **隔离** | 数据隔离 | 配置隔离 |
| **计费** | 统一计费 | 个人用量 |

---

## 二、租户管理

### 2.1 创建租户 (混合配额)

```python
from intentos.paas.tenant import TenantManager, TenantQuota

manager = TenantManager()

# 创建混合配额租户
tenant = manager.create_tenant(
    tenant_id="acme_corp",
    name="ACME 公司",
    plan="pro",
    quota=TenantQuota(
        # 物理限制
        cpu_seconds=36000, 
        memory_mb=2048,
        # 语义 Gas 限制 (跨节点)
        total_gas_limit=1000000,
        max_gas_per_intent=5000 
    )
)
```

---

## 三、私有资源嫁接

### 3.1 资源类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **database** | 数据库连接 | MySQL, PostgreSQL, MongoDB |
| **api** | 外部 API | 天气 API, 支付 API |
| **storage** | 存储服务 | S3, OSS |

### 3.2 添加并嫁接资源
```python
from intentos.paas.tenant import TenantResource
from intentos.paas.capability_binding import get_capability_binder

# 1. 添加数据库资源
manager.add_resource(
    "acme_corp",
    TenantResource(id="analytics_db", name="分析数据库", type="database", ...)
)

# 2. 将物理资源嫁接到语义能力
binder = get_capability_binder()
binder.bind_private_resource(
    tenant_id="acme_corp",
    resource_id="analytics_db",
    capability_id="data_query" # App 使用的通用能力 ID
)
```

---

## 四、自动权限合成

`RoleManager` 会根据租户当前的资产状态，为用户动态生成权限列表。

### 4.1 权限包构成
当调用 `create_user_context` 时，返回的权限包含：
- **静态权限**: 基于角色（如 `app:execute`）。
- **动态特权**: 基于租户已绑定的所有私有能力（如 `tenant:acme_corp:use:data_query`）。

---

## 五、用量与配额

### 5.1 分布式用量统计
系统支持从分布式集群的任何节点实时汇总用量：
```python
# 获取集群视角的实时统计
stats = manager.get_usage_stats("acme_corp")

# 返回结果示例
{
    "usage": {
        "cumulative_gas": 150200,    # 跨节点累计 Gas
        "cpu_seconds": 1250          # 物理 CPU 消耗
    },
    "usage_percent": {
        "gas": 15.02,
        "cpu": 3.47
    }
}
```

---

## 六、多租户应用场景

### 6.1 SaaS 应用
```
租户 A (acme 公司):
  - 数据库：acme_analytics_db
  - 用户：Alice, Bob
  - 配置：{theme: dark, region: cn-east}
  
租户 B (globex 公司):
  - 数据库：globex_sales_db
  - 用户：Carol, Dave
  - 配置：{theme: light, region: us-west}

同一 App → 不同租户 → 数据隔离 → 配置独立
```

---

**文档版本**: 2.1 (融合版)  
**最后更新**: 2026-03-21  
**状态**: **v2.1 生产级标准**
