"""
IntentOS 核心编译器

核心理念:
- 意图 (Intent) = 源代码 (Source Code)
- Prompt = 机器码 (Machine Code)
- LLM = CPU (执行单元)
- 能力 (Capability) = 库函数 (Library Function)
- 记忆 (Memory) = 存储 (Storage)

编译流程:
1. 词法分析：自然语言 → Token 流
2. 语法分析：Token 流 → 抽象语法树 (AST)
3. 语义分析：AST → 结构化意图
4. 代码生成：结构化意图 → Prompt
5. 链接：Prompt + 能力绑定 → 可执行 Prompt
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, AsyncIterator, Iterator
from enum import Enum
import asyncio
import time
import uuid
import json
import hashlib


# =============================================================================
# 编译中间表示 (Intermediate Representation)
# =============================================================================

class TokenType(Enum):
    """Token 类型"""
    IDENTIFIER = "identifier"     # 标识符
    STRING = "string"             # 字符串
    NUMBER = "number"             # 数字
    KEYWORD = "keyword"           # 关键字
    OPERATOR = "operator"         # 操作符
    DELIMITER = "delimiter"       # 分隔符
    EOF = "eof"                   # 结束


@dataclass
class Token:
    """词法 Token"""
    type: TokenType
    value: str
    position: int
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type.value}, {self.value!r})"


@dataclass
class ASTNode:
    """抽象语法树节点"""
    node_type: str
    value: Any = None
    children: list[ASTNode] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, node: ASTNode) -> None:
        self.children.append(node)
    
    def to_dict(self) -> dict:
        return {
            "type": self.node_type,
            "value": self.value,
            "children": [c.to_dict() for c in self.children],
            "attributes": self.attributes,
        }


# =============================================================================
# 词法分析器 (Lexer)
# =============================================================================

class Lexer:
    """
    词法分析器
    将自然语言文本转换为 Token 流
    """
    
    KEYWORDS = {
        "分析", "查询", "生成", "创建", "对比", "比较", "总结", "报告",
        "显示", "列出", "计算", "统计", "过滤", "排序", "分组",
        "什么", "哪些", "如何", "为什么", "多少", "哪里",
        "和", "或", "与", "非", "的", "在", "从", "到", "为",
    }
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
    
    def tokenize(self) -> list[Token]:
        """执行词法分析"""
        tokens = []
        
        while self.pos < len(self.text):
            self._skip_whitespace()
            if self.pos >= len(self.text):
                break
            
            token = self._next_token()
            if token:
                tokens.append(token)
        
        tokens.append(Token(TokenType.EOF, "", self.pos, self.line, self.column))
        return tokens
    
    def _skip_whitespace(self) -> None:
        """跳过空白字符"""
        while self.pos < len(self.text) and self.text[self.pos] in ' \t\n\r':
            if self.text[self.pos] == '\n':
                self.line += 1
                self.column = 1
            self.pos += 1
            self.column += 1
    
    def _next_token(self) -> Optional[Token]:
        """获取下一个 Token"""
        start_pos = self.pos
        start_line = self.line
        start_column = self.column
        
        # 尝试匹配数字
        if self.text[self.pos].isdigit():
            return self._read_number(start_pos, start_line, start_column)
        
        # 尝试匹配引号字符串
        if self.text[self.pos] in '"\'':
            return self._read_string(start_pos, start_line, start_column)
        
        # 尝试匹配中文词汇（2-4 字）
        if '\u4e00' <= self.text[self.pos] <= '\u9fff':
            return self._read_chinese_word(start_pos, start_line, start_column)
        
        # 默认：单字符
        char = self.text[self.pos]
        self.pos += 1
        self.column += 1
        
        if char in '，。？！；：、':
            return Token(TokenType.DELIMITER, char, start_pos, start_line, start_column)
        
        return Token(TokenType.IDENTIFIER, char, start_pos, start_line, start_column)
    
    def _read_number(self, start_pos: int, start_line: int, start_column: int) -> Token:
        """读取数字"""
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] in '.'):
            self.pos += 1
            self.column += 1
        
        value = self.text[start:self.pos]
        return Token(TokenType.NUMBER, value, start_pos, start_line, start_column)
    
    def _read_string(self, start_pos: int, start_line: int, start_column: int) -> Token:
        """读取字符串"""
        quote = self.text[self.pos]
        self.pos += 1
        self.column += 1
        
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] != quote:
            self.pos += 1
            self.column += 1
        
        value = self.text[start:self.pos]
        self.pos += 1  # 跳过结束引号
        self.column += 1
        
        return Token(TokenType.STRING, value, start_pos, start_line, start_column)
    
    def _read_chinese_word(self, start_pos: int, start_line: int, start_column: int) -> Token:
        """读取中文词汇"""
        start = self.pos
        
        # 尝试匹配 2-4 字词汇
        max_len = min(4, len(self.text) - self.pos)
        for length in range(max_len, 0, -1):
            word = self.text[start:start + length]
            if word in self.KEYWORDS:
                for _ in range(length):
                    self.pos += 1
                    self.column += 1
                return Token(TokenType.KEYWORD, word, start_pos, start_line, start_column)
        
        # 默认：单字
        self.pos += 1
        self.column += 1
        return Token(TokenType.IDENTIFIER, self.text[start:self.pos], start_pos, start_line, start_column)


# =============================================================================
# 语法分析器 (Parser)
# =============================================================================

class Parser:
    """
    语法分析器
    将 Token 流转换为抽象语法树 (AST)
    """
    
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self) -> ASTNode:
        """执行语法分析"""
        return self._parse_intent()
    
    def _current_token(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]
    
    def _consume(self, expected_type: Optional[TokenType] = None) -> Token:
        token = self._current_token()
        if expected_type and token.type != expected_type:
            raise SyntaxError(f"期望 {expected_type}, 得到 {token.type}")
        self.pos += 1
        return token
    
    def _parse_intent(self) -> ASTNode:
        """解析意图"""
        root = ASTNode(node_type="Intent")
        
        # 查找动作关键词
        action = self._parse_action()
        if action:
            root.add_child(action)
        
        # 查找目标对象
        target = self._parse_target()
        if target:
            root.add_child(target)
        
        # 查找修饰词（时间、地点、条件等）
        modifiers = self._parse_modifiers()
        for mod in modifiers:
            root.add_child(mod)
        
        return root
    
    def _parse_action(self) -> Optional[ASTNode]:
        """解析动作"""
        if self._current_token().type == TokenType.KEYWORD:
            token = self._consume()
            return ASTNode(node_type="Action", value=token.value)
        return None
    
    def _parse_target(self) -> Optional[ASTNode]:
        """解析目标对象"""
        parts = []
        
        while self._current_token().type in [TokenType.IDENTIFIER, TokenType.STRING]:
            token = self._consume()
            parts.append(token.value)
        
        if parts:
            return ASTNode(node_type="Target", value=" ".join(parts))
        return None
    
    def _parse_modifiers(self) -> list[ASTNode]:
        """解析修饰词"""
        modifiers = []
        
        while self._current_token().type != TokenType.EOF:
            token = self._current_token()
            
            # 时间修饰
            if token.value in ["今天", "昨天", "上周", "本月", "季度", "年"]:
                self._consume()
                modifiers.append(ASTNode(node_type="TimeModifier", value=token.value))
            
            # 地点/区域修饰
            elif token.value in ["华东", "华南", "华北", "西部", "北京", "上海"]:
                self._consume()
                modifiers.append(ASTNode(node_type="LocationModifier", value=token.value))
            
            # 数值修饰
            elif token.type == TokenType.NUMBER:
                num_token = self._consume()
                unit = ""
                if self._current_token().type == TokenType.IDENTIFIER:
                    unit = self._consume().value
                modifiers.append(ASTNode(
                    node_type="NumberModifier",
                    value=num_token.value,
                    attributes={"unit": unit}
                ))
            
            # 条件修饰
            elif token.value in ["大于", "小于", "等于", "超过"]:
                op = self._consume().value
                if self._current_token().type == TokenType.NUMBER:
                    val = self._consume().value
                    modifiers.append(ASTNode(
                        node_type="ConditionModifier",
                        attributes={"operator": op, "value": val}
                    ))
            
            else:
                self._consume()  # 跳过未知 token
            
            if self._current_token().type == TokenType.DELIMITER:
                self._consume()
        
        return modifiers


# =============================================================================
# 语义分析器 (Semantic Analyzer)
# =============================================================================

@dataclass
class StructuredIntent:
    """结构化意图"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""
    target: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action": self.action,
            "target": self.target,
            "parameters": self.parameters,
            "constraints": self.constraints,
            "context": self.context,
            "confidence": self.confidence,
        }


