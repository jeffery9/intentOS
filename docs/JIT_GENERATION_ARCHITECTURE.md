# AI Native App 即时生成架构

> **即时生成 · 身份感知 · 个性化保持**

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: Release Candidate

---

## 一、核心理念

### 1.1 什么是即时生成？

**AI Native App 不是预编译的，而是在用户请求时根据以下因素即时生成的**：

1. **租户资源** - 租户提供的数据库、API、存储等资源
2. **用户身份** - 用户的角色、权限、所属组织
3. **个人偏好** - 用户的配置偏好、使用习惯
4. **版本选择** - 用户选择的 App 版本（或灰度发布）

### 1.2 与传统 App 的本质区别

| 维度 | 传统 App | AI Native App (即时生成) |
|------|---------|------------------------|
| **构建时机** | 开发时编译 | 运行时即时生成 |
| **应用实例** | 所有用户共享 | 每用户唯一实例 |
| **能力绑定** | 静态链接 | 动态绑定（根据租户资源） |
| **配置管理** | 配置文件 | 个性化配置（用户偏好） |
| **版本管理** | 统一升级 | 用户选择版本 |
| **数据隔离** | 数据库层面 | 应用实例层面 |

### 1.3 架构愿景

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户请求                                  │
│                   "分析销售数据"                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  IntentOS - App 即时生成引擎                                     │
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │ 身份识别    │ → │ 能力绑定    │ → │ App 生成     │          │
│  │ 租户/用户   │   │ 资源/权限   │   │ 动态组合    │          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────────────────────────────────────────────┐       │
│  │           运行时 App 实例 (唯一、隔离、个性化)            │       │
│  │  • 版本：v2.3 (用户选择的版本)                         │       │
│  │  • 能力：data_loader(analytics_db), analyzer, ...   │       │
│  │  • 配置：{theme: dark, default_chart: line, ...}    │       │
│  │  • 记忆：用户历史、偏好、数据                         │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、核心组件

### 2.1 租户管理 (`intentos/agent/tenant.py`)

租户是资源隔离和配置管理的基本单位。

#### 数据结构

```python
@dataclass
class Tenant:
    id: str                          # 租户 ID
    name: str                        # 租户名称
    status: str = "active"           # 状态
    plan: str = "free"               # 套餐
    quota: ResourceQuota             # 资源配额
    resources: dict[str, TenantResource]  # 资源列表
    capabilities: dict[str, TenantCapability]  # 能力列表
    config: dict[str, Any]           # 租户配置
```

#### 使用示例

```python
from intentos.agent.tenant import TenantManager, Tenant, ResourceQuota

# 创建租户管理器
tenant_manager = TenantManager()

# 创建租户
tenant = tenant_manager.create_tenant(
    tenant_id="acme_corp",
    name="ACME 公司",
    plan="pro",
    quota=ResourceQuota(
        cpu_seconds=36000,
        memory_mb=2048,
        api_calls=100000,
    )
)

# 添加资源（数据库连接）
tenant_manager.add_resource(
    "acme_corp",
    TenantResource(
        id="analytics_db",
        name="分析数据库",
        type="database",
        config={
            "host": "acme-db.internal",
            "database": "analytics",
        },
    )
)
```

详细 API 参考：[租户管理模块](../intentos/agent/tenant.py)

---

### 2.2 能力绑定 (`intentos/agent/capability_binding.py`)

能力绑定器根据租户资源动态绑定能力实现。

#### 能力模板

```python
@dataclass
class CapabilityTemplate:
    id: str                          # 模板 ID
    name: str                        # 能力名称
    handler_template: str            # 处理器模板（含占位符）
    required_resources: list[str]    # 需要的资源类型
    config_schema: dict[str, Any]    # 配置 Schema
```

#### 绑定示例

```python
from intentos.agent.capability_binding import CapabilityBinder

binder = CapabilityBinder()

# 绑定能力（根据租户资源）
bound_cap = binder.bind(
    template_id="data_loader",
    tenant_id="acme_corp",
    resources=tenant.resources,
    config={"data_source": "analytics_db"},
)

# 结果：data_loader 能力绑定到 acme_corp 的 analytics_db
```

