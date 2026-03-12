# 编译器 API

> 本文档介绍 IntentOS 意图编译器的 API，用于将自然语言意图编译为 LLM 可执行的 Prompt。

---

## 1. IntentCompiler

意图编译器主类：

```python
from intentos import IntentCompiler, IntentRegistry

# 创建编译器
registry = IntentRegistry()
compiler = IntentCompiler(registry)

# 编译意图
prompt = compiler.compile("分析华东区 Q3 销售数据")

# 查看结果
print(f"动作：{prompt.intent.action}")
print(f"目标：{prompt.intent.target}")
print(f"参数：{prompt.intent.parameters}")
```

### 1.1 构造函数

```python
compiler = IntentCompiler(
    registry: Optional[IntentRegistry] = None,  # 意图仓库
)
```

### 1.2 编译方法

```python
# 编译为 Prompt
prompt = compiler.compile(
    text: str,           # 自然语言输入
    context: Context,    # 执行上下文（可选）
) -> CompiledPrompt
```

### 1.3 注册模式

```python
# 注册意图匹配模式
compiler.register_pattern(
    pattern=r"分析.*销售",
    intent_name="sales_analysis",
)

# 匹配时会使用对应的意图模板
```

---

## 2. CompiledPrompt

编译后的 Prompt：

```python
from intentos import CompiledPrompt

# 属性
print(prompt.system_prompt)    # System Prompt
print(prompt.user_prompt)      # User Prompt
print(prompt.intent)           # 原始意图
print(prompt.metadata)         # 元数据

# 转换为 LLM 消息格式
messages = prompt.messages
# [
#   {"role": "system", "content": "..."},
#   {"role": "user", "content": "..."}
# ]

# 转换为字典
data = prompt.to_dict()
```

### 2.1 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `system_prompt` | str | 系统指令 |
| `user_prompt` | str | 用户请求 |
| `intent` | Intent | 原始意图 |
| `metadata` | dict | 元数据 |

---

## 3. PromptTemplate

Prompt 模板：

```python
from intentos import PromptTemplate

# 创建模板
template = PromptTemplate(
    name="analysis_template",
    template="""
# 分析任务

请分析以下数据：

## 数据
{data}

## 要求
- 识别趋势
- 找出异常
- 给出建议
""",
    variables=["data"],
)

# 渲染模板
rendered = template.render(data="销售数据：...")
```

### 3.1 方法

```python
# 渲染模板
result = template.render(**kwargs)

# 添加变量
template.add_variable("new_var", default="default_value")
```

---

## 4. 词法分析器 (Lexer)

将文本转换为 Token 流：

```python
from intentos.parser import Lexer, TokenType

# 创建 Lexer
lexer = Lexer("分析华东区 Q3 销售数据")

# 执行词法分析
tokens = lexer.tokenize()

for token in tokens:
    print(f"{token.type}: {token.value}")
```

### 4.1 Token

```python
from intentos.parser import Token, TokenType

# Token 属性
token.type      # TokenType
token.value     # str
token.position  # int (位置)
token.line      # int (行号)
token.column    # int (列号)
```

### 4.2 TokenType

```python
from intentos.parser import TokenType

TokenType.IDENTIFIER   # 标识符
TokenType.STRING       # 字符串
TokenType.NUMBER       # 数字
TokenType.KEYWORD      # 关键字
TokenType.OPERATOR     # 操作符
TokenType.DELIMITER    # 分隔符
TokenType.EOF          # 结束
```

---

## 5. 语法分析器 (Parser)

将 Token 流转换为 AST：

```python
from intentos.parser import Parser, Lexer

# 创建 Lexer 和 Parser
lexer = Lexer("分析华东区销售")
tokens = lexer.tokenize()
parser = Parser(tokens)

# 执行语法分析
ast = parser.parse()

# 查看 AST
print(ast.to_dict())
```

### 5.1 ASTNode

```python
from intentos.parser import ASTNode

# 属性
node.node_type    # str (节点类型)
node.value        # Any (值)
node.children     # list[ASTNode] (子节点)
node.attributes   # dict (属性)

# 添加子节点
node.add_child(child_node)

# 转换为字典
data = node.to_dict()
```

---

## 6. 语义分析器 (SemanticAnalyzer)

将 AST 转换为结构化意图：

```python
from intentos.parser import Lexer, Parser
from intentos.compiler import SemanticAnalyzer

# 词法和语法分析
lexer = Lexer("分析华东区 Q3 销售")
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()

# 语义分析
analyzer = SemanticAnalyzer()
intent = analyzer.analyze(ast)

# 查看结果
print(f"动作：{intent.action}")
print(f"目标：{intent.target}")
print(f"参数：{intent.parameters}")
```

### 6.1 StructuredIntent