class SemanticAnalyzer:
    """
    语义分析器
    将 AST 转换为结构化意图
    """
    
    # 动作映射：自然语言 → 能力名称
    ACTION_MAP = {
        "分析": "analyze",
        "查询": "query",
        "生成": "generate",
        "创建": "create",
        "对比": "compare",
        "比较": "compare",
        "总结": "summarize",
        "报告": "report",
        "显示": "display",
        "列出": "list",
        "计算": "calculate",
        "统计": "statistics",
    }
    
    def analyze(self, ast: ASTNode) -> StructuredIntent:
        """执行语义分析"""
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
    
    def _resolve_action(self, action: str) -> str:
        """解析动作"""
        return self.ACTION_MAP.get(action, action)
    
    def _apply_modifier(self, intent: StructuredIntent, modifier: ASTNode) -> None:
        """应用修饰词"""
        if modifier.node_type == "TimeModifier":
            intent.parameters["time"] = modifier.value
        elif modifier.node_type == "LocationModifier":
            intent.parameters["location"] = modifier.value
        elif modifier.node_type == "NumberModifier":
            intent.parameters["number"] = modifier.value
            if modifier.attributes.get("unit"):
                intent.parameters["unit"] = modifier.attributes["unit"]
        elif modifier.node_type == "ConditionModifier":
            intent.constraints["condition"] = modifier.attributes
    
    def _infer_parameters(self, intent: StructuredIntent) -> None:
        """推断参数"""
        # 根据目标推断
        if "销售" in intent.target:
            intent.parameters["domain"] = "sales"
        elif "客户" in intent.target:
            intent.parameters["domain"] = "customer"
        elif "产品" in intent.target:
            intent.parameters["domain"] = "product"
        
        # 根据动作推断输出格式
        if intent.action == "analyze":
            intent.parameters["output_format"] = "analysis_report"
        elif intent.action == "generate":
            intent.parameters["output_format"] = "document"


