# AI Native App 测试与调试指南

> **全面测试 · 智能调试 · 性能分析**

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: Release Candidate

---

## 一、概述

### 1.1 测试层次

```
┌─────────────────────────────────────────────────────────────────┐
│ 测试金字塔                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                        ┌───────┐                               │
│                       │ E2E   │  端到端测试 (10%)              │
│                      ├─────────┤                              │
│                     │ 集成测试 │  集成测试 (20%)                │
│                    ├─────────────┤                            │
│                   │   单元测试    │ 单元测试 (70%)              │
│                  └─────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 测试覆盖率目标

| 模块 | 覆盖率目标 | 说明 |
|------|-----------|------|
| **核心逻辑** | > 90% | 意图处理、能力执行 |
| **边界条件** | > 80% | 异常处理、错误恢复 |
| **集成接口** | > 85% | API、数据库、外部服务 |
| **关键路径** | 100% | 计费、安全、认证 |

---

## 二、单元测试

### 2.1 测试框架

```python
# tests/test_intents.py
import pytest
from intentos.testing import IntentTestCase, mock_capability


class TestDataAnalysisIntent(IntentTestCase):
    """数据分析意图测试"""
    
    app_id = "data_analyst"
    intent_id = "data_analysis"
    
    @mock_capability("data_loader", returns={"data": [], "metadata": {"row_count": 0}})
    @mock_capability("analyzer", returns={"insights": []})
    @mock_capability("reporter", returns={"report": "测试报告"})
    async def test_empty_data(self):
        """测试空数据处理"""
        result = await self.execute_intent(
            intent="分析数据",
            parameters={"data_source": "file://empty.csv"}
        )
        
        assert result.success is True
        assert "没有数据" in result.message
        
    @mock_capability("data_loader", returns={
        "data": [{"revenue": 100}, {"revenue": 200}],
        "metadata": {"row_count": 2}
    })
    @mock_capability("analyzer", returns={
        "insights": [{"title": "收入增长", "confidence": 0.9}]
    })
    @mock_capability("reporter", returns={"report": "详细报告"})
    async def test_normal_analysis(self):
        """测试正常分析流程"""
        result = await self.execute_intent(
            intent="分析销售数据",
            parameters={"data_source": "file://sales.csv"}
        )
        
        assert result.success is True
        assert len(result.data["insights"]) > 0
        assert result.data["insights"][0]["title"] == "收入增长"
        
    async def test_invalid_source(self):
        """测试无效数据源"""
        result = await self.execute_intent(
            intent="分析数据",
            parameters={"data_source": "invalid://path"}
        )
        
        assert result.success is False
        assert "无效的数据源" in result.error
```

### 2.2 能力测试

```python
# tests/test_capabilities.py
import pytest
from intentos.testing import CapabilityTestCase


class TestDataLoader(CapabilityTestCase):
    """数据加载能力测试"""
    
    capability_id = "data_loader"
    
    async def test_csv_load(self):
        """测试 CSV 文件加载"""
        result = await self.execute_capability(
            path="file://tests/fixtures/test.csv"
        )
        
        assert result["success"] is True
        assert len(result["data"]) == 10
        assert result["metadata"]["row_count"] == 10
        
    async def test_json_load(self):
        """测试 JSON 文件加载"""
        result = await self.execute_capability(
            path="file://tests/fixtures/test.json"
        )
        
        assert result["success"] is True
        assert "data" in result
        
    async def test_file_not_found(self):
        """测试文件不存在"""
        result = await self.execute_capability(
            path="file://nonexistent.csv"
        )
        
        assert result["success"] is False
        assert "FILE_NOT_FOUND" in result["error"]
        
    async def test_permission_denied(self):
        """测试权限拒绝"""
        result = await self.execute_capability(
            path="file:///etc/passwd"  # 禁止访问的路径
        )
        
        assert result["success"] is False
        assert "PERMISSION_DENIED" in result["error"]
```

### 2.3  fixture 使用

```python
# tests/conftest.py
import pytest
from intentos.agent import TenantManager, CapabilityBinder


@pytest.fixture
def tenant_manager():
    """租户管理器 fixture"""
    manager = TenantManager()
    
    # 创建测试租户
    manager.create_tenant(
        tenant_id="test_tenant",
        name="测试租户",
        plan="pro"
    )
    
    return manager


@pytest.fixture
def capability_binder():
    """能力绑定器 fixture"""
    binder = CapabilityBinder()
    
    # 注册测试能力模板
    binder.register_template(DATA_LOADER_TEMPLATE)
    binder.register_template(ANALYZER_TEMPLATE)
    
    return binder


@pytest.fixture
async def test_app(tenant_manager, capability_binder):
    """测试 App fixture"""
    # 创建测试 App
    app = await create_test_app(
        app_id="test_analyst",
        tenant_id="test_tenant",
    )
    
    yield app
    
    # 清理
    await cleanup_test_app(app)
