# AI Native App 安全与权限管理

> **基于能力的权限 · 沙箱隔离 · 全面审计**

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: Release Candidate

---

## 一、概述

### 1.1 安全原则

IntentOS 遵循以下安全原则：

1. **最小权限原则** - 只授予必要的权限
2. **默认拒绝** - 未明确允许的即禁止
3. **深度防御** - 多层安全防护
4. **全面审计** - 所有操作可追溯

### 1.2 权限模型

IntentOS 采用基于能力的权限模型 (Capability-Based Security)：

```
权限层级:
├── 文件系统权限 (file)
│   ├── read          # 读取文件
│   ├── write         # 写入文件
│   ├── execute       # 执行文件
│   └── delete        # 删除文件
│
├── 网络权限 (network)
│   ├── api_call      # API 调用
│   ├── http_get      # HTTP GET
│   ├── http_post     # HTTP POST
│   └── websocket     # WebSocket 连接
│
├── 数据权限 (data)
│   ├── read_own      # 读取自己的数据
│   ├── write_own     # 写入自己的数据
│   ├── read_shared   # 读取共享数据
│   └── admin         # 管理权限
│
├── 记忆权限 (memory)
│   ├── store         # 存储记忆
│   ├── retrieve      # 检索记忆
│   └── delete        # 删除记忆
│
└── 系统权限 (system)
    ├── shell         # Shell 命令
    ├── process       # 进程管理
    ├── config_read   # 读取配置
    └── config_write  # 写入配置
```

---

## 二、权限申请与授权

### 2.1 权限声明

```yaml
# manifest.yaml 中的权限声明
permissions:
  # 声明需要的权限
  required:
    - "file:read"
    - "network:api_call"
    - "memory:store"
    
  # 权限使用说明
  justification:
    "file:read": "需要读取用户上传的数据文件"
    "network:api_call": "需要调用外部 API 获取天气数据"
    "memory:store": "需要存储用户偏好设置"
    
  # 权限限制
  restrictions:
    "file:read":
      allowed_paths:
        - "/user/data/*"
        - "/tmp/*"
      max_file_size: "10MB"
      
    "network:api_call":
      allowed_domains:
        - "api.weather.com"
        - "api.openai.com"
      rate_limit: "100/minute"
```

### 2.2 权限审批流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 开发者提交应用                                                │
│    - 声明需要的权限                                             │
│    - 说明权限用途                                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 自动审核                                                      │
│    - 检查权限合理性                                             │
│    - 检查权限限制                                               │
│    - 检查敏感权限                                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
            ┌────────┴────────┐
            │                 │
            ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│   审核通过      │  │   需要人工审核   │
│   - 标准权限    │  │   - 敏感权限     │
│   - 有限制      │  │   - 系统权限     │
└─────────────────┘  └─────────────────┘
```

### 2.3 运行时权限检查

```python
from intentos.security import PermissionChecker

checker = PermissionChecker()

# 检查权限
if checker.has_permission("file:read"):
    # 允许读取文件
    pass
else:
    # 拒绝访问
    raise PermissionDenied("缺少 file:read 权限")

# 检查路径权限
if checker.check_path_permission("file:read", "/user/data/file.csv"):
    # 允许读取
    pass
else:
    # 拒绝访问
    raise PermissionDenied("无权访问该路径")
```

---

## 三、安全策略

### 3.1 输入验证

```yaml
# 安全策略配置
security_policies:
  # 输入验证
  input_validation:
    max_input_length: 10000        # 最大输入长度
    max_file_size: "10MB"          # 最大文件大小
    allowed_file_types:            # 允许的文件类型
      - ".csv"
      - ".xlsx"
      - ".json"
    sanitize_html: true            # HTML 清理
    prevent_injection: true        # 防止注入攻击
```

### 3.2 数据保护

```yaml
# 数据保护
data_protection:
  encryption:
    at_rest: "AES-256"             # 静态加密
    in_transit: "TLS-1.3"          # 传输加密
  data_retention_days: 30          # 数据保留期限
  pii_detection: true              # 个人信息检测
  pii_masking: true                # 个人信息脱敏
```

### 3.3 访问控制

```yaml
# 访问控制
access_control:
  authentication:
    required: true
    methods: ["api_key", "oauth2", "jwt"]
  authorization:
    model: "rbac"                  # 基于角色的访问控制
    roles:
      - "viewer"                   # 只读
      - "user"                     # 普通用户
      - "developer"                # 开发者
      - "admin"                    # 管理员
```

### 3.4 速率限制

```yaml
# 速率限制
rate_limiting:
  global:
    requests_per_second: 1000
    requests_per_day: 1000000
  per_user:
    requests_per_second: 10
    requests_per_day: 10000
  per_app:
    requests_per_second: 100
    requests_per_day: 100000
```

### 3.5 审计日志

```yaml
# 审计日志
audit_logging:
  enabled: true
  events:
    - "authentication"
    - "authorization_failure"
    - "data_access"
    - "configuration_change"
    - "permission_change"
  retention_days: 365
