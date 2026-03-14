"""
语义 VM (Semantic VM)

IntentOS 的本质是一个语义虚拟机：
- 指令集：语义指令 (CREATE/MODIFY/QUERY/LOOP/BRANCH...)
- 处理器：LLM
- 内存：语义存储 (意图/能力/策略/Prompt/上下文)
- 图灵完备：是 (支持循环 + 分支)

核心洞察:
- LLM 是处理器，不是外部工具
- 语义指令在存储中，可自修改
- Self-Bootstrap 是语义 VM 的自然结果
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from .safe_eval import SafeConditionEvaluator

# =============================================================================
# 语义指令类型
# =============================================================================


class SemanticOpcode(Enum):
    """语义操作码"""

    # 基础指令
    CREATE = "create"  # 创建组件
    MODIFY = "modify"  # 修改组件
    DELETE = "delete"  # 删除组件
    QUERY = "query"  # 查询状态

    # 执行指令
    EXECUTE = "execute"  # 执行意图
    CALL = "call"  # 调用子程序

    # 控制流指令 (图灵完备关键)
    IF = "if"  # 条件分支
    ELSE = "else"
    ENDIF = "endif"

    LOOP = "loop"  # 循环
    WHILE = "while"  # 条件循环
    ENDLOOP = "endloop"

    JUMP = "jump"  # 跳转
    LABEL = "label"  # 标签

    # 数据操作
    SET = "set"  # 设置变量
    GET = "get"  # 获取变量

    # 元指令 (Self-Bootstrap)
    DEFINE_INSTRUCTION = "define_instruction"  # 定义新指令
    MODIFY_PROCESSOR = "modify_processor"  # 修改处理器 Prompt


# =============================================================================
# 语义指令
# =============================================================================


@dataclass
class SemanticInstruction:
    """
    语义指令
    """

    # 操作码
    opcode: Union[SemanticOpcode, Any]

    # 目标类型 (TEMPLATE/CAPABILITY/POLICY/CONFIG/PROGRAM)
    target: Optional[str] = None

    # 目标名称
    target_name: Optional[str] = None

    # 指令参数
    parameters: dict[str, Any] = field(default_factory=dict)

    # 条件 (用于 IF/WHILE)
    condition: Optional[str] = None

    # 指令体 (用于 LOOP/WHILE/IF)
    body: list[SemanticInstruction] = field(default_factory=list)

    # 标签 (用于跳转)
    label: Optional[str] = None

    # 跳转目标
    jump_target: Optional[str] = None

    # 元数据
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    line_number: int = 0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "opcode": self.opcode.value if hasattr(self.opcode, "value") else self.opcode,
            "target": self.target,
            "target_name": self.target_name,
            "parameters": self.parameters,
            "condition": self.condition,
            "body": [i.to_dict() for i in self.body],
            "label": self.label,
            "jump_target": self.jump_target,
            "line_number": self.line_number,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SemanticInstruction:
        """从字典创建"""
        raw_opcode = data["opcode"]
        try:
            opcode = SemanticOpcode(raw_opcode)
        except (ValueError, KeyError):
            # 可能是分布式操作码或自定义操作码
            from intentos.distributed import DistributedOpcode

            try:
                opcode = DistributedOpcode(raw_opcode)
            except (ValueError, KeyError, ImportError):
                opcode = raw_opcode

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            opcode=opcode,
            target=data.get("target"),
            target_name=data.get("target_name"),
            parameters=data.get("parameters", {}),
            condition=data.get("condition"),
            body=[cls.from_dict(i) for i in data.get("body", [])],
            label=data.get("label"),
            jump_target=data.get("jump_target"),
            line_number=data.get("line_number", 0),
        )

    def to_natural_language(self) -> str:
        """转换为自然语言"""
        opcode_val = self.opcode.value if hasattr(self.opcode, "value") else str(self.opcode)
        if self.opcode == SemanticOpcode.CREATE:
            return f"CREATE {self.target} {self.target_name} WITH {self.parameters}"
        elif self.opcode == SemanticOpcode.MODIFY:
            return f"MODIFY {self.target} {self.target_name} TO {self.parameters}"
        elif self.opcode == SemanticOpcode.QUERY:
            return f"QUERY {self.target} WHERE {self.parameters}"
        elif self.opcode == SemanticOpcode.WHILE:
            return f"WHILE {self.condition} DO [...]"
        elif self.opcode == SemanticOpcode.LOOP:
            times = self.parameters.get("times", "∞")
            return f"LOOP {times} TIMES [...]"
        else:
            return f"{opcode_val.upper()} {self.target or ''}"


# =============================================================================
# 语义程序
# =============================================================================


@dataclass
class SemanticProgram:
    """
    语义程序

    由语义指令组成的可执行程序
    """

    name: str
    description: str = ""
    instructions: list[SemanticInstruction] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    def add_instruction(self, instr: SemanticInstruction) -> None:
        """添加指令"""
        self.instructions.append(instr)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "instructions": [i.to_dict() for i in self.instructions],
            "variables": self.variables,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SemanticProgram:
        """从字典创建"""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            instructions=[SemanticInstruction.from_dict(i) for i in data.get("instructions", [])],
            variables=data.get("variables", {}),
            version=data.get("version", "1.0.0"),
        )


# =============================================================================
# 语义内存
# =============================================================================


class SemanticMemory:
    """
    语义内存

    存储语义数据的内存空间
    """

    def __init__(self):
        # 语义存储
        self.templates: dict[str, Any] = {}  # 意图模板
        self.capabilities: dict[str, Any] = {}  # 能力
        self.policies: dict[str, Any] = {}  # 策略
        self.prompts: dict[str, Any] = {}  # Prompt
        self.configs: dict[str, Any] = {}  # 配置
        self.programs: dict[str, SemanticProgram] = {}  # 程序
        self.variables: dict[str, Any] = {}  # 变量
        self.audit_log: list[dict] = []  # 审计日志

    def get(self, store: str, key: str) -> Optional[Any]:
        """获取数据"""
        store_map = {
            "TEMPLATE": self.templates,
            "CAPABILITY": self.capabilities,
            "POLICY": self.policies,
            "PROMPT": self.prompts,
            "CONFIG": self.configs,
            "PROGRAM": self.programs,
            "VARIABLE": self.variables,
        }
        return store_map.get(store, {}).get(key)

    def set(self, store: str, key: str, value: Any) -> None:
        """设置数据"""
        store_map = {
            "TEMPLATE": self.templates,
            "CAPABILITY": self.capabilities,
            "POLICY": self.policies,
            "PROMPT": self.prompts,
            "CONFIG": self.configs,
            "PROGRAM": self.programs,
            "VARIABLE": self.variables,
        }
        if store in store_map:
            store_map[store][key] = value

    def delete(self, store: str, key: str) -> bool:
        """删除数据"""
        store_map = {
            "TEMPLATE": self.templates,
            "CAPABILITY": self.capabilities,
            "POLICY": self.policies,
            "PROMPT": self.prompts,
            "CONFIG": self.configs,
            "PROGRAM": self.programs,
            "VARIABLE": self.variables,
        }
        if store in store_map and key in store_map[store]:
            del store_map[store][key]
            return True
        return False

    def query(self, store: str, condition: Optional[str] = None) -> list[dict]:
        """查询数据"""
        store_map = {
            "TEMPLATE": self.templates,
            "CAPABILITY": self.capabilities,
            "POLICY": self.policies,
            "PROMPT": self.prompts,
            "CONFIG": self.configs,
            "PROGRAM": self.programs,
            "VARIABLE": self.variables,
        }

        if store not in store_map:
            return []

        results = []
        for key, value in store_map[store].items():
            if condition is None:
                results.append({"key": key, "value": value})
            else:
                # 简化条件判断
                if self._evaluate_condition(condition, {"key": key, "value": value}):
                    results.append({"key": key, "value": value})

        return results

    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """评估条件"""
        # 简化实现，实际应该用 LLM 评估
        try:
            # 支持简单条件如：key == "sales"
            return eval(condition, {}, context)
        except Exception:
            return False

    def log_audit(self, action: str, details: dict) -> str:
        """记录审计日志"""
        audit_id = str(uuid.uuid4())
        self.audit_log.append(
            {
                "id": audit_id,
                "action": action,
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return audit_id

    def get_state(self) -> dict[str, Any]:
        """获取内存状态"""
        return {
            "templates_count": len(self.templates),
            "capabilities_count": len(self.capabilities),
            "policies_count": len(self.policies),
            "prompts_count": len(self.prompts),
            "configs_count": len(self.configs),
            "programs_count": len(self.programs),
            "variables_count": len(self.variables),
            "audit_log_count": len(self.audit_log),
        }


# =============================================================================
# LLM 处理器
# =============================================================================


class LLMProcessor:
    """
    LLM 处理器

    使用 LLM 解析和执行语义指令
    """

    # 执行 Prompt 模板
    EXECUTE_PROMPT = """