```

---

## 三、集成测试

### 3.1 集成测试套件

```python
# tests/test_integration.py
import pytest
from intentos.testing import IntegrationTestSuite


class TestDataAnalystIntegration(IntegrationTestSuite):
    """数据分析集成测试"""
    
    async def setup(self):
        """设置测试环境"""
        await self.deploy_app("data_analyst")
        await self.setup_test_data()
        
    async def teardown(self):
        """清理测试环境"""
        await self.cleanup_test_data()
        await self.undeploy_app("data_analyst")
        
    async def test_end_to_end(self):
        """端到端测试"""
        # 用户上传数据
        upload_result = await self.upload_file("test_sales.csv")
        
        # 执行分析
        result = await self.execute(
            app_id="data_analyst",
            intent="分析华东区销售数据",
            parameters={"data_source": upload_result.path}
        )
        
        # 验证结果
        assert result.success
        assert "insights" in result.data
        assert "summary" in result.data
        
        # 验证计费
        assert result.billing.amount > 0
        assert result.billing.currency == "USD"
        
    async def test_multi_user_isolation(self):
        """测试多用户隔离"""
        # 用户 A 执行
        result_a = await self.execute(
            app_id="data_analyst",
            intent="分析数据",
            user_id="user_a",
            parameters={"data_source": "file://user_a_data.csv"}
        )
        
        # 用户 B 执行
        result_b = await self.execute(
            app_id="data_analyst",
            intent="分析数据",
            user_id="user_b",
            parameters={"data_source": "file://user_b_data.csv"}
        )
        
        # 验证数据隔离
        assert result_a.data != result_b.data
```

### 3.2 API 测试

```python
# tests/test_api.py
import pytest
from aiohttp import ClientSession


class TestRestAPI:
    """REST API 测试"""
    
    @pytest.fixture
    async def session(self):
        """HTTP 会话 fixture"""
        async with ClientSession() as session:
            yield session
            
    async def test_execute_intent(self, session):
        """测试执行意图 API"""
        payload = {
            "intent": "分析销售数据",
            "context": {"user_id": "test_user"},
            "app_id": "data_analyst"
        }
        
        async with session.post(
            "http://localhost:8080/v1/execute",
            json=payload
        ) as response:
            assert response.status == 200
            result = await response.json()
            assert result["success"] is True
            
    async def test_wallet_balance(self, session):
        """测试钱包余额 API"""
        async with session.get(
            "http://localhost:8080/v1/wallet/balance?user_id=test_user"
        ) as response:
            assert response.status == 200
            result = await response.json()
            assert "balance" in result
            
    async def test_usage_query(self, session):
        """测试用量查询 API"""
        async with session.get(
            "http://localhost:8080/v1/usage?user_id=test_user&period=2026-03"
        ) as response:
            assert response.status == 200
            result = await response.json()
            assert "usage" in result
```

---

## 四、调试工具

### 4.1 调试器使用

```python
from intentos.debug import Debugger, Breakpoint

# 创建调试器
debugger = Debugger(app_id="data_analyst")

# 设置断点
debugger.add_breakpoint(
    intent_id="data_analysis",
    step_id="analyze",  # 在分析步骤前断点
    condition="data.row_count > 1000"
)

# 设置变量监视
debugger.watch("data")
debugger.watch("analysis_result")
debugger.watch("cost")

# 启动调试会话
async with debugger.session() as session:
    # 执行意图
    result = await session.execute(
        intent="分析销售数据",
        parameters={"data_source": "file://sales.csv"}
    )
    
    # 查看执行轨迹
    trace = session.get_execution_trace()
    print(trace.to_table())
    
    # 查看变量值
    print(f"Data rows: {session.get_variable('data.row_count')}")
    print(f"Analysis: {session.get_variable('analysis_result')}")
    print(f"Cost: ${session.get_variable('cost')}")
```

### 4.2 执行轨迹

```python
# 执行轨迹示例
"""
执行轨迹：data_analysis

┌──────┬─────────────┬──────────┬───────────┬────────┐
│ 步骤 │ 能力        │ 状态     │ 耗时 (ms) │ 结果   │
├──────┼─────────────┼──────────┼───────────┼────────┤
│ 1    │ data_loader │ ✓ 成功   │ 45        │ 1000 行│
│ 2    │ validator   │ ✓ 成功   │ 12        │ 通过   │
│ 3    │ analyzer    │ ✓ 成功   │ 850       │ 5 洞察 │
│ 4    │ reporter    │ ✓ 成功   │ 120       │ 报告   │
└──────┴─────────────┴──────────┴───────────┴────────┘

总耗时：1027ms
总成本：$0.103
"""
```

### 4.3 日志分析

```python
from intentos.logging import LogQuery

# 创建日志查询
query = LogQuery(
    app_id="data_analyst",
    time_range="last_1h",
    level="ERROR"
)