# =============================================================================
# 代码生成器 (Code Generator)
# =============================================================================

@dataclass
class GeneratedPrompt:
    """生成的 Prompt"""
    system_prompt: str
    user_prompt: str
    intent: StructuredIntent
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def messages(self) -> list[dict[str, str]]:
        """转换为 LLM 消息格式"""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]
    
    def to_dict(self) -> dict:
        return {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "intent": self.intent.to_dict(),
            "metadata": self.metadata,
        }


class CodeGenerator:
    """
    代码生成器
    将结构化意图转换为 Prompt
    """
    
    def __init__(self, capabilities: Optional[dict[str, Any]] = None):
        self.capabilities = capabilities or {}
    
    def generate(self, intent: StructuredIntent) -> GeneratedPrompt:
        """生成 Prompt"""
        system_prompt = self._generate_system_prompt(intent)
        user_prompt = self._generate_user_prompt(intent)
        
        return GeneratedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            intent=intent,
            metadata={
                "generated_at": time.time(),
                "intent_id": intent.id,
            },
        )
    
    def _generate_system_prompt(self, intent: StructuredIntent) -> str:
        """生成 System Prompt"""
        capabilities_info = self._format_capabilities()
        
        return f"""# AI 助手指令

你是一个专业的 AI 助手，需要执行用户的意图。

## 意图信息
- **动作**: {intent.action}
- **目标**: {intent.target}
- **参数**: {intent.parameters}
- **约束**: {intent.constraints}

## 可用能力
{capabilities_info}

## 输出要求
- 准确理解用户意图
- 调用合适的能力
- 返回结构化的结果
"""
    
    def _generate_user_prompt(self, intent: StructuredIntent) -> str:
        """生成 User Prompt"""
        return f"请{intent.action}{intent.target}"
    
    def _format_capabilities(self) -> str:
        """格式化能力列表"""
        if not self.capabilities:
            return "（无可用能力）"
        
        lines = []
        for name, cap in self.capabilities.items():
            lines.append(f"- **{name}**: {cap.get('description', '')}")
        return "\n".join(lines)


