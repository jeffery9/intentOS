# IntentOS 项目路线图 v2.0

> **核心原则：先实现完整的内核，然后再外扩、长大**

---

## 当前状态 (v0.5.0) - 基础架构完成 ✅

### ✅ 已完成模块

| 模块 | 状态 | 完成度 |
|------|------|--------|
| **核心数据模型** | ✅ 完成 | 100% |
| **意图编译器** | ✅ 完成 | 100% |
| **PEF 规范** | ✅ 完成 | 100% |
| **LLM 后端** | ✅ 完成 | 100% |
| **记忆管理** | ✅ 完成 | 100% |
| **记忆注入** | ✅ 完成 | 100% |
| **DAG 执行引擎** | ✅ 完成 | 100% |
| **文档系统** | ✅ 完成 | 100% |

---

## 🎯 核心原则：先内核，后外扩

### 内核定义

**IntentOS 内核 = Self-Bootstrap 能力**

```
┌─────────────────────────────────────────────────────────────┐
│  IntentOS Kernel (Self-Bootstrap Core)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  元意图 DSL (Meta-Intent DSL)                       │   │
│  │  - 定义意图的意图                                   │   │
│  │  - 系统自管理的语言基础                             │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  系统自省 (System Introspection)                    │   │
│  │  - 查询自身状态                                     │   │
│  │  - 了解自身能力                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  系统自修改 (System Self-Modification)              │   │
│  │  - 创建新意图模板                                   │   │
│  │  - 修改执行策略                                     │   │
│  │  - 注册新能力                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  安全边界 (Safety Boundary)                         │   │
│  │  - 权限分级                                         │   │
│  │  - 操作审计                                         │   │
│  │  - 回滚机制                                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 外扩定义

**内核稳定后，外扩生长**

```
内核稳定后:
├── 意图图谱 (复杂推理)
├── 形式化验证 (正确性保证)
├── 意图学习 (自动归纳)
├── 开发者工具 (CLI/LSP)
├── 分布式集群 (水平扩展)
└── 生态系统 (App Store/SDK)
```

---

## v0.6.0 - Self-Bootstrap 内核 (唯一目标) 🔴

### 阶段 1：元意图 DSL (Week 1-2)

**目标**: 定义系统自管理的语言基础

#### 1.1 元意图语法定义

```python
@dataclass
class MetaIntent:
    """元意图：管理意图的意图"""
    
    # 元意图动作
    action: MetaAction  # CREATE | MODIFY | DELETE | QUERY
    
    # 管理目标类型
    target_type: TargetType  # TEMPLATE | CAPABILITY | POLICY | CONFIG
    
    # 目标标识
    target_id: Optional[str] = None
    
    # 操作参数
    parameters: dict[str, Any] = field(default_factory=dict)
    
    # 执行约束
    constraints: dict[str, Any] = field(default_factory=dict)
```

**任务**:
- [ ] 定义 `MetaIntent` 数据类
- [ ] 定义 `MetaAction` 枚举 (CREATE/MODIFY/DELETE/QUERY)
- [ ] 定义 `TargetType` 枚举 (TEMPLATE/CAPABILITY/POLICY/CONFIG)
- [ ] 编写元意图语法规范文档

**预期代码**: ~200 行

---

#### 1.2 元意图解析器

```python
class MetaIntentParser:
    """元意图解析器"""
    
    def parse(self, source: str) -> MetaIntent:
        """解析自然语言为元意图"""
        # 例："创建一个名为 sales_analysis 的意图模板"
        # → MetaIntent(action=CREATE, target_type=TEMPLATE, ...)
        pass
    
    def validate(self, meta_intent: MetaIntent) -> list[str]:
        """验证元意图有效性"""
        errors = []
        
        # 检查必填字段
        if not meta_intent.action:
            errors.append("缺少 action")
        
        # 检查目标存在性 (DELETE/MODIFY 需要)
        if meta_intent.action in [MetaAction.DELETE, MetaAction.MODIFY]:
            if not meta_intent.target_id:
                errors.append("缺少 target_id")
        
        return errors
```

**任务**:
- [ ] 实现 `MetaIntentParser` 类
- [ ] 实现自然语言解析
- [ ] 实现验证逻辑
- [ ] 编写单元测试

**预期代码**: ~300 行

---

### 阶段 2：系统自省 API (Week 3)

**目标**: 系统了解自身状态

#### 2.1 意图模板查询

```python
class IntentRegistry:
    async def query_templates(
        self,
        tags: Optional[list[str]] = None,
        search: Optional[str] = None,
    ) -> list[IntentTemplate]:
        """查询意图模板"""
        pass
    
    async def get_template(self, name: str) -> Optional[IntentTemplate]:
        """获取特定模板"""
        pass
    
    async def list_templates(self) -> list[IntentTemplate]:
        """列出所有模板"""
        pass