# 执行查询
logs = query.execute()

# 错误分析
error_summary = logs.analyze_errors()
print(f"错误总数：{error_summary.total}")
print(f"错误类型分布：{error_summary.by_type}")
print(f"最常见错误：{error_summary.most_common}")

# 性能日志分析
perf_logs = LogQuery(
    app_id="data_analyst",
    time_range="last_1h",
    type="performance"
).execute()

latency_report = perf_logs.analyze_latency()
print(f"P50: {latency_report.p50}ms")
print(f"P95: {latency_report.p95}ms")
print(f"P99: {latency_report.p99}ms")
```

---

## 五、性能分析

### 5.1 性能分析器

```python
from intentos.profiling import Profiler

# 创建性能分析器
profiler = Profiler(app_id="data_analyst")

# 开始分析
async with profiler.profile() as profile:
    result = await execute_intent(
        intent="分析销售数据",
        parameters={"data_source": "file://large_sales.csv"}
    )

# 输出分析报告
report = profile.generate_report()

# 火焰图
report.save_flame_graph("profile.svg")

# 性能瓶颈分析
bottlenecks = report.find_bottlenecks()
for bottleneck in bottlenecks:
    print(f"瓶颈：{bottleneck.step}")
    print(f"  耗时：{bottleneck.duration_ms}ms")
    print(f"  占比：{bottleneck.percentage}%")
    print(f"  建议：{bottleneck.suggestion}")
```

### 5.2 内存分析

```python
from intentos.profiling import MemoryProfiler

# 创建内存分析器
mem_profiler = MemoryProfiler()

# 开始分析
with mem_profiler.profile() as profile:
    result = await process_large_dataset(data)

# 内存报告
report = profile.get_report()
print(f"峰值内存：{report.peak_memory_mb}MB")
print(f"平均内存：{report.avg_memory_mb}MB")
print(f"内存泄漏：{report.leaks}")

# 内存快照
profile.save_snapshot("memory_snapshot.pkl")
```

---

## 六、故障排查

### 6.1 常见问题

#### 问题 1：能力绑定失败

```
错误：ValueError: 能力 data_loader 需要资源 database，但租户未提供

解决方案:
1. 检查租户资源
   tenant = tenant_manager.get_tenant("acme_corp")
   print(tenant.resources)

2. 添加缺失资源
   tenant_manager.add_resource(
       "acme_corp",
       TenantResource(id="analytics_db", type="database", ...)
   )
```

#### 问题 2：版本不存在

```
错误：ValueError: 版本不存在：data_analyst v2.5.0

解决方案:
1. 检查可用版本
   versions = version_manager.list_versions("data_analyst")

2. 注册新版本
   version_manager.register_version(
       app_id="data_analyst",
       version="2.5.0",
       manifest={...}
   )
```

#### 问题 3：配置未生效

```
问题：用户配置未应用到 App 实例

解决方案:
1. 检查配置是否设置
   config = manager.get_app_config("alice", "data_analyst")

2. 检查 Schema 是否注册
   schema = manager.get_config_schema("data_analyst")

3. 获取有效配置
   effective = manager.get_effective_config(
       user_id="alice",
       app_id="data_analyst"
   )
```

### 6.2 调试命令

```bash
# 查看 App 状态
intentos app status data_analyst

# 查看用户会话
intentos session list --user alice

# 查看执行日志
intentos logs tail data_analyst --lines 100

# 性能分析
intentos profile start data_analyst
intentos profile stop --output profile.json

# 调试模式
intentos debug data_analyst --intent "分析数据"
```

---

## 七、最佳实践

### 7.1 测试最佳实践

```python
# ✅ 正确：测试隔离
class TestIsolation:
    async def setup(self):
        # 每个测试独立环境
        self.tenant = create_test_tenant()
        
    async def teardown(self):
        # 清理测试数据
        await cleanup_test_tenant(self.tenant)

# ❌ 错误：测试依赖
class TestDependency:
    # 测试 B 依赖测试 A 的结果
    async def test_a(self):
        self.data = create_data()
        
    async def test_b(self):
        # 使用 test_a 的数据
        process(self.data)
```

### 7.2 调试最佳实践

```python
# ✅ 正确：结构化日志
logger.info("分析开始", extra={
    "user_id": user_id,
    "data_source": source,
    "row_count": len(data)
})

# ❌ 错误：非结构化日志
logger.info(f"用户{user_id}开始分析数据源{source}共{len(data)}行")
```

---

## 八、参考文档

| 文档 | 说明 |
|------|------|
| [AI Native App 概述](./AI_NATIVE_APP.md) | 核心概念、架构概览 |
| [性能优化](./PERFORMANCE_OPTIMIZATION.md) | 性能分析、优化策略 |
| [应用开发指南](./APP_DEVELOPMENT_GUIDE.md) | 开发流程、最佳实践 |

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Release Candidate