#### 预定义模板

```python
# 数据加载器模板
DATA_LOADER_TEMPLATE = CapabilityTemplate(
    id="data_loader",
    name="数据加载器",
    required_resources=["database"],
    config_schema={
        "properties": {
            "data_source": {"type": "string", "default": "default_db"},
            "max_rows": {"type": "integer", "default": 10000},
        }
    },
)

# 分析器模板
ANALYZER_TEMPLATE = CapabilityTemplate(
    id="analyzer",
    name="数据分析器",
    required_resources=[],
    config_schema={
        "properties": {
            "analysis_engine": {"type": "string", "default": "builtin"},
            "confidence_threshold": {"type": "number", "default": 0.7},
        }
    },
)
```

详细 API 参考：[能力绑定模块](../intentos/agent/capability_binding.py)

---

### 2.3 App 生成器 (`intentos/agent/app_generator.py`)

App 生成器根据租户资源和用户身份即时生成 App 实例。

#### 生成流程

```python
from intentos.agent.app_generator import AppGenerator, AppGenerationRequest

# 创建 App 生成器
generator = AppGenerator(
    tenant_manager=tenant_manager,
    capability_binder=binder,
    personalization_manager=personalization_manager,
    version_manager=version_manager,
)

# 生成 App 实例
request = AppGenerationRequest(
    app_id="data_analyst",
    tenant_id="acme_corp",
    user_id="alice@acme.com",
    version="2.3",  # 可选，默认用户偏好版本
)

generated_app = generator.generate(request)
```

#### 生成的 App 实例

```python
@dataclass
class GeneratedApp:
    id: str                          # App 实例 ID
    app_id: str                      # App 定义 ID
    tenant_id: str                   # 租户 ID
    user_id: str                     # 用户 ID
    version: str                     # App 版本
    name: str                        # App 名称
    intents: dict[str, Any]          # 意图定义
    capabilities: dict[str, Any]     # 已绑定的能力
    config: dict[str, Any]           # 合并后的配置
    resources: dict[str, Any]        # 使用的资源
```

详细 API 参考：[App 生成器模块](../intentos/agent/app_generator.py)

---

### 2.4 版本管理 (`intentos/agent/versioning.py`)

版本管理器支持多版本共存、灰度发布、用户版本偏好。

#### 版本注册

```python
from intentos.agent.versioning import VersionManager, VersionStatus

version_manager = VersionManager()

# 注册版本
version_manager.register_version(
    app_id="data_analyst",
    version="2.3.0",
    manifest={...},
    status=VersionStatus.STABLE,
)
```

#### 用户版本偏好

```python
# 设置用户版本偏好
version_manager.set_user_version(
    user_id="alice@acme.com",
    app_id="data_analyst",
    version="2.3.0",
    auto_update=False,
)

# 获取用户版本偏好
user_version = version_manager.get_user_version(
    user_id="alice@acme.com",
    app_id="data_analyst",
)
```

#### 灰度发布

```python
# 创建灰度发布
rollout = version_manager.create_rollout(
    app_id="data_analyst",
    version="2.4.0-beta",
    percentage=10,  # 10% 用户
)

# 获取用户所在的灰度版本
rollout_version = version_manager.get_rollout_for_user(
    user_id="alice@acme.com",
    app_id="data_analyst",
)
```

详细 API 参考：[版本管理模块](../intentos/agent/versioning.py)

---

### 2.5 个性化配置 (`intentos/agent/personalization.py`)

个性化管理器管理用户的配置偏好。

#### 配置 Schema

```python
from intentos.agent.personalization import PersonalizationManager

manager = PersonalizationManager()

# 注册配置 Schema
manager.register_config_schema(
    app_id="data_analyst",
    schema={
        "type": "object",
        "properties": {
            "theme": {"type": "string", "enum": ["light", "dark"]},
            "default_chart": {"type": "string", "enum": ["line", "bar", "pie"]},
            "export_format": {"type": "string", "enum": ["png", "pdf", "svg"]},
        }
    },
    defaults={"theme": "light", "default_chart": "line"},
)
```

