# IntentOS v16.0 开发者工具文档

**版本**: v16.0  
**发布日期**: 2026-03-27  
**状态**: ✅ 完成

---

## 📋 概述

v16.0 版本专注于开发者工具链建设，提供：

1. **CLI 工具** - 命令行界面，用于图谱管理、验证和调试
2. **Python SDK** - 简洁的 Python API，用于集成 IntentOS 功能

---

## 🛠️ CLI 工具

### 安装

```bash
# 添加执行权限
chmod +x intentos/cli/__main__.py

# 或者使用 Python 模块方式运行
python -m intentos.cli
```

### 可用命令

#### 1. execute - 执行意图

```bash
intentos execute "分析销售数据"
```

#### 2. graph - 意图图谱操作

**初始化图谱**
```bash
# 输出到控制台
intentos graph init

# 保存到文件
intentos graph init -o graph.json
```

**查询图谱**
```bash
# 查看所有节点
intentos graph query -i graph.json

# 关键词搜索
intentos graph query -i graph.json -s "销售"

# 查询指定节点
intentos graph query -i graph.json -n demo_001

# 查看邻居节点
intentos graph query -i graph.json --neighbors demo_001

# 查看统计信息
intentos graph query -i graph.json --stats
```

**查找多跳路径**
```bash
intentos graph path -i graph.json --source node_001 --target node_002
intentos graph path -i graph.json --source node_001 --target node_002 -d 10
```

#### 3. verify - 形式化验证

**验证 DAG**
```bash
# 验证示例 DAG
intentos verify dag

# 验证文件中的 DAG
intentos verify dag -i dag.json
```

#### 4. trace - 执行轨迹

**记录轨迹**
```bash
intentos trace record --intent-id intent_001
intentos trace record --intent-id intent_001 -o trace.json
```

**回放轨迹**
```bash
# 完整回放
intentos trace replay -i trace.json

# 单步回放
intentos trace replay -i trace.json -s

# 回放指定步数
intentos trace replay -i trace.json -s 5
```

#### 5. status - 系统状态

```bash
intentos status
```

输出示例：
```
IntentOS 系统状态
========================================
版本：v16.0.0
时间：2026-03-27 19:00:00

模块状态:
  ✅ 语义 VM
  ✅ 分布式 VM
  ✅ Self-Bootstrap
  ✅ 意图编译器
  ✅ 意图图谱
  ✅ 形式化验证
  ✅ CLI 工具
  ✅ Python SDK

CLI 版本：16.0.0
```

---

## 🐍 Python SDK

### 安装

```bash
# SDK 已包含在 IntentOS 中，直接导入使用
from intentos.sdk import create_client
```

### 快速开始

```python
from intentos.sdk import create_client
from intentos.graph import IntentEdgeType

# 创建客户端
client = create_client()

# 创建意图
intent1 = client.create_intent(
    name="分析销售数据",
    description="分析指定区域和时间的销售数据",
    tags=["销售", "分析"],
)

intent2 = client.create_intent(
    name="生成报表",
    description="生成销售报表",
    tags=["报表"],
)

# 添加关系
client.add_relationship(
    source_id=intent1.node_id,
    target_id=intent2.node_id,
    relationship=IntentEdgeType.TRIGGERS,
)

# 搜索意图
results = client.search_intents(keyword="销售")
print(f"找到 {len(results)} 个意图")

# 获取图谱统计
stats = client.get_graph_stats()
print(f"图谱统计：{stats}")
```

### API 参考

#### IntentOSClient

**初始化**
```python
client = IntentOSClient(host="localhost", port=8080)
# 或
client = create_client()
```

**意图图谱 API**

```python
# 创建意图
intent = client.create_intent(
    name="意图名称",
    description="意图描述",
    intent_type=IntentNodeType.ATOMIC,
    tags=["标签 1", "标签 2"],
    content={"key": "value"},
)

# 添加关系
edge = client.add_relationship(
    source_id="source_node_id",
    target_id="target_node_id",
    relationship=IntentEdgeType.TRIGGERS,
    weight=1.0,
)

# 搜索意图
results = client.search_intents(keyword="关键词")
results = client.search_intents(tag="标签")
results = client.search_intents(node_id="node_001")

# 查找多跳路径
paths = client.find_path("source_id", "target_id", max_depth=5)

# 推荐意图
recommendations = client.recommend_intents("node_id", num=5)

# 获取统计
stats = client.get_graph_stats()
```

