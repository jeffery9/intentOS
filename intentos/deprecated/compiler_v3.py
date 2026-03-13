"""
IntentOS 编译器 v2.0

核心理念:
- 意图 (Intent) = 源代码
- Prompt = 中间表示 (IR)
- LLM = 处理器 (执行 IR)
- IntentOS = 编译器前端 (词法/语法/语义分析由 LLM 完成)

架构原则:
1. 自然语言处理 → 交给 LLM
2. 结构化验证 → IntentOS 负责
3. 代码生成 → 模板填充
4. 链接 → 能力/记忆绑定
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from enum import Enum
import time
import uuid


# =============================================================================
# 编译中间表示
# =============================================================================

@dataclass
class StructuredIntent:
    """
    结构化意图 (编译后的 IR)
    
    由 LLM 从自然语言解析而来
    """
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


@dataclass
class GeneratedPrompt:
    """
    生成的 Prompt (可执行的 IR)
    """
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


# =============================================================================
# LLM 驱动的解析器
# =============================================================================

class IntentParser:
    """
    意图解析器
    
    使用 LLM 将自然语言解析为结构化意图
    """
    
    # 解析 Prompt 模板
    PARSE_PROMPT = """
你是一个意图解析专家。请将用户的自然语言输入解析为结构化的意图。

## 输出格式
请返回 JSON 格式，包含以下字段:
{
    "action": "动作 (analyze/query/generate/create/compare 等)",
    "target": "目标对象",
    "parameters": {
        // 从输入中提取的参数
    },
    "constraints": {
        // 约束条件
    },
    "confidence": 0.0-1.0  // 解析置信度
}

## 示例
输入："分析华东区 Q3 销售数据，对比去年同期"
输出:
{
    "action": "analyze",
    "target": "销售数据",
    "parameters": {
        "region": "华东",
        "period": "Q3",
        "compare_with": "last_year"
    },
    "constraints": {},
    "confidence": 0.95
}

## 用户输入
输入："{user_input}"

请解析为结构化意图:
"""
    
    def __init__(self, llm_executor: Any = None):
        """
        初始化解析器
        
        Args:
            llm_executor: LLM 执行器 (用于解析自然语言)
        """
        self.llm_executor = llm_executor
    
    async def parse(
        self,
        source: str,
        context: Optional[dict] = None,
    ) -> StructuredIntent:
        """
        解析自然语言为结构化意图
        
        Args:
            source: 自然语言输入
            context: 上下文信息
        
        Returns:
            结构化意图
        """
        if not self.llm_executor:
            raise ValueError("需要配置 LLM 执行器")
        
        # 构建解析 Prompt
        parse_prompt = self.PARSE_PROMPT.format(user_input=source)
        
        # 调用 LLM 解析
        messages = [
            {"role": "system", "content": "你是一个意图解析专家。"},
            {"role": "user", "content": parse_prompt},
        ]
        
        response = await self.llm_executor.execute(messages)
        
        # 解析 LLM 返回的 JSON
        import json
        try:
            # 提取 JSON 部分
            json_str = response.content
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            parsed = json.loads(json_str.strip())
            
            return StructuredIntent(
                action=parsed.get("action", ""),
                target=parsed.get("target", ""),
                parameters=parsed.get("parameters", {}),
                constraints=parsed.get("constraints", {}),
                context=context or {},
                confidence=parsed.get("confidence", 1.0),
            )
        except Exception as e:
            # 解析失败，返回基本结构
            return StructuredIntent(
                action="unknown",
                target=source,
                parameters={"raw_input": source},
                context=context or {},
                confidence=0.0,
            )


# =============================================================================
# 代码生成器
# =============================================================================

class CodeGenerator:
    """
    代码生成器
    
    将结构化意图转换为可执行的 Prompt
    """
    
    # Prompt 模板库
    TEMPLATES = {
        "atomic": """
# AI 助手指令

你是一个专业的 AI 助手，需要执行用户的意图。

## 意图信息
- **动作**: {action}
- **目标**: {target}
- **参数**: {parameters}

## 可用能力
{capabilities}

## 输出要求
- 准确理解用户意图
- 调用合适的能力
- 返回结构化的结果
""",
        "composite": """
# 复合任务执行计划

你是一个 AI 原生助手，需要执行一个多步骤的复合任务。

## 意图信息
- **动作**: {action}
- **目标**: {target}

## 执行步骤
{steps}

## 上下文信息
{context}