#### 用户配置

```python
# 设置用户配置
manager.set_app_config(
    user_id="alice@acme.com",
    app_id="data_analyst",
    config={"theme": "dark", "default_chart": "bar"},
)

# 获取有效配置（合并默认 + 租户 + 用户）
effective_config = manager.get_effective_config(
    user_id="alice@acme.com",
    app_id="data_analyst",
    app_defaults={"export_format": "png"},
)
# 结果：{"theme": "dark", "default_chart": "bar", "export_format": "png"}
```

详细 API 参考：[个性化配置模块](../intentos/agent/personalization.py)

---

## 三、工作流程

### 3.1 App 即时生成流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 用户发起请求                                                  │
│    "分析华东区 Q3 销售数据"                                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 身份识别                                                      │
│    - 租户 ID: acme_corp                                         │
│    - 用户 ID: alice@acme.com                                    │
│    - 角色：analyst                                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 获取用户 App 版本偏好                                          │
│    - data_analyst: v2.3.0                                       │
│    - auto_update: false                                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. 加载对应版本意图包                                            │
│    - manifest.yaml                                              │
│    - intents/                                                   │
│    - capabilities/                                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. 能力绑定 (根据租户资源)                                        │
│    - data_loader → data_loader(acme_analytics_db)               │
│    - analyzer → analyzer(acme_config)                           │
│    - reporter → reporter(acme_template)                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. 注入个性化配置                                                │
│    - theme: dark                                                │
│    - default_chart: bar                                         │
│    - export_format: png                                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. 生成运行时 App 实例                                            │
│    - App 实例 ID: app_data_analyst_a1b2c3d4                     │
│    - 唯一、隔离、个性化                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. 执行意图                                                      │
│    - 编译意图为 PEF                                             │
│    - 执行能力                                                   │
│    - 计量用量                                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. 返回结果 + 更新记忆                                           │
│    - 分析结果                                                   │
│    - 计费信息                                                   │
│    - 更新用户记忆                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、应用场景

### 4.1 多租户 SaaS

```
租户 A (acme 公司):
  - 数据库：acme_analytics_db
  - 能力：data_loader(acme_db), analyzer, reporter
  - 用户 Alice 偏好：line_chart, dark_theme
  - 版本：v2.3.0

租户 B (globex 公司):
  - 数据库：globex_sales_db
  - 能力：data_loader(globex_db), analyzer, reporter
  - 用户 Bob 偏好：bar_chart, light_theme
  - 版本：v2.2.0

同一 App 定义 → 不同租户 → 不同数据源 → 不同配置 → 隔离运行
```

### 4.2 版本灰度发布

```
App v2.4.0-beta 发布:

发布配置:
  - percentage: 10%  # 10% 用户
  - target_users: []  # 随机选择
  
用户分配:
  - Alice (hash=15) → v2.3.0 (稳定版)
  - Bob (hash=5) → v2.4.0-beta (灰度)
  
用户可手动选择:
  - "切换到稳定版" → v2.3.0
  - "体验最新版" → v2.4.0-beta
```

### 4.3 个性化保持

```
用户 Alice 使用数据分析 App:

首次使用 (v2.0):
  - 配置：默认 (theme=light, chart=line)
  
设置偏好 (v2.0):
  - theme: dark
  - chart: bar
  - export: png

下次使用 (v2.0):
  - 自动加载个人配置
  
App 升级 (v2.3):
  - 配置保持：theme=dark, chart=bar
  - 体验一致
```

---

## 五、技术实现

### 5.1 模块依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│                         App Generator                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Tenant     │  │  Capability  │  │  Version     │         │
│  │   Manager    │  │   Binder     │  │   Manager    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │           Personalization Manager                    │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 缓存策略

```python
from intentos.agent.app_generator import AppInstanceCache

# App 实例缓存
cache = AppInstanceCache(
    max_size=1000,      # 最多缓存 1000 个实例
    ttl_seconds=3600,   # TTL 1 小时
)

# 缓存 App 实例
cache.put(generated_app)

# 获取缓存
cached_app = cache.get(instance_id)

# 缓存失效
cache.invalidate(instance_id)
```