# =============================================================================
# 链接器 (Linker)
# =============================================================================

class Linker:
    """
    链接器
    将 Prompt 与能力、记忆绑定，生成可执行 Prompt
    """

    def __init__(
        self,
        capabilities: dict[str, Callable],
        memory_manager: Optional[Any] = None,  # DistributedMemoryManager
    ):
        self.capabilities = capabilities
        self.memory_manager = memory_manager

    def link(self, prompt: GeneratedPrompt) -> dict[str, Any]:
        """链接 Prompt 和能力"""
        return {
            "prompt": prompt.to_dict(),
            "capabilities": self._get_relevant_capabilities(prompt.intent),
            "executable": True,
        }

    def _get_relevant_capabilities(self, intent: StructuredIntent) -> list[str]:
        """获取相关能力"""
        relevant = []

        # 根据动作推断需要的能力
        action_to_cap = {
            "analyze": ["data_query", "statistics"],
            "query": ["data_query"],
            "generate": ["template_render"],
            "compare": ["data_query", "comparison"],
        }

        for cap in action_to_cap.get(intent.action, []):
            if cap in self.capabilities:
                relevant.append(cap)

        return relevant

    async def link_with_memories(
        self,
        prompt: GeneratedPrompt,
        context: Optional[Any] = None,
    ) -> dict[str, Any]:
        """链接 Prompt、能力和记忆"""
        # 1. 绑定能力
        capabilities = self._get_relevant_capabilities(prompt.intent)

        # 2. 解析并注入记忆
        memories = {}
        if self.memory_manager:
            memories = await self._resolve_memory_references(prompt)
            prompt = await self._inject_memories(prompt, memories)

            # 添加上下文记忆
            if context:
                prompt = await self._add_context_memories(prompt, context)

        # 3. 绑定参数
        bound_params = self._bind_params(prompt.intent.parameters, memories)

        return {
            "prompt": prompt.to_dict(),
            "capabilities": capabilities,
            "memories": memories,
            "params": bound_params,
            "executable": True,
        }

    async def _resolve_memory_references(self, prompt: GeneratedPrompt) -> dict[str, Any]:
        """解析 Prompt 中的记忆引用"""
        import re
        memories = {}

        # 提取记忆引用 ${memory.type.key}
        pattern = r'\$\{memory\.([^}]+)\}'

        # 从 System Prompt 中提取
        refs = re.findall(pattern, prompt.system_prompt)
        # 从 User Prompt 中提取
        refs.extend(re.findall(pattern, prompt.user_prompt))
        # 从参数中提取
        refs.extend(re.findall(pattern, str(prompt.intent.parameters)))

        refs = list(set(refs))

        for ref in refs:
            # 解析引用格式 type.key
            parts = ref.split('.', 1)
            if len(parts) == 2:
                memory_type, key = parts
            else:
                memory_type, key = "auto", ref

            # 检索记忆
            try:
                if memory_type == "short_term":
                    entry = await self.memory_manager.get_short_term(key)
                elif memory_type == "long_term":
                    entry = await self.memory_manager.get_long_term(key)
                else:
                    entry = await self.memory_manager.get(key)

                if entry:
                    memories[ref] = entry.value
            except Exception as e:
                print(f"检索记忆失败 {ref}: {e}")
                memories[ref] = None

        return memories

    async def _inject_memories(self, prompt: GeneratedPrompt, memories: dict[str, Any]) -> GeneratedPrompt:
        """将记忆注入到 Prompt"""
        import re

        system_prompt = prompt.system_prompt
        user_prompt = prompt.user_prompt

        for ref, value in memories.items():
            placeholder = f"${{memory.{ref}}}"
            str_value = str(value) if value is not None else ""

            # 替换 System Prompt 中的记忆引用
            system_prompt = re.sub(re.escape(placeholder), str_value, system_prompt)
            # 替换 User Prompt 中的记忆引用
            user_prompt = re.sub(re.escape(placeholder), str_value, user_prompt)

        return GeneratedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            intent=prompt.intent,
            metadata=prompt.metadata,
        )

    async def _add_context_memories(
        self,
        prompt: GeneratedPrompt,
        context: Any,
    ) -> GeneratedPrompt:
        """添加上下文记忆到 System Prompt"""
        context_section = []

        # 获取用户偏好
        if hasattr(context, 'user_id'):
            user_pref = await self.memory_manager.get_short_term(
                f"user:{context.user_id}:preference"
            )
            if user_pref:
                context_section.append(f"## 用户偏好\n{user_pref.value}")

        # 获取对话历史
        if hasattr(context, 'session_id'):
            history = await self.memory_manager.get_short_term(
                f"session:{context.session_id}:history"
            )
            if history:
                context_section.append(f"## 对话历史\n{history.value}")

        # 获取相关知识
        knowledge = await self.memory_manager.get_by_tag("knowledge")
        if knowledge:
            context_section.append("## 相关知识")
            for k in knowledge[:3]:  # 最多 3 条
                context_section.append(f"- {k.value}")

        if context_section:
            context_text = "\n\n".join(context_section)
            prompt.system_prompt += f"\n\n## 上下文\n{context_text}"

        return prompt

    def _bind_params(self, params: dict, memories: dict[str, Any]) -> dict:
        """绑定参数中的记忆引用"""
        import re
        bound = {}

        for key, value in params.items():
            if isinstance(value, str):
                # 替换记忆引用
                for ref, mem_value in memories.items():
                    placeholder = f"${{memory.{ref}}}"
                    value = value.replace(placeholder, str(mem_value) if mem_value else "")
            bound[key] = value

        return bound


