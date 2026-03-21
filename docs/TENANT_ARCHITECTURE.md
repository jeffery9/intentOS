# IntentOS 租户架构

> **多租户隔离 · 资源配置 · 能力绑定**

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: Release Candidate

---

## 一、概述

### 1.1 什么是租户？

**租户 (Tenant)** 是 IntentOS 中资源隔离和配置管理的基本单位。每个租户拥有：

- **独立的资源** - 数据库、API、存储等
- **独立的能力** - 可用的功能列表
- **独立的配置** - 租户级配置项
- **独立的配额** - CPU、内存、API 调用等限制

### 1.2 租户 vs 用户

| 维度 | 租户 | 用户 |
|------|------|------|
| **定义** | 组织/公司/团队 | 个人 |
| **资源** | 拥有资源 | 使用租户资源 |
| **配置** | 租户级配置 | 个人偏好 |
| **隔离** | 数据隔离 | 配置隔离 |
| **计费** | 统一计费 | 个人用量 |

### 1.3 租户层级

```
┌─────────────────────────────────────────────────────────────────┐
│                        Platform                                  │
│                      (IntentOS)                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Tenant A│ │ Tenant B│ │ Tenant C│
    │ (acme)  │ │(globex) │ │(initech)│
    └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │
    ┌────┴────┐  ┌───┴────┐  ┌───┴────┐
    │         │  │        │  │        │
    ▼         ▼  ▼        ▼  ▼        ▼
 ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
 │Alice │ │ Bob │ │Carol │ │Dave │ │Eve  │
 └──────┘ └──────┘ └──────┘ └──────┘ └──────┘
```

---

## 二、租户管理

### 2.1 创建租户

```python
from intentos.agent.tenant import TenantManager, Tenant, ResourceQuota

# 创建租户管理器
tenant_manager = TenantManager()

# 创建租户
tenant = tenant_manager.create_tenant(
    tenant_id="acme_corp",
    name="ACME 公司",
    plan="pro",  # free/pro/enterprise
    quota=ResourceQuota(
        cpu_seconds=36000,      # CPU 秒数/月
        memory_mb=2048,         # 内存 MB
        storage_mb=10240,       # 存储 MB
        api_calls=100000,       # API 调用次数/月
        tokens=5000000,         # Token 数量/月
        bandwidth_mb=5000,      # 带宽 MB/月
    ),
    config={
        "region": "cn-east",
        "timezone": "Asia/Shanghai",
    }
)
```

### 2.2 租户套餐

| 套餐 | CPU 秒 | 内存 | 存储 | API 调用 | Token | 价格 |
|------|-------|------|------|---------|-------|------|
| **Free** | 3,600 | 512MB | 1GB | 10,000 | 1M | $0/月 |
| **Pro** | 36,000 | 2GB | 10GB | 100,000 | 5M | $99/月 |
| **Enterprise** | 360,000 | 20GB | 100GB | 1,000,000 | 50M | $999/月 |

### 2.3 管理租户

```python
# 获取租户
tenant = tenant_manager.get_tenant("acme_corp")

# 更新配置
tenant_manager.update_config(
    "acme_corp",
    {"region": "cn-north"}
)

# 列出租户
tenants = tenant_manager.list_tenants(status="active", plan="pro")

# 删除租户
tenant_manager.delete_tenant("acme_corp")
```

---

## 三、租户资源

### 3.1 资源类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **database** | 数据库连接 | MySQL, PostgreSQL, MongoDB |
| **api** | 外部 API | 天气 API, 支付 API |
| **storage** | 存储服务 | S3, OSS |
| **cache** | 缓存服务 | Redis, Memcached |
| **queue** | 消息队列 | Kafka, RabbitMQ |

### 3.2 添加资源

```python
from intentos.agent.tenant import TenantResource

# 添加数据库资源
tenant_manager.add_resource(
    "acme_corp",
    TenantResource(
        id="analytics_db",
        name="分析数据库",
        type="database",
        config={
            "host": "acme-db.internal",
            "port": 5432,
            "database": "analytics",
            "schema": "public",
        },
        credentials={
            "username": "acme_user",
            "password": "encrypted_password",  # 加密存储
        },
        endpoint="postgresql://acme-db.internal:5432/analytics",
    )
)

# 添加 API 资源
tenant_manager.add_resource(
    "acme_corp",
    TenantResource(
        id="weather_api",
        name="天气 API",
        type="api",
        config={
            "provider": "openweather",
            "base_url": "https://api.openweathermap.org",
        },
        credentials={
            "api_key": "encrypted_api_key",
        },
        endpoint="https://api.openweathermap.org/data/2.5",
    )
)
```