你是一个语义 VM 处理器。请解析并执行以下语义指令。

## 语义指令
{instruction_nl}

## 指令详情
{instruction_json}

## 当前内存状态
{memory_state}

## 可用操作
- create_template: 创建意图模板
- modify_template: 修改意图模板
- delete_template: 删除意图模板
- create_capability: 注册能力
- modify_config: 修改配置
- query_status: 查询状态
- execute_program: 执行程序

## 输出格式
请返回 JSON 格式:
{{
    "operation": "操作名称",
    "parameters": {{...}},
    "result": {{...}},
    "error": "错误信息 (如果失败)"
}}
"""

    def __init__(self, llm_executor: Any):
        """
        初始化处理器

        Args:
            llm_executor: LLM 执行器
        """
        self.llm_executor = llm_executor
        self.processor_prompt = self.EXECUTE_PROMPT

    async def execute(
        self,
        instruction: SemanticInstruction,
        memory: SemanticMemory,
    ) -> dict[str, Any]:
        """
        执行语义指令

        Args:
            instruction: 语义指令
            memory: 语义内存

        Returns:
            执行结果
        """
        # 1. 检查是否有动态处理器 (Self-Bootstrap 扩展)
        handler_name = f"_handle_{instruction.opcode.value.lower()}"
        if hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            return await handler(self, instruction.parameters, memory)

        # 2. 构建执行 Prompt
        exec_prompt = self.processor_prompt.format(
            instruction_nl=instruction.to_natural_language(),
            instruction_json=json.dumps(instruction.to_dict(), indent=2, ensure_ascii=False),
            memory_state=json.dumps(memory.get_state(), indent=2),
        )

        # LLM 执行
        messages = [
            {"role": "system", "content": "你是语义 VM 处理器。"},
            {"role": "user", "content": exec_prompt},
        ]

        response = await self.llm_executor.execute(messages)

        # 解析结果
        result = self._parse_response(response.content)

        # 执行操作
        if result.get("success", True):
            await self._apply_operation(result, memory)

        return result

    def _parse_response(self, content: str) -> dict[str, Any]:
        """解析 LLM 响应"""
        try:
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            return json.loads(json_str)
        except Exception as e:
            return {
                "success": False,
                "error": f"解析失败：{e}",
                "raw_content": content,
            }

    async def _apply_operation(
        self,
        result: dict[str, Any],
        memory: SemanticMemory,
    ) -> None:
        """应用操作结果"""
        operation = result.get("operation", "")
        parameters = result.get("parameters", {})

        if operation == "create_template":
            name = parameters.get("name")
            if name:
                memory.set("TEMPLATE", name, parameters)

        elif operation == "modify_config":
            key = parameters.get("key")
            value = parameters.get("value")
            if key:
                memory.set("CONFIG", key, value)

        elif operation == "query_status":
            # 查询结果已包含在 result 中
            pass

        # 添加更多操作处理...

    async def execute_llm(self, prompt: str, memory: SemanticMemory) -> dict[str, Any]:
        """执行原始 LLM 提示"""
        messages = [
            {"role": "system", "content": "你是语义 VM 处理器。"},
            {
                "role": "user",
                "content": f"当前内存状态: {json.dumps(memory.get_state())}\n\n指令: {prompt}",
            },
        ]
        response = await self.llm_executor.execute(messages)
        return self._parse_response(response.content)

    def update_processor_prompt(self, new_prompt: str) -> None:
        """更新处理器 Prompt (Self-Bootstrap)"""
        self.processor_prompt = new_prompt


# =============================================================================
# 语义 VM 执行器
# =============================================================================


class SemanticVM:
    """
    语义虚拟机

    执行语义程序的完整虚拟机
    """

    def __init__(self, llm_executor: Any):
        """
        初始化 VM

        Args:
            llm_executor: LLM 执行器
        """
        self.memory = SemanticMemory()
        self.processor = LLMProcessor(llm_executor)
        self.pc = 0  # 程序计数器
        self.running = False

    async def load_program(self, program: SemanticProgram) -> None:
        """加载程序"""
        self.memory.set("PROGRAM", program.name, program)

    async def execute_program(
        self,
        program_name: str,
        context: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        执行程序

        Args:
            program_name: 程序名称
            context: 执行上下文

        Returns:
            执行结果
        """
        program = self.memory.get("PROGRAM", program_name)
        if not program:
            return {"success": False, "error": f"程序不存在：{program_name}"}

        self.pc = 0
        self.running = True

        results = []
        max_iterations = 10000  # 防止无限循环
        iterations = 0

        while self.pc < len(program.instructions) and self.running and iterations < max_iterations:
            instruction = program.instructions[self.pc]

            # 执行指令
            result = await self._execute_instruction(instruction, program)
            results.append(result)

            # 更新程序计数器
            if result.get("jump"):
                self.pc = result["jump"]
            else:
                self.pc += 1

            iterations += 1

        self.running = False

        return {
            "success": True,
            "results": results,
            "final_state": self.memory.get_state(),
        }

    async def _execute_instruction(
        self,
        instruction: SemanticInstruction,
        program: SemanticProgram,
    ) -> dict[str, Any]:
        """执行单条指令"""

        # 处理标签
        if instruction.label:
            return {"success": True, "jump": None}

        # 处理条件分支
        if instruction.opcode == SemanticOpcode.IF:
            if not self._evaluate_condition(instruction.condition, program.variables):
                # 跳过 IF 体
                return {
                    "success": True,
                    "jump": self._find_endif(program.instructions, self.pc) + 1,
                }
            return {"success": True}

        elif instruction.opcode == SemanticOpcode.ELSE:
            # 跳过 ELSE 体 (因为 IF 体已执行)
            return {"success": True, "jump": self._find_endif(program.instructions, self.pc) + 1}

        elif instruction.opcode == SemanticOpcode.ENDIF:
            return {"success": True}

        # 处理循环
        elif instruction.opcode == SemanticOpcode.LOOP:
            times = instruction.parameters.get("times", 1)
            current_loop = instruction.parameters.get("_current_loop", 0)

            if current_loop < times:
                instruction.parameters["_current_loop"] = current_loop + 1
                # 跳转到循环体开始
                return {"success": True, "jump": self.pc + 1}
            else:
                # 循环结束，跳转到循环体后
                instruction.parameters.pop("_current_loop", None)
                return {
                    "success": True,
                    "jump": self._find_endloop(program.instructions, self.pc) + 1,
                }

        elif instruction.opcode == SemanticOpcode.WHILE:
            if self._evaluate_condition(instruction.condition, program.variables):
                return {"success": True, "jump": self.pc + 1}
            else:
                return {
                    "success": True,
                    "jump": self._find_endloop(program.instructions, self.pc) + 1,
                }

        elif instruction.opcode == SemanticOpcode.ENDLOOP:
            # 跳回循环开始
            return {"success": True, "jump": self._find_loop_start(program.instructions, self.pc)}

        # 处理跳转
        elif instruction.opcode == SemanticOpcode.JUMP:
            return {
                "success": True,
                "jump": self._find_label(program.instructions, instruction.jump_target),
            }

        # 处理变量操作
        elif instruction.opcode == SemanticOpcode.SET:
            name = instruction.parameters.get("name")
            value = instruction.parameters.get("value")
            if name:
                program.variables[name] = value
                self.memory.set("VARIABLE", name, value)
            return {"success": True}

        elif instruction.opcode == SemanticOpcode.GET:
            name = instruction.parameters.get("name")
            if name:
                value = self.memory.get("VARIABLE", name)
                program.variables[name] = value
            return {"success": True}

        # 处理基础指令 (CREATE/MODIFY/QUERY/EXECUTE)
        else:
            result = await self.processor.execute(instruction, self.memory)

            # 记录审计
            self.memory.log_audit(
                action=instruction.opcode.value,
                details=instruction.to_dict(),
            )

            return result

    def _evaluate_condition(self, condition: str, variables: dict) -> bool:
        """评估条件（安全版本）"""
        if not condition:
            return True

        try:
            # 使用安全评估器替代 eval()
            return SafeConditionEvaluator.evaluate(condition, variables)
        except ValueError as e:
            # 记录安全日志
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"不安全或无效的条件表达式：{condition}, 错误：{e}")
            return False  # 不安全条件视为 False
        except Exception as e:
            return False

    def _find_endif(self, instructions: list[SemanticInstruction], start: int) -> int:
        """查找 ENDIF 位置"""
        depth = 1
        for i in range(start + 1, len(instructions)):
            if instructions[i].opcode == SemanticOpcode.IF:
                depth += 1
            elif instructions[i].opcode == SemanticOpcode.ENDIF:
                depth -= 1
                if depth == 0:
                    return i
        return len(instructions) - 1

    def _find_endloop(self, instructions: list[SemanticInstruction], start: int) -> int:
        """查找 ENDLOOP 位置"""
        depth = 1
        for i in range(start + 1, len(instructions)):
            if instructions[i].opcode in [SemanticOpcode.LOOP, SemanticOpcode.WHILE]:
                depth += 1
            elif instructions[i].opcode == SemanticOpcode.ENDLOOP:
                depth -= 1
                if depth == 0:
                    return i
        return len(instructions) - 1

    def _find_loop_start(self, instructions: list[SemanticInstruction], end: int) -> int:
        """查找循环开始位置"""
        depth = 1
        for i in range(end - 1, -1, -1):
            if instructions[i].opcode == SemanticOpcode.ENDLOOP:
                depth += 1
            elif instructions[i].opcode in [SemanticOpcode.LOOP, SemanticOpcode.WHILE]:
                depth -= 1
                if depth == 0:
                    return i
        return 0

    def _find_label(self, instructions: list[SemanticInstruction], label: str) -> int:
        """查找标签位置"""
        for i, instr in enumerate(instructions):
            if instr.label == label:
                return i
        return self.pc + 1


# =============================================================================
# 便捷函数
# =============================================================================


def create_semantic_vm(llm_executor: Any) -> SemanticVM:
    """创建语义 VM"""
    return SemanticVM(llm_executor)


def create_program(name: str, description: str = "") -> SemanticProgram:
    """创建程序"""
    return SemanticProgram(name=name, description=description)


def create_instruction(
    opcode: SemanticOpcode,
    target: Optional[str] = None,
    target_name: Optional[str] = None,
    **parameters,
) -> SemanticInstruction:
    """创建指令"""
    return SemanticInstruction(
        opcode=opcode,
        target=target,
        target_name=target_name,
        parameters=parameters,
    )