# =============================================================================
# 意图编译器 (Intent Compiler)
# =============================================================================

class IntentCompiler:
    """
    意图编译器

    完整编译流程:
    自然语言 → Lexer → Tokens → Parser → AST → SemanticAnalyzer →
    StructuredIntent → CodeGenerator → Prompt → Linker(with Memory) → Executable
    """

    def __init__(
        self,
        capabilities: Optional[dict[str, Any]] = None,
        memory_manager: Optional[Any] = None,  # DistributedMemoryManager
    ):
        self.capabilities = capabilities or {}
        self.memory_manager = memory_manager
        self._capability_funcs: dict[str, Callable] = {}

    def register_capability(self, name: str, func: Callable, description: str = "") -> None:
        """注册能力"""
        self.capabilities[name] = {"description": description}
        self._capability_funcs[name] = func

    def compile(self, source: str) -> GeneratedPrompt:
        """
        编译意图

        Args:
            source: 自然语言输入

        Returns:
            生成的 Prompt
        """
        # 1. 词法分析
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # 2. 语法分析
        parser = Parser(tokens)
        ast = parser.parse()

        # 3. 语义分析
        analyzer = SemanticAnalyzer()
        intent = analyzer.analyze(ast)

        # 4. 代码生成
        generator = CodeGenerator(self.capabilities)
        prompt = generator.generate(intent)

        return prompt

    async def compile_and_link(
        self,
        source: str,
        context: Optional[Any] = None,
    ) -> dict[str, Any]:
        """编译并链接（包含记忆）"""
        prompt = self.compile(source)

        if self.memory_manager:
            # 使用记忆链接
            linker = Linker(self._capability_funcs, self.memory_manager)
            return await linker.link_with_memories(prompt, context)
        else:
            # 简单链接（无记忆）
            linker = Linker(self._capability_funcs)
            return linker.link(prompt)

    async def execute(
        self,
        source: str,
        context: Optional[Any] = None,
    ) -> Any:
        """编译、链接（含记忆）并执行"""
        executable = await self.compile_and_link(source, context)

        # 执行相关能力
        results = {}
        for cap_name in executable["capabilities"]:
            if cap_name in self._capability_funcs:
                func = self._capability_funcs[cap_name]
                if asyncio.iscoroutinefunction(func):
                    results[cap_name] = await func(executable["prompt"]["intent"])
                else:
                    results[cap_name] = func(executable["prompt"]["intent"])

        return {
            "prompt": executable["prompt"],
            "memories": executable.get("memories", {}),
            "results": results,
        }