```python
from intentos.compiler import StructuredIntent

# 属性
intent.id              # str (唯一标识)
intent.action          # str (动作)
intent.target          # str (目标)
intent.parameters      # dict (参数)
intent.constraints     # dict (约束)
intent.context         # dict (上下文)
intent.confidence      # float (置信度)

# 转换为字典
data = intent.to_dict()
```

---

## 7. 代码生成器 (CodeGenerator)

将结构化意图转换为 Prompt：

```python
from intentos.compiler import CodeGenerator, StructuredIntent

# 创建生成器
generator = CodeGenerator(registry)

# 生成 Prompt
prompt = generator.generate(intent)

# 查看结果
print(prompt.system_prompt)
print(prompt.user_prompt)
```

### 7.1 GeneratedPrompt

```python
from intentos.compiler import GeneratedPrompt

# 属性
prompt.system_prompt   # str
prompt.user_prompt     # str
prompt.intent          # StructuredIntent
prompt.metadata        # dict

# 转换为 LLM 消息
messages = prompt.messages

# 转换为字典
data = prompt.to_dict()
```

---

## 8. 链接器 (Linker)

将 Prompt 与能力绑定：

```python
from intentos.compiler import Linker

# 创建链接器
linker = Linker(registry)

# 链接
executable = linker.link(prompt)

# 查看结果
print(f"Prompt: {executable['prompt']}")
print(f"能力：{executable['capabilities']}")
print(f"可执行：{executable['executable']}")
```

---

## 9. 便捷函数

### 9.1 compile_intent

```python
from intentos import compile_intent

# 编译意图
prompt = compile_intent(
    source="分析华东区销售数据",
    capabilities={
        "query_sales": {"description": "查询销售数据"},
    },
)
```

### 9.2 create_compiler

```python
from intentos import create_compiler

# 创建编译器
compiler = create_compiler(
    capabilities={
        "query_sales": {"description": "查询销售数据"},
    },
)

# 编译
prompt = compiler.compile("分析销售数据")
```

---

## 10. 完整示例

### 10.1 完整编译流程

```python
from intentos import IntentCompiler, IntentRegistry, Context

# 创建组件
registry = IntentRegistry()
compiler = IntentCompiler(registry)

# 注册能力
from intentos import Capability

async def query_sales(context, region: str):
    return {"region": region, "revenue": 1000000}

registry.register_capability(Capability(
    name="query_sales",
    description="查询销售数据",
    input_schema={"region": {"type": "string"}},
    func=query_sales,
))

# 编译意图
context = Context(user_id="manager_001", permissions=["read_sales"])
prompt = compiler.compile("分析华东区 Q3 销售数据", context)

# 查看编译结果
print(f"System Prompt: {prompt.system_prompt[:200]}...")
print(f"User Prompt: {prompt.user_prompt}")
print(f"意图：{prompt.intent.to_dict()}")

# 执行
from intentos import LLMExecutor
executor = create_executor(provider="openai", api_key="sk-...")
response = await executor.execute(prompt.messages)
print(f"响应：{response.content}")
```

### 10.2 自定义模板

```python
from intentos import PromptTemplate, IntentCompiler

# 创建自定义模板
custom_template = PromptTemplate(
    name="custom_analysis",
    template="""
# 自定义分析指令

你是{role}，需要执行以下分析：

## 目标
{goal}

## 数据
{data}

## 输出要求
- 使用专业术语
- 提供数据支持
- 给出可执行建议
""",
)

# 使用模板
compiler = IntentCompiler()
compiler.templates["analysis"] = custom_template

# 编译时会使用自定义模板
prompt = compiler.compile("分析销售数据")
```

---

## 11. 错误处理

### 11.1 编译错误

```python
from intentos import IntentCompiler

compiler = IntentCompiler()

try:
    prompt = compiler.compile("分析...")
except ValueError as e:
    print(f"编译错误：{e}")
```

### 11.2 验证错误

```python
# 验证 Prompt
errors = prompt.validate()
if errors:
    for error in errors:
        print(f"验证失败：{error}")
```

---

## 12. 总结

编译器 API 分类：

| 组件 | 主要类/函数 |
|------|-----------|
| **主编译器** | IntentCompiler |
| **编译结果** | CompiledPrompt, GeneratedPrompt |
| **模板** | PromptTemplate |
| **词法分析** | Lexer, Token, TokenType |
| **语法分析** | Parser, ASTNode |
| **语义分析** | SemanticAnalyzer, StructuredIntent |
| **代码生成** | CodeGenerator |
| **链接器** | Linker |
| **便捷函数** | compile_intent, create_compiler |

---

**下一篇**: [记忆 API](03-memory-api.md)

**上一篇**: [核心 API](01-core-api.md)