```

**任务**:
- [ ] 实现 `query_templates` (支持标签过滤、搜索)
- [ ] 实现 `get_template`
- [ ] 实现 `list_templates`
- [ ] 编写单元测试

**预期代码**: ~200 行

---

#### 2.2 能力注册查询

```python
class IntentRegistry:
    async def list_capabilities(self) -> list[Capability]:
        """列出所有能力"""
        pass
    
    async def get_capability(self, name: str) -> Optional[Capability]:
        """获取特定能力"""
        pass
    
    async def search_capabilities(self, query: str) -> list[Capability]:
        """搜索能力"""
        pass
```

**任务**:
- [ ] 实现 `list_capabilities`
- [ ] 实现 `get_capability`
- [ ] 实现 `search_capabilities`
- [ ] 编写单元测试

**预期代码**: ~150 行

---

#### 2.3 执行历史查询

```python
class ExecutionEngine:
    async def get_execution_history(
        self,
        intent_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[ExecutionRecord]:
        """获取执行历史"""
        pass
    
    async def get_execution_stats(
        self,
        time_range: str = "24h",
    ) -> ExecutionStats:
        """获取执行统计"""
        pass
```

**任务**:
- [ ] 实现 `get_execution_history`
- [ ] 实现 `get_execution_stats`
- [ ] 实现执行记录存储
- [ ] 编写单元测试

**预期代码**: ~250 行

---

#### 2.4 系统状态查询

```python
class SystemStatus:
    async def get_status(self) -> dict[str, Any]:
        """获取系统状态"""
        return {
            "version": "0.6.0",
            "templates_count": await self.registry.count_templates(),
            "capabilities_count": await self.registry.count_capabilities(),
            "memory_usage": await self.memory_manager.get_stats(),
            "llm_status": await self.llm_executor.get_status(),
        }
```

**任务**:
- [ ] 实现 `get_status`
- [ ] 实现各组件状态查询
- [ ] 编写单元测试

**预期代码**: ~100 行

---

### 阶段 3：系统自修改 (Week 4)

**目标**: 系统可以修改自身

#### 3.1 创建意图模板

```python
class IntentRegistry:
    async def create_template(
        self,
        name: str,
        template: IntentTemplate,
        context: Context,
    ) -> CreateResult:
        """创建新意图模板"""
        
        # 1. 验证模板有效性
        errors = template.validate()
        if errors:
            return CreateResult(success=False, errors=errors)
        
        # 2. 检查名称冲突
        if name in self._templates:
            return CreateResult(success=False, errors=["名称已存在"])
        
        # 3. 注册模板
        self._templates[name] = template
        
        # 4. 记录审计日志
        await self.audit.log(
            action="create_template",
            user=context.user_id,
            details={"name": name},
        )
        
        return CreateResult(success=True, template_id=name)
```

**任务**:
- [ ] 实现 `create_template`
- [ ] 实现模板验证
- [ ] 实现审计日志
- [ ] 编写单元测试

**预期代码**: ~200 行

---

#### 3.2 修改执行策略

```python
class ExecutionEngine:
    async def update_policy(
        self,
        intent_type: str,
        policy: dict[str, Any],
        context: Context,
    ) -> UpdateResult:
        """修改执行策略"""
        
        # 1. 验证策略有效性
        errors = self._validate_policy(policy)
        if errors:
            return UpdateResult(success=False, errors=errors)
        
        # 2. 更新策略
        self._policies[intent_type] = policy
        
        # 3. 记录审计日志
        await self.audit.log(
            action="update_policy",
            user=context.user_id,
            details={"intent_type": intent_type, "policy": policy},
        )
        
        return UpdateResult(success=True)
```

**任务**:
- [ ] 实现 `update_policy`
- [ ] 实现策略验证
- [ ] 实现审计日志
- [ ] 编写单元测试

**预期代码**: ~200 行

---

#### 3.3 注册新能力

```python
class IntentRegistry:
    async def register_capability(
        self,
        name: str,
        capability: Capability,
        context: Context,
    ) -> RegisterResult:
        """注册新能力"""
        
        # 1. 验证能力有效性
        errors = self._validate_capability(capability)
        if errors:
            return RegisterResult(success=False, errors=errors)
        
        # 2. 注册能力
        self._capabilities[name] = capability
        
        # 3. 记录审计日志
        await self.audit.log(
            action="register_capability",
            user=context.user_id,
            details={"name": name},
        )
        
        return RegisterResult(success=True, capability_id=name)
```

**任务**:
- [ ] 实现 `register_capability`
- [ ] 实现能力验证
- [ ] 实现审计日志
- [ ] 编写单元测试

**预期代码**: ~200 行

---

### 阶段 4：安全边界 (Week 5)

**目标**: 确保自管理安全

#### 4.1 权限分级

```python
class PermissionLevel(Enum):
    """权限级别"""
    READ = "read"              # 只读
    WRITE = "write"            # 创建/修改
    ADMIN = "admin"            # 删除/策略修改
    SUPER_ADMIN = "super_admin" # 系统级操作

def require_permission(level: PermissionLevel):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, context: Context, *args, **kwargs):
            if not context.has_permission(level):
                raise PermissionError(f"需要 {level.value} 权限")
            return await func(self, context, *args, **kwargs)
        return wrapper
    return decorator