# =============================================================================
# 便捷函数
# =============================================================================

def compile_intent(
    source: str,
    capabilities: Optional[dict] = None,
    memory_manager: Optional[Any] = None,
) -> GeneratedPrompt:
    """便捷函数：编译意图"""
    compiler = IntentCompiler(capabilities, memory_manager)
    return compiler.compile(source)


def create_compiler(
    capabilities: Optional[dict] = None,
    memory_manager: Optional[Any] = None,
) -> IntentCompiler:
    """创建编译器"""
    return IntentCompiler(capabilities, memory_manager)


# =============================================================================
# 示例
# =============================================================================

if __name__ == "__main__":
    import asyncio

    async def demo_with_memory():
        """演示带记忆注入的编译"""
        from intentos import create_memory_manager, create_and_initialize_memory_manager, Context

        # 创建记忆管理器
        memory_manager = await create_and_initialize_memory_manager(
            short_term_max=1000,
            long_term_enabled=True,
            long_term_backend="file",
        )
        await memory_manager.initialize()

        try:
            # 设置记忆
            await memory_manager.set_short_term(
                key="user:manager_001:preference",
                value={"region": "华东", "format": "dashboard"},
                tags=["user", "preference"],
            )

            await memory_manager.set_long_term(
                key="knowledge:sales_terms",
                value={
                    "Q3": "第三季度 (7-9 月)",
                    "GMV": "商品交易总额",
                },
                tags=["knowledge", "sales"],
            )

            # 创建编译器（带记忆管理器）
            compiler = IntentCompiler(
                capabilities={
                    "data_query": {"description": "查询数据"},
                    "analyze": {"description": "分析数据"},
                },
                memory_manager=memory_manager,
            )

            # 编译包含记忆引用的意图（使用简单语法）
            source = "分析华东区 Q3 销售数据"

            print("=" * 60)
            print("IntentOS 编译器 - 带记忆注入演示")
            print("=" * 60)
            print(f"\n输入：{source}\n")

            # 编译并链接（含记忆）
            context = Context(user_id="manager_001", session_id="session_001")
            executable = await compiler.compile_and_link(source, context)

            print(f"绑定的能力：{executable['capabilities']}")
            print(f"注入的上下文记忆：{executable.get('memories', {})}")
            print(f"\n编译后的 System Prompt:")
            print(executable['prompt']['system_prompt'][:500] + "...")
            print(f"\n编译后的 User Prompt:")
            print(executable['prompt']['user_prompt'])

        finally:
            await memory_manager.shutdown()

    # 运行演示
    asyncio.run(demo_with_memory())
