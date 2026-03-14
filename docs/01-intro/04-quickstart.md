# 快速开始

> 5 分钟上手 IntentOS

---

## 1. 安装

### 1.1 基础安装

```bash
# 克隆仓库
git clone https://github.com/jeffery9/IntentOS.git
cd intentos

# 安装依赖
pip install pyyaml
```

### 1.2 完整安装（可选）

```bash
# 安装所有 LLM 后端支持
pip install "intentos[all]"

# 或单独安装
pip install "intentos[openai]"    # OpenAI
pip install "intentos[anthropic]" # Anthropic
pip install "intentos[ollama]"    # Ollama
```

---

## 2. 第一个意图编译

### 2.1 创建编译器

```python
from intentos import IntentCompiler

compiler = IntentCompiler()
```

### 2.2 编译意图

```python
# 编译自然语言
prompt = compiler.compile("分析华东区 Q3 销售数据")

# 查看结果
print(f"动作：{prompt.intent.action}")
print(f"目标：{prompt.intent.target}")
print(f"参数：{prompt.intent.parameters}")
```

### 2.3 获取 Prompt

```python
# System Prompt
print(prompt.system_prompt)

# User Prompt
print(prompt.user_prompt)

# 转换为 LLM 消息格式
messages = prompt.messages
# [
#   {"role": "system", "content": "..."},
#   {"role": "user", "content": "..."}
# ]
```

---

## 3. 执行意图

### 3.1 使用 Mock 后端

```python
import asyncio
from intentos import IntentOS

async def main():
    os = IntentOS()
    os.initialize()
    
    # 执行意图
    result = await os.execute("分析华东区 Q3 销售数据")
    print(result)

asyncio.run(main())
```

### 3.2 使用真实 LLM

```python
import asyncio
import os
from intentos import IntentOS

async def main():
    os = IntentOS()
    os.initialize()
    
    # 配置 OpenAI
    os.interface.engine.llm_executor = create_executor(
        provider="openai",
        api_key=os.environ.get("OPENAI_API_KEY"),
        model="gpt-4o",
    )
    
    # 执行
    result = await os.execute("分析华东区 Q3 销售数据")
    print(result)

asyncio.run(main())
```

---

## 4. 注册能力

### 4.1 定义能力

```python
from intentos import Capability, Context

def query_sales(context: Context, region: str, period: str) -> dict:
    """查询销售数据"""
    # 实际逻辑：调用 API 或数据库
    return {
        "region": region,
        "period": period,
        "data": [100, 200, 150],
    }

capability = Capability(
    name="query_sales",
    description="查询销售数据",
    input_schema={"region": "string", "period": "string"},
    output_schema={"data": "array"},
    func=query_sales,
)
```

### 4.2 注册能力

```python
from intentos import IntentRegistry

registry = IntentRegistry()
registry.register_capability(capability)
```

### 4.3 使用能力

```python
# 能力会自动被意图编译器使用
prompt = compiler.compile("查询华东区 Q3 销售")

# 编译后的 Prompt 会包含能力信息
print(prompt.system_prompt)
```

---

## 5. 记忆管理

### 5.1 创建记忆管理器

```python
from intentos import create_memory_manager

manager = create_memory_manager(
    short_term_max=1000,
    long_term_enabled=True,
    sync_enabled=False,
)
await manager.initialize()
```

### 5.2 设置记忆

```python
# 短期记忆
await manager.set_short_term(
    key="user:123:preference",
    value={"theme": "dark", "language": "zh-CN"},
    tags=["user", "preference"],
    ttl_seconds=3600,
)

# 长期记忆
await manager.set_long_term(
    key="knowledge:fact:1",
    value={"fact": "地球是圆的"},
    tags=["knowledge"],
    ttl_seconds=86400 * 30,  # 30 天
)
```

### 5.3 检索记忆

```python
# 获取记忆
entry = await manager.get("user:123:preference")
print(entry.value)

# 按标签检索
entries = await manager.get_by_tag("user")
for e in entries:
    print(e.key, e.value)

# 搜索
results = await manager.search("地球")
for r in results:
    print(r.key, r.value)
```

---

## 6. 运行示例

### 6.1 编译器演示

```bash
python intentos/compiler_v2.py
```

### 6.2 LLM 后端演示

```bash
python intentos/examples/demo_llm_backends.py
```

### 6.3 并行执行演示

```bash
python intentos/examples/demo_parallel.py
```

### 6.4 记忆管理演示

```bash
python intentos/examples/demo_memory.py
```

---

## 7. 运行测试

```bash
# 运行所有测试
python -m pytest intentos/examples/ -v

# 运行特定测试
python -m pytest intentos/examples/test_compiler.py -v
```

---

## 8. 下一步

- [了解什么是 AI 原生软件](01-what-is-ai-native.md)
- [学习3 Layer / 7 Level架构](../02-architecture/01-three-layer-model.md)
- [构建第一个 App](../07-guides/01-build-first-app.md)

---

**上一篇**: [IntentOS 概述](03-intentos-overview.md)
