# 意图编译器架构

> IntentOS 的核心是意图编译器，将自然语言意图编译为 LLM 可执行的 Prompt。

---

## 1. 编译器概览

### 1.1 核心洞察

IntentOS 的本质是一个**意图编译器**：

| 传统编译器 | IntentOS 意图编译器 |
|-----------|-------------------|
| 源代码 (Source Code) | **自然语言意图** |
| 机器码 (Machine Code) | **Prompt** |
| CPU | **LLM** |
| 库函数 | **能力 (Capability)** |
| 内存/存储 | **记忆 (Memory)** |
| 链接器 | **Prompt 链接器** |

### 1.2 编译流程

```
自然语言 → Lexer → Tokens → Parser → AST → SemanticAnalyzer → 
StructuredIntent → CodeGenerator → Prompt → Linker → Executable → LLM
```

### 1.3 组件说明

| 组件 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **Lexer** | 词法分析 | 文本 | Token 流 |
| **Parser** | 语法分析 | Token 流 | AST |
| **SemanticAnalyzer** | 语义分析 | AST | 结构化意图 |
| **CodeGenerator** | 代码生成 | 结构化意图 | Prompt |
| **Linker** | 链接 | Prompt + 能力 | 可执行 Prompt |

---

## 2. 词法分析 (Lexer)

### 2.1 职责

将自然语言文本转换为 Token 流：

```
输入："分析华东区 Q3 销售数据"
输出：[分析 (KEYWORD), 华东 (IDENTIFIER), 区 (IDENTIFIER), 
      Q3 (IDENTIFIER), 销售 (IDENTIFIER), 数据 (IDENTIFIER)]
```

### 2.2 Token 类型

```python
class TokenType(Enum):
    IDENTIFIER = "identifier"     # 标识符
    STRING = "string"             # 字符串
    NUMBER = "number"             # 数字
    KEYWORD = "keyword"           # 关键字
    OPERATOR = "operator"         # 操作符
    DELIMITER = "delimiter"       # 分隔符
    EOF = "eof"                   # 结束
```

### 2.3 实现示例

```python
class Lexer:
    KEYWORDS = {
        "分析", "查询", "生成", "创建", "对比", "比较", 
        "总结", "报告", "显示", "列出", "计算", "统计",
    }
    
    def tokenize(self, text: str) -> list[Token]:
        tokens = []
        
        while self.pos < len(text):
            self._skip_whitespace()
            
            # 匹配数字
            if text[self.pos].isdigit():
                tokens.append(self._read_number())
            
            # 匹配关键字
            elif self._match_keyword():
                tokens.append(self._read_keyword())
            
            # 默认：标识符
            else:
                tokens.append(self._read_identifier())
        
        tokens.append(Token(TokenType.EOF, "", self.pos))
        return tokens
```

---

## 3. 语法分析 (Parser)

### 3.1 职责

将 Token 流转换为抽象语法树 (AST)：

```
输入：[分析 (KEYWORD), 华东 (IDENTIFIER), 销售 (IDENTIFIER)]
输出：
Intent
├── Action: 分析
└── Target: 华东 销售
```

### 3.2 AST 结构

```python
@dataclass
class ASTNode:
    node_type: str
    value: Any = None
    children: list[ASTNode] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, node: ASTNode) -> None:
        self.children.append(node)
```

### 3.3 实现示例

```python
class Parser:
    def parse(self, tokens: list[Token]) -> ASTNode:
        self.tokens = tokens
        self.pos = 0
        return self._parse_intent()
    
    def _parse_intent(self) -> ASTNode:
        root = ASTNode(node_type="Intent")
        
        # 解析动作
        action = self._parse_action()
        if action:
            root.add_child(action)
        
        # 解析目标
        target = self._parse_target()
        if target:
            root.add_child(target)
        
        # 解析修饰词
        modifiers = self._parse_modifiers()
        for mod in modifiers:
            root.add_child(mod)
        
        return root
```

---

## 4. 语义分析 (SemanticAnalyzer)

### 4.1 职责

将 AST 转换为结构化意图：

```python
# 输入 AST
Intent
├── Action: 分析
└── Target: 华东 销售

# 输出 StructuredIntent
{
    "action": "analyze",
    "target": "sales_data",
    "parameters": {
        "region": "华东",
    },
    "output_format": "analysis_report"
}
```

### 4.2 动作映射

