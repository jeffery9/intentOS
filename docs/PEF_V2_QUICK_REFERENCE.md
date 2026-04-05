# PEF v2.0 快速参考

## 导入

```python
from intentos.compiler import (
    PEF,                    # PEF v2.0 主类
    IntentDeclaration,      # 意图声明
    ContextBinding,         # 上下文绑定
    CapabilityBinding,      # 能力绑定
    WorkflowDefinition,     # 工作流定义
    WorkflowStep,           # 工作流步骤
    IntentCompilerV2,       # 编译器 v2.0
    compile_intent,         # 快速编译函数
    create_pef,             # 快速创建函数
    load_pef,               # 加载 PEF 文件
    save_pef,               # 保存 PEF 文件
)
```

## 快速创建

```python
# 方法 1: 使用便捷函数
pef = compile_intent(
    goal="分析销售数据",
    user_id="sales_manager",
    capabilities=["query_sales", "analyze"],
)

# 方法 2: 使用 create_pef
pef = create_pef(
    goal="分析销售数据",
    user_id="sales_manager",
    capabilities=["query_sales"],
    context={"region": "华东"},
)

# 方法 3: 使用类构造
pef = PEF(
    intent=IntentDeclaration(goal="分析销售数据"),
    context=ContextBinding(user_id="sales_manager"),
    capabilities=[CapabilityBinding(name="query_sales")],
)
```

## 序列化

```python
# 导出
yaml_str = pef.to_yaml()
json_str = pef.to_json(indent=2)
data_dict = pef.to_dict()

# 导入
pef = PEF.from_yaml(yaml_str)
pef = PEF.from_json(json_str)
pef = PEF.from_dict(data_dict)
```

## 文件 I/O

```python
# 保存
save_pef(pef, "output.pef.yaml")  # YAML
save_pef(pef, "output.pef.json")  # JSON

# 加载
pef = load_pef("input.pef.yaml")
pef = PEF.from_file("input.pef.json")  # 自动检测格式
```

## 验证

```python
errors = pef.validate()
if errors:
    for err in errors:
        print(f"错误: {err}")
else:
    print("✓ 验证通过")
```

## 编译器 v2.0

```python
compiler = IntentCompilerV2()

# 编译
pef = compiler.compile(
    goal="分析销售数据",
    user_id="sales_manager",
    capabilities=["query_sales"],
    context={"region": "华东"},
)

# 从文件编译
pef = compiler.compile_from_file("input.pef.yaml")

# 从 stdin 编译
pef = compiler.compile_from_stdin()

# 保存
compiler.save_pef(pef, "output.pef.yaml")

# 统计
stats = compiler.get_stats()
```

## v1.0 兼容

```python
from intentos.agent.compiler import PEF as PEFv1

# v1 → v2
v2_pef = PEF.from_v1(v1_pef)
# 或
v2_pef = v1_pef.to_v2()

# v2 → v1
v1_pef = v2_pef.to_v1()
```

## 工作流

```python
pef = PEF(
    intent=IntentDeclaration(goal="数据分析"),
    context=ContextBinding(user_id="analyst"),
    capabilities=[
        CapabilityBinding(name="query"),
        CapabilityBinding(name="analyze"),
    ],
    workflow=WorkflowDefinition(
        steps=[
            WorkflowStep(
                id="step1",
                name="查询数据",
                capability="query",
                output_var="data",
            ),
            WorkflowStep(
                id="step2",
                name="分析数据",
                capability="analyze",
                depends_on=["step1"],
                output_var="result",
            ),
        ]
    ),
)
```

## 常用方法

```python
# 获取能力名称列表
capability_names = pef.get_capability_names()

# 获取缓存键
cache_key = pef.cache_key

# 验证 PEF
errors = pef.validate()
```

## PEF 结构

```
PEF
├── Header
│   ├── version: "2.0"
│   ├── id: "pef_..."
│   └── compiled_at: "2026-04-05T..."
├── Intent
│   ├── goal: "分析销售数据"
│   ├── description: "详细说明"
│   └── output_format: "json"
├── Context
│   ├── user_id: "sales_manager"
│   ├── session_id: "sess_..."
│   ├── business_context: {...}
│   └── technical_context: {...}
├── Capabilities
│   └── [CapabilityBinding, ...]
├── Constraints (可选)
│   ├── resource_limits: {...}
│   └── execution: {...}
├── Workflow (可选)
│   ├── steps: [WorkflowStep, ...]
│   └── on_error: [...]
└── Metadata (可选)
    ├── tags: ["sales", "analysis"]
    ├── cache_key: "..."
    └── {...}
```

## 命令行（未来支持）

```bash
# 编译意图
intentos compile "分析销售数据" > output.pef.yaml

# 从文件执行
intentos execute input.pef.yaml

# 管道操作
echo "分析销售数据" | intentos compile > output.pef.yaml
cat input.pef.yaml | intentos execute

# 验证 PEF
intentos validate input.pef.yaml
```

## 测试

```bash
# 运行 PEF 测试
pytest tests/unit/test_pef_format.py -v

# 运行编译器测试
pytest tests/unit/test_compiler*.py -v

# 运行所有测试
pytest tests/unit/ -v
```

## 文档

- [PEF 格式规范](docs/PEF_FORMAT_SPEC.md)
- [实现总结](docs/PEF_V2_IMPLEMENTATION.md)
- [改进提案](docs/IMPROVEMENT_PROPOSAL.md)
- [使用示例](examples/pef_v2_examples.py)
- [示例 PEF](examples/sales_analysis.pef.yaml)