# 使用示例
@require_permission(PermissionLevel.WRITE)
async def create_template(self, ...):
    ...

@require_permission(PermissionLevel.ADMIN)
async def update_policy(self, ...):
    ...

@require_permission(PermissionLevel.SUPER_ADMIN)
async def delete_template(self, ...):
    ...
```

**任务**:
- [ ] 定义 `PermissionLevel` 枚举
- [ ] 实现 `require_permission` 装饰器
- [ ] 应用到所有自修改方法
- [ ] 编写单元测试

**预期代码**: ~150 行

---

#### 4.2 操作审计日志

```python
class AuditLogger:
    """审计日志"""
    
    async def log(
        self,
        action: str,
        user: str,
        details: dict[str, Any],
        result: str = "success",
    ) -> None:
        """记录操作日志"""
        record = AuditRecord(
            timestamp=datetime.now(),
            action=action,
            user=user,
            details=details,
            result=result,
        )
        
        # 存储到记忆系统
        await self.memory_manager.set_long_term(
            key=f"audit:{uuid.uuid4()}",
            value=record.to_dict(),
            tags=["audit", action],
        )
    
    async def query_logs(
        self,
        action: Optional[str] = None,
        user: Optional[str] = None,
        time_range: str = "24h",
    ) -> list[AuditRecord]:
        """查询审计日志"""
        pass
```

**任务**:
- [ ] 定义 `AuditRecord` 数据类
- [ ] 实现 `AuditLogger` 类
- [ ] 实现日志存储
- [ ] 实现日志查询
- [ ] 编写单元测试

**预期代码**: ~250 行

---

#### 4.3 回滚机制

```python
class SystemRollback:
    """系统回滚"""
    
    async def create_checkpoint(self, name: str) -> str:
        """创建系统检查点"""
        checkpoint = SystemCheckpoint(
            id=str(uuid.uuid4()),
            name=name,
            timestamp=datetime.now(),
            templates_snapshot=self.registry.get_all_templates(),
            capabilities_snapshot=self.registry.get_all_capabilities(),
            policies_snapshot=self.engine.get_all_policies(),
        )
        
        await self.storage.store(f"checkpoint:{checkpoint.id}", checkpoint)
        return checkpoint.id
    
    async def rollback(self, checkpoint_id: str) -> RollbackResult:
        """回滚到检查点"""
        checkpoint = await self.storage.retrieve(f"checkpoint:{checkpoint_id}")
        
        # 恢复模板
        self.registry.restore_templates(checkpoint.templates_snapshot)
        
        # 恢复能力
        self.registry.restore_capabilities(checkpoint.capabilities_snapshot)
        
        # 恢复策略
        self.engine.restore_policies(checkpoint.policies_snapshot)
        
        return RollbackResult(success=True)
```

**任务**:
- [ ] 定义 `SystemCheckpoint` 数据类
- [ ] 实现 `create_checkpoint`
- [ ] 实现 `rollback`
- [ ] 编写单元测试

**预期代码**: ~300 行

---

### 阶段 5：元意图示例库 (Week 6)

**目标**: 提供 Self-Bootstrap 使用示例

#### 5.1 示例 PEF 文件

```yaml
# examples/meta/create_template.pef
metadata:
  name: create_sales_template
  intent_type: meta

intent:
  action: create_template
  target_type: TEMPLATE
  parameters:
    name: sales_analysis_v2
    description: 销售分析模板 v2
    steps:
      - capability: query_sales
      - capability: analyze_trends
      - capability: generate_report
```

```yaml
# examples/meta/update_policy.pef
metadata:
  name: update_timeout_policy
  intent_type: meta

intent:
  action: update_policy
  target_type: POLICY
  parameters:
    intent_type: sales_analysis
    policy:
      timeout_seconds: 600
      retry_count: 5