**验证 API**

```python
# 验证 DAG
from intentos.verification import create_dag_node

dag_nodes = [
    create_dag_node("task_1", "query", dependencies=[]),
    create_dag_node("task_2", "analyze", dependencies=["task_1"]),
    create_dag_node("task_3", "visualize", dependencies=["task_2"]),
]

result = client.validate_dag(dag_nodes)
print(f"DAG 有效：{result['is_valid']}")
print(f"错误：{result['errors']}")
print(f"警告：{result['warnings']}")

# 注册能力
signature = client.register_capability(
    name="query_sales",
    input_schema={
        "type": "object",
        "required": ["region", "quarter"],
        "properties": {
            "region": {"type": "string"},
            "quarter": {"type": "string"},
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "data": {"type": "array"},
            "total": {"type": "number"},
        }
    },
    description="查询销售数据",
)

# 验证能力调用
result = client.validate_capability_call(
    "query_sales",
    {"region": "east", "quarter": "Q3"},
)
print(f"调用有效：{result['is_valid']}")
```

**轨迹 API**

```python
from intentos.verification import EventType

# 创建轨迹
trace = client.create_trace("intent_001")

# 添加事件
trace.add_event(EventType.TASK_START, "task_001", {"name": "分析数据"})
trace.add_event(EventType.CAPABILITY_CALL, "task_001", {"capability": "query_db"})
trace.add_event(EventType.CAPABILITY_RETURN, "task_001", {"result": "success"})
trace.add_event(EventType.TASK_END, "task_001", {"status": "completed"})

# 回放轨迹
events = client.replay_trace(trace)
for event in events:
    print(f"{event['event_type']} @ {event['task_id']}")

# 单步回放
events = client.replay_trace(trace, step=2)
```

**导出/导入**

```python
# 导出图谱
client.export_graph("graph.json")

# 导入图谱
client.import_graph("graph.json")

# 导出轨迹
client.export_trace(trace, "trace.json")

# 导入轨迹
trace = client.import_trace("trace.json")
```

---

## 📊 使用场景

### 场景 1: 开发和调试意图图谱

```bash
# 1. 初始化示例图谱
intentos graph init -o demo_graph.json

# 2. 查看图谱内容
intentos graph query -i demo_graph.json

# 3. 搜索特定意图
intentos graph query -i demo_graph.json -s "销售"

# 4. 查找意图间关系
intentos graph path -i demo_graph.json --source demo_001 --target demo_002
```

### 场景 2: 验证任务 DAG

```python
from intentos.sdk import create_client
from intentos.verification import create_dag_node

client = create_client()

# 定义任务 DAG
dag_nodes = [
    create_dag_node("extract", "extract_data", dependencies=[]),
    create_dag_node("clean", "clean_data", dependencies=["extract"]),
    create_dag_node("analyze", "analyze_data", dependencies=["clean"]),
    create_dag_node("report", "generate_report", dependencies=["analyze"]),
]

# 验证
result = client.validate_dag(dag_nodes)
if result["is_valid"]:
    print("✅ DAG 有效，可以执行")
else:
    print("❌ DAG 无效:")
    for error in result["errors"]:
        print(f"  - {error}")
```

### 场景 3: 执行轨迹分析

```bash
# 1. 记录执行轨迹
intentos trace record --intent-id analysis_001 -o trace.json

# 2. 回放分析
intentos trace replay -i trace.json

# 3. 单步调试
intentos trace replay -i trace.json -s
```

---

## 🧪 测试

运行 CLI 和 SDK 测试：

```bash
PYTHONPATH=. python -m pytest tests/unit/test_cli_and_sdk.py -v
```

---

## 📝 总结

v16.0 开发者工具提供了完整的命令行和 Python API，使开发者能够：

- ✅ 通过 CLI 快速操作意图图谱
- ✅ 验证 DAG 和 capability 调用
- ✅ 记录和回放执行轨迹
- ✅ 通过 Python SDK 集成 IntentOS 功能
- ✅ 导出/导入图谱和轨迹数据

这些工具显著提升了开发效率和调试能力。

---

**文档版本**: 16.0.0  
**最后更新**: 2026-03-27  
**维护者**: IntentOS Team
