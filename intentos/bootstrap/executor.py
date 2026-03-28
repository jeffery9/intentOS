"""
完整的 Self-Bootstrap 实现

基于分布式语义 VM，实现完整的自举能力：
1. 系统可以修改自身的解析规则
2. 系统可以修改自身的执行规则
3. 系统可以扩展自身的指令集
4. 系统可以复制自身到新节点
5. 系统可以动态扩缩容

核心洞察:
- Self-Bootstrap = 语义 VM + 可修改的存储 + 分布式
- 解析规则在存储中 (可修改)
- 执行规则在存储中 (可修改)
- 指令集在存储中 (可扩展)
"""

from __future__ import annotations
import logging

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from intentos.distributed import DistributedSemanticVM
    from intentos.semantic_vm import SemanticVM


# =============================================================================
# Self-Bootstrap 核心数据结构
# =============================================================================


@dataclass
class BootstrapRecord:
    """自举记录"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: str = ""  # modify_parse_prompt, modify_execute_prompt, extend_instructions...
    target: str = ""  # 修改目标
    old_value: Any = None
    new_value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    executed_by: str = ""  # 程序 ID
    approved_by: Optional[str] = None  # 审批人
    status: str = "pending"  # pending/approved/rejected/completed/failed

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "target": self.target,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat(),
            "executed_by": self.executed_by,
            "approved_by": self.approved_by,
            "status": self.status,
        }


@dataclass
class BootstrapPolicy:
    """自举策略"""

    allow_self_modification: bool = True
    require_approval_for: list[str] = field(
        default_factory=lambda: [
            "delete_all_templates",
            "modify_audit_rules",
            "disable_self_bootstrap",
        ]
    )
    max_modifications_per_hour: int = 10
    require_confidence_threshold: float = 0.8
    replication_factor: int = 3  # 自修改需要复制到的节点数
    consistency_level: str = "quorum"  # eventual/quorum/strong

    def to_dict(self) -> dict[str, Any]:
        return {
            "allow_self_modification": self.allow_self_modification,
            "require_approval_for": self.require_approval_for,
            "max_modifications_per_hour": self.max_modifications_per_hour,
            "require_confidence_threshold": self.require_confidence_threshold,
            "replication_factor": self.replication_factor,
            "consistency_level": self.consistency_level,
        }


# =============================================================================
# Self-Bootstrap 执行器
# =============================================================================


class SelfBootstrapExecutor:
    """
    Self-Bootstrap 执行器

    执行自修改操作的核心组件
    """

    def __init__(
        self,
        semantic_vm: SemanticVM | DistributedSemanticVM,
        policy: Optional[BootstrapPolicy] = None,
    ):
        self.vm = semantic_vm
        self.policy = policy or BootstrapPolicy()
        self.records: list[BootstrapRecord] = []
        self.modification_count = 0
        self.last_reset_time = datetime.now()

    async def execute_bootstrap(
        self,
        action: str,
        target: str,
        new_value: Any,
        context: dict[str, Any],
        program_id: str = "",
    ) -> BootstrapRecord:
        """
        执行自举操作

        Args:
            action: 操作类型
            target: 修改目标
            new_value: 新值
            context: 执行上下文
            program_id: 执行程序 ID

        Returns:
            自举记录
        """
        record = BootstrapRecord(
            action=action,
            target=target,
            new_value=new_value,
            executed_by=program_id,
        )

        try:
            # 1. 检查是否允许自修改
            if not self.policy.allow_self_modification:
                record.status = "rejected"
                record.old_value = "Self-modification is disabled"
                return record

            # 2. 检查速率限制
            if not self._check_rate_limit():
                record.status = "rejected"
                record.old_value = "Rate limit exceeded"
                return record

            # 3. 检查是否需要审批
            if self._requires_approval(action):
                record.status = "pending"
                # 实际实现应该发送审批请求
                # 这里简化为自动批准
                record.approved_by = "auto_approved"
                record.status = "approved"

            # 4. 获取旧值
            record.old_value = await self._get_current_value(target)

            # 5. 执行修改
            await self._apply_modification(target, new_value)

            # 6. 复制修改到多个节点 (分布式)
            if hasattr(self.vm, "memory"):
                await self._replicate_modification(target, new_value)

            # 7. 记录审计
            record.status = "completed"
            self.records.append(record)
            self.modification_count += 1

            return record

        except Exception as e:
            record.status = "failed"
            record.old_value = str(e)
            self.records.append(record)
            return record

    def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        now = datetime.now()

        # 重置计数器 (每小时)
        if (now - self.last_reset_time).total_seconds() > 3600:
            self.modification_count = 0
            self.last_reset_time = now

        return self.modification_count < self.policy.max_modifications_per_hour

    def _requires_approval(self, action: str) -> bool:
        """检查是否需要审批"""
        return action in self.policy.require_approval_for

    async def _get_current_value(self, target: str) -> Any:
        """获取当前值"""
        # 解析 target 路径
        # 例如："CONFIG.PARSE_PROMPT" 或 "INSTRUCTION_SET.META_ACTIONS"
        parts = target.split(".")

        if parts[0] == "CONFIG":
            if hasattr(self.vm, "memory"):
                result: Any = await self.vm.memory.get(
                    "CONFIG", parts[1] if len(parts) > 1 else target
                )  # type: ignore
                return result
        elif parts[0] == "INSTRUCTION_SET":
            # 返回当前指令集
            # 如果是分布式 VM，检查 local_vm 的处理器
            vm_to_check = self.vm.local_vm if hasattr(self.vm, "local_vm") else self.vm
            return list(vm_to_check.processor.__class__.__dict__.keys())
        elif parts[0] == "POLICY":
            if len(parts) > 1:
                return getattr(self.policy, parts[1], None)

        return None

    async def _apply_modification(self, target: str, new_value: Any) -> None:
        """
        应用修改
        
        支持修改类型:
        - CONFIG.xxx: 系统配置
        - COMPILER_RULE.xxx: 编译器规则
        - EXECUTOR_RULE.xxx: 执行器规则
        - INSTRUCTION.xxx: 指令集扩展
        - POLICY.xxx: 自举策略
        
        Args:
            target: 修改目标
            new_value: 新值
        """
        parts = target.split(".")
        category = parts[0]
        
        logging.info(f"Applying modification: {target}")
        
        if category == "CONFIG":
            # 修改系统配置
            if len(parts) > 1:
                config_key = parts[1]
                if hasattr(self.vm, "memory"):
                    await self.vm.memory.set("CONFIG", config_key, new_value)
                    logging.info(f"CONFIG.{config_key} updated")
        
        elif category == "COMPILER_RULE":
            # 修改编译器规则
            if len(parts) > 1:
                rule_name = parts[1]
                # 访问编译器实例
                if hasattr(self.vm, "compiler"):
                    compiler = self.vm.compiler
                    if hasattr(compiler, rule_name):
                        setattr(compiler, rule_name, new_value)
                        logging.info(f"COMPILER_RULE.{rule_name} updated")
                    elif hasattr(compiler, "rules"):
                        compiler.rules[rule_name] = new_value
                        logging.info(f"COMPILER_RULE.{rule_name} added to rules")
        
        elif category == "EXECUTOR_RULE":
            # 修改执行器规则
            if len(parts) > 1:
                rule_name = parts[1]
                # 访问执行器实例
                if hasattr(self.vm, "engine"):
                    engine = self.vm.engine
                    if hasattr(engine, rule_name):
                        setattr(engine, rule_name, new_value)
                        logging.info(f"EXECUTOR_RULE.{rule_name} updated")
                    elif hasattr(engine, "rules"):
                        engine.rules[rule_name] = new_value
                        logging.info(f"EXECUTOR_RULE.{rule_name} added to rules")
        
        elif category == "INSTRUCTION":
            # 动态添加指令
            if len(parts) > 1:
                instruction_name = parts[1]
                await self._add_instruction(instruction_name, new_value)
        
        elif category == "POLICY":
            # 修改自举策略
            if len(parts) > 1:
                policy_attr = parts[1]
                if hasattr(self.policy, policy_attr):
                    setattr(self.policy, policy_attr, new_value)
                    logging.info(f"POLICY.{policy_attr} updated")
        
        else:
            logging.warning(f"Unknown modification category: {category}")

    async def _add_instruction(self, instruction_name: str, definition: Any) -> None:
        """
        动态添加指令
        
        Args:
            instruction_name: 指令名称
            definition: 指令定义（可以是函数、Prompt 模板等）
        """
        logging.info(f"Adding new instruction: {instruction_name}")
        
        # 确定要修改的 VM
        vm_to_modify = self.vm.local_vm if hasattr(self.vm, "local_vm") else self.vm
        
        if not hasattr(vm_to_modify, "processor"):
            raise ValueError("VM has no processor")
        
        processor = vm_to_modify.processor
        
        # 根据定义类型添加指令
        if callable(definition):
            # 如果是可调用对象，直接包装为处理器方法
            async def new_instruction(params: dict, memory: Any) -> Any:
                return await definition(params, memory)
            
            # 添加到处理器的指令分发器
            method_name = f"_handle_{instruction_name.lower()}"
            setattr(processor, method_name, new_instruction)
            
            # 同时添加到指令集注册表（如果有）
            if hasattr(processor, "instruction_set"):
                processor.instruction_set[instruction_name] = new_instruction
            
            logging.info(f"Instruction {instruction_name} added as callable")
        
        elif isinstance(definition, dict):
            # 如果是指令定义字典
            prompt_template = definition.get("prompt", "")
            handler_type = definition.get("type", "llm")
            
            if handler_type == "llm":
                # 创建基于 LLM 的指令处理器
                async def llm_instruction(params: dict, memory: Any) -> Any:
                    # 使用 Prompt 模板
                    prompt = prompt_template.format(**params)
                    if hasattr(processor, "execute_llm"):
                        return await processor.execute_llm(prompt, memory)
                    else:
                        raise ValueError("Processor has no execute_llm method")
                
                method_name = f"_handle_{instruction_name.lower()}"
                setattr(processor, method_name, llm_instruction)
                
                if hasattr(processor, "instruction_set"):
                    processor.instruction_set[instruction_name] = llm_instruction
                
                logging.info(f"Instruction {instruction_name} added as LLM-based")
        
        else:
            raise ValueError(f"Unsupported instruction definition type: {type(definition)}")

    async def _replicate_modification(self, target: str, new_value: Any) -> None:
        """复制修改到多个节点"""
        if not hasattr(self.vm, "memory"):
            return

        # 使用分布式内存的 set (会自动哈希到对应节点或广播)
        # 如果是关键配置，我们强制广播
        if target.startswith("CONFIG"):
            parts = target.split(".")
            key = parts[1] if len(parts) > 1 else target

            # 如果 VM 是分布式 VM，使用广播
            if hasattr(self.vm, "memory") and hasattr(self.vm.memory, "get_nodes"):
                nodes = self.vm.memory.get_nodes()
                for node in nodes:
                    if hasattr(node, "node_id") and hasattr(
                        getattr(self.vm, "local_node", {}), "node_id"
                    ):
                        if node.node_id != getattr(self.vm, "local_node").node_id:  # type: ignore
                            # 实际调用远程设置
                            await self.vm.memory._remote_set(  # type: ignore
                                node, "CONFIG", key, new_value
                            )

    def get_bootstrap_history(
        self,
        limit: int = 100,
        action: Optional[str] = None,
    ) -> list[BootstrapRecord]:
        """获取自举历史"""
        records = self.records

        if action:
            records = [r for r in records if r.action == action]

        return records[-limit:]

    def get_policy(self) -> BootstrapPolicy:
        """获取自举策略"""
        return self.policy

    async def modify_policy(self, **kwargs) -> None:
        """修改自举策略"""
        for key, value in kwargs.items():
            if hasattr(self.policy, key):
                setattr(self.policy, key, value)


# =============================================================================
# 自举程序库
# =============================================================================


class BootstrapPrograms:
    """
    自举程序库

    预定义的自举程序
    """

    @staticmethod
    def create_parse_prompt_modifier(new_prompt: str) -> Any:
        """创建解析 Prompt 修改程序"""
        from intentos.semantic_vm import SemanticOpcode, create_instruction, create_program

        program = create_program(
            name="modify_parse_prompt",
            description="修改解析 Prompt",
        )

        program.add_instruction(
            create_instruction(
                SemanticOpcode.MODIFY,
                target="CONFIG",
                target_name="PARSE_PROMPT",
                value=new_prompt,
            )
        )

        return program

    @staticmethod
    def create_execute_prompt_modifier(new_prompt: str) -> Any:
        """创建执行 Prompt 修改程序"""
        from intentos.semantic_vm import SemanticOpcode, create_instruction, create_program

        program = create_program(
            name="modify_execute_prompt",
            description="修改执行 Prompt",
        )

        program.add_instruction(
            create_instruction(
                SemanticOpcode.MODIFY,
                target="CONFIG",
                target_name="EXECUTE_PROMPT",
                value=new_prompt,
            )
        )

        return program

    @staticmethod
    def create_instruction_extender(new_instructions: list[str]) -> Any:
        """创建指令集扩展程序"""
        from intentos.semantic_vm import SemanticOpcode, create_instruction, create_program

        program = create_program(
            name="extend_instruction_set",
            description="扩展指令集",
        )

        program.add_instruction(
            create_instruction(
                SemanticOpcode.DEFINE_INSTRUCTION,
                instruction_name="NEW_INSTRUCTION",
                instructions=new_instructions,
            )
        )

        return program

    @staticmethod
    def create_policy_modifier(**policy_changes) -> Any:
        """创建策略修改程序"""
        from intentos.semantic_vm import SemanticOpcode, create_instruction, create_program

        program = create_program(
            name="modify_bootstrap_policy",
            description="修改自举策略",
        )

        for key, value in policy_changes.items():
            program.add_instruction(
                create_instruction(
                    SemanticOpcode.MODIFY,
                    target="POLICY",
                    target_name=key,
                    value=value,
                )
            )

        return program

    @staticmethod
    def create_self_replicator() -> Any:
        """创建自我复制程序"""
        from intentos.distributed_semantic_vm import DistributedOpcode
        from intentos.semantic_vm import (
            create_instruction,
            create_program,
        )

        program = create_program(
            name="self_replicator",
            description="自我复制程序",
        )

        # 复制自身到其他节点
        program.add_instruction(
            create_instruction(
                DistributedOpcode.REPLICATE,
                target="PROGRAM",
                target_name="self_replicator",
            )
        )

        return program

    @staticmethod
    def create_auto_scaler(
        scale_up_threshold: float = 0.8,
        scale_down_threshold: float = 0.3,
    ) -> Any:
        """创建自动扩缩容程序"""
        from intentos.distributed_semantic_vm import DistributedOpcode
        from intentos.semantic_vm import (
            SemanticInstruction,
            SemanticOpcode,
            create_instruction,
            create_program,
        )

        program = create_program(
            name="auto_scaler",
            description="自动扩缩容",
        )

        # 监控负载
        program.add_instruction(
            create_instruction(
                SemanticOpcode.WHILE,
                condition="true",
                body=[
                    # 高负载时扩容
                    SemanticInstruction(
                        opcode=SemanticOpcode.IF,
                        condition=f"cluster_load > {scale_up_threshold}",
                        body=[
                            SemanticInstruction(
                                opcode=DistributedOpcode.SPAWN,
                                target="NODE",
                            ),
                        ],
                    ),
                    # 低负载时缩容
                    SemanticInstruction(
                        opcode=SemanticOpcode.IF,
                        condition=f"cluster_load < {scale_down_threshold}",
                        body=[
                            SemanticInstruction(
                                opcode=SemanticOpcode.DELETE,
                                target="NODE",
                            ),
                        ],
                    ),
                    SemanticInstruction(
                        opcode=SemanticOpcode.SET,
                        parameters={"name": "_", "value": "sleep(60)"},
                    ),
                ],
            )
        )

        return program


# =============================================================================
# Self-Bootstrap 验证器
# =============================================================================


class BootstrapValidator:
    """
    Self-Bootstrap 验证器

    验证自修改的有效性
    """

    def __init__(self, executor: SelfBootstrapExecutor):
        self.executor = executor

    async def validate_modification(
        self,
        record: BootstrapRecord,
    ) -> dict[str, Any]:
        """验证修改"""
        result: dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
        }

        # 1. 验证修改格式
        if not record.action:
            result["valid"] = False
            result["errors"].append("缺少 action")

        if not record.target:
            result["valid"] = False
            result["errors"].append("缺少 target")

        # 2. 验证修改权限
        if self.executor._requires_approval(record.action):
            if not record.approved_by:
                result["valid"] = False
                result["errors"].append("需要审批")

        # 3. 验证修改速率
        if not self.executor._check_rate_limit():
            result["valid"] = False
            result["errors"].append("超过速率限制")

        # 4. 验证修改内容
        if record.new_value is None:
            result["valid"] = False
            result["errors"].append("新值不能为空")

        # 5. 警告：危险操作
        dangerous_actions = ["delete_all", "disable_self_bootstrap"]
        if record.action in dangerous_actions:
            result["warnings"].append(f"危险操作：{record.action}")

        return result

    async def validate_bootstrap_capability(self) -> dict[str, Any]:
        """验证 Self-Bootstrap 能力"""
        result: dict[str, Any] = {
            "capable": True,
            "capabilities": {
                "modify_parse_prompt": False,
                "modify_execute_prompt": False,
                "extend_instructions": False,
                "modify_policy": False,
                "self_replicate": False,
                "auto_scale": False,
            },
            "missing": [],
        }

        # 检查各项能力
        if hasattr(self.executor.vm, "memory"):
            result["capabilities"]["modify_parse_prompt"] = True
            result["capabilities"]["modify_execute_prompt"] = True
            result["capabilities"]["modify_policy"] = True

        if hasattr(self.executor.vm, "processor"):
            result["capabilities"]["extend_instructions"] = True

        if hasattr(self.executor.vm, "add_node"):
            result["capabilities"]["self_replicate"] = True
            result["capabilities"]["auto_scale"] = True

        # 列出缺失能力
        for cap, capable in result["capabilities"].items():
            if not capable:
                result["missing"].append(cap)

        if result["missing"]:
            result["capable"] = False

        return result


# =============================================================================
# 便捷函数
# =============================================================================


def create_bootstrap_executor(
    semantic_vm: Any,
    policy: Optional[BootstrapPolicy] = None,
) -> SelfBootstrapExecutor:
    """创建 Self-Bootstrap 执行器"""
    return SelfBootstrapExecutor(semantic_vm, policy)


def create_bootstrap_validator(
    executor: SelfBootstrapExecutor,
) -> BootstrapValidator:
    """创建 Self-Bootstrap 验证器"""
    return BootstrapValidator(executor)


def create_bootstrap_policy(**kwargs) -> BootstrapPolicy:
    """创建自举策略"""
    return BootstrapPolicy(**kwargs)