### 3.3 资源隔离

```
租户 A (acme_corp):
  ┌─────────────────────────────────────┐
  │  resources:                         │
  │    - analytics_db (acme 数据库)      │
  │    - weather_api (acme API key)     │
  │    - storage (acme S3 bucket)       │
  └─────────────────────────────────────┘

租户 B (globex_inc):
  ┌─────────────────────────────────────┐
  │  resources:                         │
  │    - sales_db (globex 数据库)        │
  │    - weather_api (globex API key)   │
  │    - storage (globex S3 bucket)     │
  └─────────────────────────────────────┘

完全隔离，互不影响
```

---

## 四、租户能力

### 4.1 能力定义

```python
from intentos.agent.tenant import TenantCapability

# 添加能力
tenant_manager.add_capability(
    "acme_corp",
    TenantCapability(
        id="data_loader",
        name="数据加载器",
        description="从数据源加载数据",
        bound_config={
            "data_source": "analytics_db",
            "max_rows": 10000,
        },
        rate_limit={
            "requests_per_minute": 60,
            "requests_per_day": 10000,
        },
        enabled=True,
    )
)
```

### 4.2 能力绑定

能力绑定根据租户资源配置具体的能力实现：

```python
from intentos.agent.capability_binding import CapabilityBinder

binder = CapabilityBinder()

# 绑定能力
bound_cap = binder.bind(
    template_id="data_loader",
    tenant_id="acme_corp",
    resources=tenant.resources,
    config={"data_source": "analytics_db"},
)

# 结果：data_loader 能力绑定到 acme_corp 的 analytics_db
```

### 4.3 启用/禁用能力

```python
# 启用能力
tenant_manager.enable_capability("acme_corp", "data_loader")

# 禁用能力
tenant_manager.disable_capability("acme_corp", "weather_api")

# 列出可用能力
capabilities = tenant.list_capabilities()
```

---

## 五、用户上下文

### 5.1 创建用户上下文

```python
from intentos.agent.tenant import UserContext, RoleManager

# 创建角色管理器
role_manager = RoleManager()

# 创建用户上下文
user_context = role_manager.create_user_context(
    tenant_id="acme_corp",
    user_id="alice@acme.com",
    roles=["user", "analyst"],  # 用户角色
    preferences={
        "theme": "dark",
        "language": "zh-CN",
    }
)
```

### 5.2 角色和权限

```python
# 预定义角色
roles = {
    "viewer": {
        "permissions": ["app:read", "data:read_own"],
    },
    "user": {
        "permissions": ["app:read", "app:execute", "data:read_own", "data:write_own"],
    },
    "developer": {
        "permissions": ["app:read", "app:execute", "app:deploy", "data:read_shared", "capability:register"],
    },
    "admin": {
        "permissions": ["*"],  # 所有权限
    },
}

# 检查权限
if user_context.has_permission("app:execute"):
    # 允许执行应用
    pass

if user_context.has_role("admin"):
    # 管理员操作
    pass
```

### 5.3 用户偏好

```python
from intentos.agent.personalization import PersonalizationManager

manager = PersonalizationManager()

# 设置用户偏好
manager.set_app_config(
    user_id="alice@acme.com",
    app_id="data_analyst",
    config={
        "theme": "dark",
        "default_chart": "bar",
        "export_format": "png",
    },
)

# 获取用户偏好
config = manager.get_app_config("alice@acme.com", "data_analyst")
```

---

## 六、用量与配额

### 6.1 用量统计

```python
# 获取用量统计
stats = tenant_manager.get_usage_stats("acme_corp")

# 结果示例
{
    "tenant_id": "acme_corp",
    "period": "current_month",
    "usage": {
        "cpu_seconds": 12500,
        "memory_mb": 850,
        "storage_mb": 3200,
        "api_calls": 45000,
        "tokens": 2100000,
    },
    "quota": {
        "cpu_seconds": 36000,
        "memory_mb": 2048,
        "storage_mb": 10240,
        "api_calls": 100000,
        "tokens": 5000000,
    },
    "usage_percent": {
        "cpu_seconds": 34.7,
        "api_calls": 45.0,
        "tokens": 42.0,
    },
}
```

### 6.2 配额限制

当租户用量超过配额时：