```

**任务**:
- [ ] 创建 `create_template.pef`
- [ ] 创建 `update_policy.pef`
- [ ] 创建 `register_capability.pef`
- [ ] 创建 `query_templates.pef`
- [ ] 编写示例说明文档

**预期代码**: ~200 行 (PEF 文件)

---

## v0.6.0 内核完成标准

### 功能标准

- [ ] 元意图 DSL 定义完成
- [ ] 元意图解析器工作
- [ ] 系统自省 API 完整
- [ ] 系统自修改功能完整
- [ ] 安全边界（权限/审计/回滚）完整
- [ ] 元意图示例库完整

### 代码标准

- [ ] 核心代码：~3,000 行
- [ ] 测试用例：50+
- [ ] 测试覆盖率：90%+
- [ ] 文档：Self-Bootstrap 使用指南

### 验收标准

系统可以：
1. ✅ 用元意图创建新意图模板
2. ✅ 用元意图修改执行策略
3. ✅ 用元意图注册新能力
4. ✅ 查询自身状态（模板/能力/历史）
5. ✅ 权限分级保护
6. ✅ 操作审计记录
7. ✅ 系统回滚

---

## v0.7.0+ - 外扩生长 (内核稳定后)

### 意图图谱 (复杂推理)
- 意图间依赖关系
- 多跳推理
- 子图复用

### 形式化验证 (正确性保证)
- DAG 有效性验证
- 类型检查
- 执行轨迹回放

### 意图学习 (自动归纳)
- 从高频对话提炼模板
- 意图优化建议
- 用户反馈收集

### 开发者工具 (开发体验)
- CLI 工具
- PEF 语言服务器
- 可视化 DAG 编辑器

### 分布式集群 (水平扩展)
- 负载均衡
- 故障恢复
- 自动扩缩容

### 生态系统 (社区建设)
- App Store
- SDK
- 插件系统

---

## 里程碑 (v2.0)

| 版本 | 日期 | 里程碑 | 关键交付物 |
|------|------|--------|-----------|
| v0.5.0 | 2026-03-12 | 基础架构完成 | ✅ 已完成 |
| **v0.6.0** | **2026-04-12** | **Self-Bootstrap 内核** | 🔴 进行中 |
| v0.6.1 | 2026-04-19 | 元意图 DSL | 元意图语法、解析器 |
| v0.6.2 | 2026-04-26 | 系统自省 API | 查询 API 完整 |
| v0.6.3 | 2026-05-03 | 系统自修改 | 创建/修改/注册 |
| v0.6.4 | 2026-05-10 | 安全边界 | 权限/审计/回滚 |
| **v0.6.0** | **2026-05-17** | **内核完成** | **完整 Self-Bootstrap** |
| v0.7.0 | 2026-06-12 | 意图图谱 + 验证 | 外扩开始 |
| v1.0.0 | 2026-12-12 | 正式发布 | 完整生态系统 |

---

## 本周行动项 (2026-03-12 ~ 2026-03-19)

### Week 1: 元意图 DSL

1. [ ] **定义 MetaIntent 数据类**
   - [ ] MetaAction 枚举
   - [ ] TargetType 枚举
   - [ ] MetaIntent 数据类

2. [ ] **实现 MetaIntentParser**
   - [ ] 自然语言解析
   - [ ] 验证逻辑
   - [ ] 单元测试

3. [ ] **编写元意图规范文档**
   - [ ] 语法定义
   - [ ] 语义定义
   - [ ] 使用示例

---

## 核心原则重申

> **先实现完整的内核，然后再外扩、长大**

### 内核优先

1. **Self-Bootstrap 是核心**
   - 其他功能都可以等
   - 只有 Self-Bootstrap 是 IntentOS 的独特价值

2. **内核必须完整**
   - 元意图 DSL
   - 系统自省
   - 系统自修改
   - 安全边界
   - 缺一不可

3. **内核必须稳定**
   - 90%+ 测试覆盖率
   - 完整的审计日志
   - 可靠的回滚机制

### 外扩后行

1. **意图图谱可以等**
   - 没有图谱，系统依然可以运行
   - 有了 Self-Bootstrap，图谱可以自己生长

2. **形式化验证可以等**
   - 没有验证，系统依然可以用
   - 有了 Self-Bootstrap，验证可以自己实现

3. **开发者工具可以等**
   - 没有工具，开发者可以用 API
   - 有了 Self-Bootstrap，工具可以自己生成

---

**文档版本**: 2.0  
**创建日期**: 2026-03-12  
**最后更新**: 2026-03-13  
**负责人**: IntentOS Team