请按顺序执行上述步骤，每一步的输出将作为下一步的输入。
最终返回整合后的结果。
""",
    }
    
    def __init__(self, capabilities: Optional[dict[str, Any]] = None):
        self.capabilities = capabilities or {}
    
    def generate(self, intent: StructuredIntent) -> GeneratedPrompt:
        """生成 Prompt"""
        # 选择模板
        template_name = self._select_template(intent)
        template = self.TEMPLATES.get(template_name, self.TEMPLATES["atomic"])
        
        # 填充模板
        system_prompt = template.format(
            action=intent.action,
            target=intent.target,
            parameters=self._format_params(intent.parameters),
            capabilities=self._format_capabilities(),
            steps=self._format_steps(intent),
            context=self._format_context(intent.context),
        )
        
        user_prompt = f"请{intent.action}{intent.target}"
        
        return GeneratedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            intent=intent,
            metadata={
                "generated_at": time.time(),
                "intent_id": intent.id,
                "template": template_name,
            },
        )
    
    def _select_template(self, intent: StructuredIntent) -> str:
        """选择模板"""
        # 根据参数复杂度选择
        if len(intent.parameters) > 5:
            return "composite"
        return "atomic"
    
    def _format_params(self, params: dict) -> str:
        """格式化参数"""
        if not params:
            return "（无参数）"
        return "\n".join(f"- {k}: {v}" for k, v in params.items())
    
    def _format_capabilities(self) -> str:
        """格式化能力列表"""
        if not self.capabilities:
            return "（无可用能力）"
        lines = [f"- **{name}**: {cap.get('description', '')}" 
                 for name, cap in self.capabilities.items()]
        return "\n".join(lines)
    
    def _format_steps(self, intent: StructuredIntent) -> str:
        """格式化步骤"""
        return "（自动推导执行步骤）"
    
    def _format_context(self, context: dict) -> str:
        """格式化上下文"""
        if not context:
            return "（无特殊上下文）"
        return "\n".join(f"- {k}: {v}" for k, v in context.items())


# =============================================================================
# 链接器
# =============================================================================

class Linker:
    """
    链接器
    
    将 Prompt 与能力、记忆绑定
    """
    
    def __init__(
        self,
        capabilities: dict[str, Callable],
        memory_manager: Optional[Any] = None,
    ):
        self.capabilities = capabilities
        self.memory_manager = memory_manager
    
    async def link(
        self,
        prompt: GeneratedPrompt,
        context: Optional[dict] = None,
    ) -> dict[str, Any]:
        """链接 Prompt、能力和记忆"""
        # 1. 绑定能力
        capabilities = self._get_relevant_capabilities(prompt.intent)
        
        # 2. 注入记忆 (如果有记忆管理器)
        memories = {}
        if self.memory_manager:
            memories = await self._resolve_memories(prompt)
            prompt = await self._inject_memories(prompt, memories)
        
        return {
            "prompt": prompt.to_dict(),
            "capabilities": capabilities,
            "memories": memories,
            "executable": True,
        }
    
    def _get_relevant_capabilities(self, intent: StructuredIntent) -> list[str]:
        """获取相关能力"""
        action_to_cap = {
            "analyze": ["data_query", "statistics"],
            "query": ["data_query"],
            "generate": ["template_render"],
            "compare": ["data_query", "comparison"],
        }
        
        relevant = []
        for cap in action_to_cap.get(intent.action, []):
            if cap in self.capabilities:
                relevant.append(cap)
        
        return relevant
    
    async def _resolve_memories(
        self,
        prompt: GeneratedPrompt,
    ) -> dict[str, Any]:
        """解析记忆引用"""
        import re
        memories = {}
        
        # 提取记忆引用 ${memory.type.key}
        pattern = r'\$\{memory\.([^}]+)\}'
        refs = re.findall(pattern, prompt.system_prompt)
        refs.extend(re.findall(pattern, prompt.user_prompt))
        
        for ref in set(refs):
            parts = ref.split('.', 1)
            key = parts[1] if len(parts) == 2 else ref
            
            try:
                entry = await self.memory_manager.get(key)
                if entry:
                    memories[ref] = entry.value
            except Exception:
                pass
        
        return memories
    
    async def _inject_memories(
        self,
        prompt: GeneratedPrompt,
        memories: dict[str, Any],
    ) -> GeneratedPrompt:
        """注入记忆到 Prompt"""
        import re
        
        system_prompt = prompt.system_prompt
        user_prompt = prompt.user_prompt
        
        for ref, value in memories.items():
            placeholder = f"${{memory.{ref}}}"
            str_value = str(value) if value is not None else ""
            system_prompt = re.sub(re.escape(placeholder), str_value, system_prompt)
            user_prompt = re.sub(re.escape(placeholder), str_value, user_prompt)
        
        return GeneratedPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            intent=prompt.intent,
            metadata=prompt.metadata,
        )


# =============================================================================
# 意图编译器 (统一入口)
# =============================================================================

class IntentCompiler:
    """
    意图编译器
    
    完整编译流程:
    自然语言 → [LLM 解析] → StructuredIntent → [代码生成] → Prompt → [链接] → Executable
    """
    
    def __init__(
        self,
        llm_executor: Any = None,
        capabilities: Optional[dict[str, Any]] = None,
        memory_manager: Optional[Any] = None,
    ):
        """
        初始化编译器
        
        Args:
            llm_executor: LLM 执行器 (用于解析)
            capabilities: 能力注册表
            memory_manager: 记忆管理器
        """
        self.parser = IntentParser(llm_executor)
        self.generator = CodeGenerator(capabilities)
        self.linker = Linker(
            capabilities=self._extract_callables(capabilities),
            memory_manager=memory_manager,
        )
    
    def _extract_callables(self, capabilities: dict) -> dict[str, Callable]:
        """从能力注册表提取可调用函数"""
        # 简化实现，实际应该从 registry 获取
        return {}
    
    async def compile(
        self,
        source: str,
        context: Optional[dict] = None,
    ) -> GeneratedPrompt:
        """
        编译意图
        
        Args:
            source: 自然语言输入
            context: 上下文信息
        
        Returns:
            生成的 Prompt
        """
        # 1. LLM 解析 (自然语言 → 结构化意图)
        intent = await self.parser.parse(source, context)
        
        # 2. 代码生成 (结构化意图 → Prompt)
        prompt = self.generator.generate(intent)
        
        return prompt
    
    async def compile_and_link(
        self,
        source: str,
        context: Optional[dict] = None,
    ) -> dict[str, Any]:
        """编译并链接"""
        prompt = await self.compile(source, context)
        return await self.linker.link(prompt, context)


# =============================================================================
# 便捷函数
# =============================================================================

def create_compiler(
    llm_executor: Any = None,
    capabilities: Optional[dict] = None,
    memory_manager: Optional[Any] = None,
) -> IntentCompiler:
    """创建编译器"""
    return IntentCompiler(llm_executor, capabilities, memory_manager)