```python
# 检查配额
if stats["usage_percent"]["api_calls"] > 100:
    # 配额已用尽
    # 1. 拒绝新的 API 调用
    # 2. 发送告警通知
    # 3. 建议升级套餐
```

### 6.3 配额升级

```python
# 升级套餐
tenant.plan = "enterprise"
tenant.quota = ResourceQuota(
    cpu_seconds=360000,
    memory_mb=20480,
    storage_mb=102400,
    api_calls=1000000,
    tokens=50000000,
)
tenant_manager.update_tenant(tenant)
```

---

## 七、多租户应用场景

### 7.1 SaaS 应用

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

### 7.2 白标应用

```
租户 A (品牌 A):
  - Logo: brand_a.png
  - 域名：app.branda.com
  - 配色：{primary: "#FF0000"}
  
租户 B (品牌 B):
  - Logo: brand_b.png
  - 域名：app.brandb.com
  - 配色：{primary: "#0000FF"}

同一 App → 不同品牌 → 白标部署
```

### 7.3 灰度发布

```
租户 A (灰度租户):
  - 版本：v2.4.0-beta
  - 功能：新功能测试
  
租户 B (稳定租户):
  - 版本：v2.3.0
  - 功能：稳定功能

同一 App → 不同版本 → 灰度发布
```

---

## 八、最佳实践

### 8.1 租户命名

```python
# ✅ 正确：使用有意义的 ID
tenant_manager.create_tenant(tenant_id="acme_corp", name="ACME 公司")
tenant_manager.create_tenant(tenant_id="globex_inc", name="Globex 公司")

# ❌ 错误：使用随机 ID
tenant_manager.create_tenant(tenant_id="tenant_12345", name="ACME 公司")
```

### 8.2 资源配置

```python
# ✅ 正确：使用环境变量存储敏感信息
TenantResource(
    id="database",
    type="database",
    config={
        "host": os.getenv("DB_HOST"),
        "database": os.getenv("DB_NAME"),
    },
    credentials={
        "username": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    },
)

# ❌ 错误：硬编码敏感信息
TenantResource(
    id="database",
    credentials={
        "password": "super_secret_123",  # 明文密码
    },
)
```

### 8.3 权限控制

```python
# ✅ 正确：最小权限原则
user_context = role_manager.create_user_context(
    tenant_id="acme_corp",
    user_id="alice",
    roles=["user"],  # 普通用户权限
)

# ❌ 错误：过度授权
user_context = role_manager.create_user_context(
    tenant_id="acme_corp",
    user_id="alice",
    roles=["admin"],  # 管理员权限（不必要）
)
```

---

## 九、故障排查

### 9.1 资源访问失败

**问题**: `PermissionDenied: 租户 acme_corp 无法访问资源 analytics_db`

**解决方案**:
```python
# 检查资源是否存在
tenant = tenant_manager.get_tenant("acme_corp")
print(tenant.resources.get("analytics_db"))

# 检查资源类型
if resource.type != "database":
    # 类型不匹配
    pass

# 检查凭证
if not resource.credentials:
    # 缺少凭证
    pass
```

### 9.2 配额超限

**问题**: `QuotaExceeded: API 调用次数超过配额`

**解决方案**:
```python
# 检查用量
stats = tenant_manager.get_usage_stats("acme_corp")
print(f"API 调用：{stats['usage']['api_calls']}/{stats['quota']['api_calls']}")

# 升级套餐
tenant.plan = "enterprise"
tenant_manager.update_tenant(tenant)

# 或等待下月重置
```

### 9.3 能力绑定失败

**问题**: `ValueError: 能力 data_loader 需要资源 database，但租户未提供`

**解决方案**:
```python
# 检查租户资源
tenant = tenant_manager.get_tenant("acme_corp")
database_resources = [r for r in tenant.resources.values() if r.type == "database"]

if not database_resources:
    # 添加数据库资源
    tenant_manager.add_resource(...)
```

---

## 十、参考文档

| 文档 | 说明 |
|------|------|
| [AI Native App 概述](./AI_NATIVE_APP.md) | 核心概念、架构概览 |
| [即时生成架构](./JIT_GENERATION_ARCHITECTURE.md) | App 即时生成、身份感知 |
| [计费与收益](./BILLING_AND_REVENUE.md) | 计费模式、收益分成 |
| [安全与权限](./SECURITY_AND_PERMISSIONS.md) | 权限模型、安全策略 |

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Release Candidate