### 5.3 配置合并优先级

```
配置优先级（从高到低）:

1. 用户应用配置 (user_id + app_id)
   ↓
2. 用户全局配置 (user_id)
   ↓
3. 租户配置 (tenant_id)
   ↓
4. 应用默认配置 (app defaults)
```

---

## 六、最佳实践

### 6.1 租户设计

```python
# ✅ 正确：按组织划分租户
tenant_manager.create_tenant(tenant_id="acme_corp", name="ACME 公司")
tenant_manager.create_tenant(tenant_id="globex_inc", name="Globex 公司")

# ❌ 错误：按用户划分租户（应该用用户上下文）
tenant_manager.create_tenant(tenant_id="alice", name="Alice")
```

### 6.2 能力绑定

```python
# ✅ 正确：使用模板绑定
binder.bind(
    template_id="data_loader",
    tenant_id="acme_corp",
    resources=tenant.resources,
)

# ❌ 错误：硬编码资源
def load_data():
    return connect_to("acme-db.internal")
```

### 6.3 版本管理

```python
# ✅ 正确：允许用户选择版本
version_manager.set_user_version(
    user_id="alice",
    app_id="data_analyst",
    version="2.3.0",
    auto_update=False,  # 用户控制升级
)

# ❌ 错误：强制升级
version_manager.set_user_version(
    user_id="alice",
    app_id="data_analyst",
    version="2.4.0",
    auto_update=True,  # 强制自动升级
)
```

### 6.4 个性化配置

```python
# ✅ 正确：提供配置 Schema
manager.register_config_schema(
    app_id="data_analyst",
    schema={"type": "object", "properties": {...}},
    defaults={"theme": "light"},
)

# ❌ 错误：无 Schema 验证
manager.set_app_config(
    user_id="alice",
    app_id="data_analyst",
    config={"invalid_key": "value"},  # 无验证
)
```

---

## 七、故障排查

### 7.1 能力绑定失败

**问题**: `ValueError: 能力 data_loader 需要资源 database，但租户未提供`

**解决方案**:
```python
# 检查租户资源
tenant = tenant_manager.get_tenant("acme_corp")
print(tenant.resources)  # 应该包含 database 类型的资源

# 添加缺失的资源
tenant_manager.add_resource(
    "acme_corp",
    TenantResource(
        id="analytics_db",
        type="database",
        config={...},
    )
)
```

### 7.2 版本不存在

**问题**: `ValueError: 版本不存在：data_analyst v2.5.0`

**解决方案**:
```python
# 检查可用版本
versions = version_manager.list_versions("data_analyst")
for v in versions:
    print(f"{v.version} - {v.status.value}")

# 注册新版本
version_manager.register_version(
    app_id="data_analyst",
    version="2.5.0",
    manifest={...},
)
```

### 7.3 配置未生效

**问题**: 用户配置未应用到 App 实例

**解决方案**:
```python
# 检查配置是否设置
config = manager.get_app_config("alice", "data_analyst")
print(config)

# 检查 Schema 是否注册
schema = manager.get_config_schema("data_analyst")
if schema:
    print(f"Defaults: {schema.defaults}")

# 获取有效配置（合并所有层级）
effective = manager.get_effective_config(
    user_id="alice",
    app_id="data_analyst",
)
```

---

## 八、参考文档

| 文档 | 说明 |
|------|------|
| [AI Native App 概述](./AI_NATIVE_APP.md) | 核心概念、架构概览 |
| [租户架构](./TENANT_ARCHITECTURE.md) | 多租户隔离、资源配置 |
| [计费与收益](./BILLING_AND_REVENUE.md) | 计费模式、收益分成 |
| [意图包格式](./INTENT_PACKAGE_SPEC.md) | manifest.yaml Schema |
| [安全与权限](./SECURITY_AND_PERMISSIONS.md) | 权限模型、安全策略 |

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Release Candidate