```python
ACTION_MAP = {
    "分析": "analyze",
    "查询": "query",
    "生成": "generate",
    "创建": "create",
    "对比": "compare",
    "总结": "summarize",
    "报告": "report",
}
```

### 4.3 实现示例

```python
class SemanticAnalyzer:
    def analyze(self, ast: ASTNode) -> StructuredIntent:
        intent = StructuredIntent()
        
        for child in ast.children:
            if child.node_type == "Action":
                intent.action = self._resolve_action(child.value)
            elif child.node_type == "Target":
                intent.target = child.value
            elif child.node_type.endswith("Modifier"):
                self._apply_modifier(intent, child)
        
        # 推断参数
        self._infer_parameters(intent)
        
        return intent
```

---

## 5. 代码生成 (CodeGenerator)

### 5.1 职责

将结构化意图转换为 Prompt：

```python
# 输入
StructuredIntent(
    action="analyze",
    target="sales_data",
    parameters={"region": "华东"}
)

# 输出
system_prompt = """
# AI 助手指令

## 意图信息
- 动作：analyze
- 目标：sales_data
- 参数：region=华东

## 可用能力
- query_sales: 查询销售数据
- analyze_trends: 分析趋势
"""

user_prompt = "请分析华东区销售数据"
```

### 5.2 模板系统

```python
TEMPLATES = {
    "atomic": """
# 任务执行指令

你是一个 AI 原生助手，需要执行用户的意图。

## 意图信息
- 名称：{intent_name}
- 类型：原子任务
- 目标：{goal}

## 可用能力
{capabilities}

## 上下文信息
- 用户：{user_id}
- 角色：{user_role}
""",

    "composite": """
# 复合任务执行计划

## 执行步骤
{steps}

请按顺序执行上述步骤。
""",
}
```

### 5.3 实现示例

```python
class CodeGenerator:
    def generate(self, intent: StructuredIntent) -> GeneratedPrompt:
        system_prompt = self._generate_system_prompt(intent)
        user_prompt = self._generate_user_prompt(intent)
        
        return GeneratedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            intent=intent,
        )
```

---

## 6. 链接器 (Linker)

### 6.1 职责

将 Prompt 与能力绑定，生成可执行 Prompt：

```python
# 输入
{
    "prompt": {...},
    "capabilities": ["query_sales", "analyze_trends"]
}

# 输出
{
    "prompt": {...},
    "bound_capabilities": [
        {"name": "query_sales", "endpoint": "..."},
        {"name": "analyze_trends", "endpoint": "..."}
    ],
    "executable": True
}
```

### 6.2 能力绑定

```python
class Linker:
    def link(self, prompt: GeneratedPrompt) -> dict:
        return {
            "prompt": prompt.to_dict(),
            "capabilities": self._get_relevant_capabilities(prompt.intent),
            "executable": True,
        }
    
    def _get_relevant_capabilities(self, intent) -> list:
        relevant = []
        
        # 根据动作推断需要的能力
        action_to_cap = {
            "analyze": ["data_query", "statistics"],
            "query": ["data_query"],
            "generate": ["template_render"],
        }
        
        for cap in action_to_cap.get(intent.action, []):
            if cap in self.capabilities:
                relevant.append(cap)
        
        return relevant
```

---

## 7. 完整示例

### 7.1 编译流程

```python
from intentos import IntentCompiler

# 创建编译器
compiler = IntentCompiler()

# 注册能力
compiler.register_capability(
    "query_sales",
    query_sales_func,
    "查询销售数据"
)

# 编译
prompt = compiler.compile("分析华东区 Q3 销售数据")

# 查看结果
print(f"动作：{prompt.intent.action}")
print(f"目标：{prompt.intent.target}")
print(f"参数：{prompt.intent.parameters}")

# 获取 Prompt
print(prompt.system_prompt)
print(prompt.user_prompt)
```

### 7.2 编译并执行

```python
# 编译并执行
result = await compiler.execute("分析华东区 Q3 销售数据")

# 结果包含
{
    "prompt": {...},
    "results": {
        "query_sales": {...},
        "analyze_trends": {...}
    }
}
```

---

## 8. 总结

意图编译器的核心价值：

1. **结构化**: 将模糊的自然语言转换为结构化意图
2. **可验证**: 意图可验证、可测试
3. **可复用**: 意图模板可复用
4. **可执行**: 编译为 LLM 可执行的 Prompt

---

**下一篇**: [PEF 规范](02-pef-specification.md)

**上一篇**: [分布式架构](../02-architecture/04-distributed-architecture.md)