```

---

## 四、沙箱执行

### 4.1 沙箱配置

```python
# 沙箱执行配置
sandbox_config = {
    # 资源限制
    "resource_limits": {
        "cpu_time_seconds": 60,
        "memory_mb": 512,
        "disk_mb": 100,
        "network_bandwidth_mbps": 10,
    },
    
    # 系统调用限制
    "syscall_filter": {
        "allowed": [
            "read", "write", "open", "close",
            "stat", "fstat", "mmap", "munmap",
        ],
        "denied": [
            "execve", "fork", "ptrace",
            "setuid", "setgid",
        ],
    },
    
    # 文件系统隔离
    "filesystem": {
        "root": "/sandbox/{app_id}",
        "readonly_paths": ["/system", "/lib"],
        "tmpfs_size_mb": 100,
    },
    
    # 网络隔离
    "network": {
        "enabled": True,
        "allowed_hosts": [
            "api.intentos.io",
            "*.openai.com",
        ],
        "blocked_ports": [22, 23, 3389],
    },
    
    # 环境变量隔离
    "environment": {
        "inherit": False,
        "allowed_vars": [
            "INTENTOS_API_KEY",
            "INTENTOS_APP_ID",
        ],
    },
}
```

### 4.2 沙箱执行

```python
from intentos.security import SandboxExecutor

executor = SandboxExecutor(sandbox_config)

# 在沙箱中执行
result = await executor.execute(
    app_id="data_analyst",
    code=user_code,
    timeout=60
)

# 如果超出资源限制
if result.exceeded_quota:
    # 终止执行
    executor.terminate()
```

---

## 五、角色与权限

### 5.1 预定义角色

```python
# 预定义角色
ROLES = {
    "viewer": {
        "permissions": ["app:read", "data:read_own"],
        "description": "只读用户",
    },
    "user": {
        "permissions": [
            "app:read", "app:execute",
            "data:read_own", "data:write_own",
            "memory:store", "memory:retrieve"
        ],
        "description": "普通用户",
    },
    "developer": {
        "permissions": [
            "app:read", "app:execute", "app:deploy",
            "data:read_shared",
            "capability:register",
            "memory:store", "memory:retrieve", "memory:delete"
        ],
        "description": "开发者",
    },
    "admin": {
        "permissions": ["*"],  # 所有权限
        "description": "管理员",
    },
}
```

### 5.2 自定义角色

```python
from intentos.security import RoleManager

role_manager = RoleManager()

# 创建自定义角色
role_manager.create_role(
    role_id="analyst",
    name="数据分析师",
    permissions=[
        "app:read", "app:execute",
        "data:read_shared",
        "memory:retrieve"
    ],
    description="可以访问共享数据的分析师"
)

# 分配角色
role_manager.assign_role(
    user_id="alice",
    role_id="analyst"
)
```

---

## 六、安全审计

### 6.1 审计事件

```python
from intentos.security import AuditLogger

logger = AuditLogger()

# 记录审计事件
logger.log_event(
    event_type="data_access",
    user_id="alice",
    app_id="data_analyst",
    resource="file:///data/sales.csv",
    action="read",
    result="success",
    timestamp=datetime.now()
)
```

### 6.2 审计查询

```python
# 查询审计日志
logs = logger.query(
    user_id="alice",
    event_type="data_access",
    time_range="last_24h"
)

for log in logs:
    print(f"{log.timestamp}: {log.action} on {log.resource}")
```

### 6.3 异常检测

```python
# 检测异常行为
anomalies = logger.detect_anomalies(
    user_id="alice",
    time_range="last_hour"
)

for anomaly in anomalies:
    print(f"异常：{anomaly.type}")
    print(f"  说明：{anomaly.description}")
    print(f"  风险等级：{anomaly.risk_level}")
```

---

## 七、安全最佳实践

### 7.1 权限最小化

```yaml
# ✅ 正确：最小权限
permissions:
  required:
    - "file:read"  # 只读权限
  restrictions:
    "file:read":
      allowed_paths:
        - "/user/data/*"  # 限制路径

# ❌ 错误：过度权限
permissions:
  required:
    - "file:*"  # 所有文件权限
```

### 7.2 输入验证

```python
# ✅ 正确：验证输入
def process_file(path: str):
    # 验证路径
    if not path.startswith("/user/data/"):
        raise ValueError("无效路径")
    
    # 验证文件类型
    if not path.endswith((".csv", ".xlsx")):
        raise ValueError("不支持的文件类型")
    
    # 验证文件大小
    if os.path.getsize(path) > 10 * 1024 * 1024:
        raise ValueError("文件过大")
    
    # 处理文件
    ...

# ❌ 错误：无验证
def process_file(path: str):
    # 直接使用路径
    with open(path) as f:
        ...
```

### 7.3 敏感数据处理

```python
# ✅ 正确：脱敏处理
def process_user_data(data):
    # 脱敏个人信息
    if "email" in data:
        data["email"] = mask_email(data["email"])
    if "phone" in data:
        data["phone"] = mask_phone(data["phone"])
    return data

# ❌ 错误：明文处理
def process_user_data(data):
    # 直接返回原始数据
    return data
```

### 7.4 错误处理

```python
# ✅ 正确：安全错误处理
try:
    result = execute_user_code(code)
except Exception as e:
    # 不泄露内部细节
    logger.error(f"执行失败：{e}")
    raise UserError("执行失败，请联系管理员")

# ❌ 错误：泄露敏感信息
try:
    result = execute_user_code(code)
except Exception as e:
    # 泄露堆栈信息
    raise Exception(f"执行失败：{e}\n{traceback.format_exc()}")
```

---

## 八、参考文档

| 文档 | 说明 |
|------|------|
| [AI Native App 概述](./AI_NATIVE_APP.md) | 核心概念、架构概览 |
| [即时生成架构](./JIT_GENERATION_ARCHITECTURE.md) | App 即时生成、身份感知 |
| [租户架构](./TENANT_ARCHITECTURE.md) | 多租户隔离、资源配置 |

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Release Candidate
