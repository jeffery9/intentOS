"""
自修改操作系统 (Self-Modifying OS)

真正的 Self-Bootstrap：修改运行中的 OS 本体
1. 动态添加新指令到语义 VM
2. 修改编译器的解析规则
3. 修改执行器的执行逻辑
4. 修改分布式协议
"""

from __future__ import annotations
import logging

import importlib
import inspect
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Type

from .meta_intent_executor import MetaIntent, MetaIntentType, MetaIntentExecutor


@dataclass
class OSComponent:
    """
    OS 组件
    
    可被自我修改的系统组件
    """
    name: str
    component_type: str  # instruction / compiler_rule / executor_rule / protocol
    module: str
    class_name: str
    code: str
    version: str = "1.0.0"
    description: str = ""
    modified_at: Optional[datetime] = None
    modified_by: str = "system"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "component_type": self.component_type,
            "module": self.module,
            "class_name": self.class_name,
            "code": self.code,
            "version": self.version,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "modified_by": self.modified_by,
        }


class SelfModifyingOS:
    """
    自修改操作系统
    
    真正的 Self-Bootstrap：修改运行中的 OS 本体
    """
    
    def __init__(self):
        # 已注册的组件
        self.components: dict[str, OSComponent] = {}
        
        # 指令注册表
        self.instructions: dict[str, Callable] = {}
        
        # 编译器规则
        self.compiler_rules: dict[str, Any] = {}
        
        # 执行器规则
        self.executor_rules: dict[str, Any] = {}
        
        # 修改历史
        self.modification_history: list[dict] = []
        
        # 注册元指令执行器
        self.meta_intent_executor: Optional[MetaIntentExecutor] = None
    
    def set_meta_intent_executor(self, executor: MetaIntentExecutor) -> None:
        """设置元意图执行器"""
        self.meta_intent_executor = executor
        
        # 注册自我修改的元意图类型
        executor._handlers[MetaIntentType.DEFINE_INSTRUCTION] = self._execute_define_instruction
        executor._handlers[MetaIntentType.MODIFY_COMPILER_RULE] = self._execute_modify_compiler_rule
        executor._handlers[MetaIntentType.MODIFY_EXECUTOR_RULE] = self._execute_modify_executor_rule
        executor._handlers[MetaIntentType.MODIFY_OS_COMPONENT] = self._execute_modify_os_component
    
    # =========================================================================
    # 核心自我修改能力
    # =========================================================================
    
    def define_instruction(
        self,
        name: str,
        handler: Callable,
        description: str = "",
    ) -> OSComponent:
        """
        定义新指令
        
        Args:
            name: 指令名称
            handler: 指令处理函数
            description: 指令描述
        """
        """
        定义新指令
        
        动态添加新指令到语义 VM
        
        Args:
            name: 指令名称（如 "AR_RENDER"）
            handler: 指令处理函数
            description: 指令描述
            
        Returns:
            注册的组件
        """
        # 注册指令
        self.instructions[name] = handler
        
        # 记录组件
        component = OSComponent(
            name=name,
            component_type="instruction",
            module=handler.__module__,
            class_name=handler.__qualname__,
            code=str(handler),
            description=description,
            modified_at=datetime.now(),
            modified_by="system",
        )
        
        self.components[name] = component
        self.modification_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "define_instruction",
            "target": name,
            "status": "completed",
        })
        
        return component
    
    def modify_compiler_rule(
        self,
        rule_name: str,
        new_rule: Any,
    ) -> OSComponent:
        """
        修改编译器规则
        
        Args:
            rule_name: 规则名称（如 "intent_parse_prompt"）
            new_rule: 新规则
        """
        self.compiler_rules[rule_name] = new_rule
        
        component = OSComponent(
            name=rule_name,
            component_type="compiler_rule",
            module="intentos.compiler",
            class_name=rule_name,
            code=str(new_rule),
            modified_at=datetime.now(),
            modified_by="system",
        )
        
        self.components[rule_name] = component
        self.modification_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "modify_compiler_rule",
            "target": rule_name,
            "status": "completed",
        })
        
        return component
    
    def modify_executor_rule(
        self,
        rule_name: str,
        new_rule: Any,
    ) -> OSComponent:
        """
        修改执行器规则
        
        Args:
            rule_name: 规则名称
            new_rule: 新规则
        """
        self.executor_rules[rule_name] = new_rule
        
        component = OSComponent(
            name=rule_name,
            component_type="executor_rule",
            module="intentos.engine",
            class_name=rule_name,
            code=str(new_rule),
            modified_at=datetime.now(),
            modified_by="system",
        )
        
        self.components[rule_name] = component
        self.modification_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "modify_executor_rule",
            "target": rule_name,
            "status": "completed",
        })
        
        return component
    
    def modify_os_component(
        self,
        component_name: str,
        new_code: str,
        component_type: str,
    ) -> OSComponent:
        """
        修改 OS 组件（高级操作）
        
        可以直接修改运行中的 OS 代码
        
        Args:
            component_name: 组件名称
            new_code: 新代码（Python 源代码）
            component_type: 组件类型
        """
        # 在实际系统中，这里会：
        # 1. 编译新代码
        # 2. 热替换模块
        # 3. 重新加载
        
        # 简化版本：记录修改
        component = OSComponent(
            name=component_name,
            component_type=component_type,
            module="intentos",
            class_name=component_name,
            code=new_code,
            modified_at=datetime.now(),
            modified_by="system",
        )
        
        self.components[component_name] = component
        self.modification_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "modify_os_component",
            "target": component_name,
            "status": "completed",
        })
        
        return component
    
    # =========================================================================
    # 元意图执行器
    # =========================================================================
    
    async def _execute_define_instruction(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """执行定义指令元意图"""
        name = meta_intent.params.get("name", meta_intent.target)
        code = meta_intent.params.get("code")
        description = meta_intent.params.get("description", "")
        
        # 动态创建指令处理函数
        # 在实际系统中，这里会执行代码并创建函数
        def handler(**kwargs):
            # 动态生成的指令处理逻辑
            return {"status": "executed", "instruction": name}
        
        # 注册指令
        self.define_instruction(name, handler, description)
        
        return {
            "instruction": name,
            "status": "registered",
        }
    
    async def _execute_modify_compiler_rule(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """执行修改编译器规则元意图"""
        rule_name = meta_intent.target
        new_rule = meta_intent.params.get("rule")
        
        self.modify_compiler_rule(rule_name, new_rule)
        
        return {
            "rule": rule_name,
            "status": "modified",
        }
    
    async def _execute_modify_executor_rule(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """执行修改执行器规则元意图"""
        rule_name = meta_intent.target
        new_rule = meta_intent.params.get("rule")
        
        self.modify_executor_rule(rule_name, new_rule)
        
        return {
            "rule": rule_name,
            "status": "modified",
        }
    
    async def _execute_modify_os_component(self, meta_intent: MetaIntent) -> dict[str, Any]:
        """执行修改 OS 组件元意图"""
        component_name = meta_intent.target
        new_code = meta_intent.params.get("code")
        component_type = meta_intent.params.get("type", "module")
        
        self.modify_os_component(component_name, new_code, component_type)
        
        return {
            "component": component_name,
            "status": "modified",
        }
    
    # =========================================================================
    # 查询和审计
    # =========================================================================
    
    def get_component(self, name: str) -> Optional[OSComponent]:
        """获取组件"""
        return self.components.get(name)
    
    def list_components(
        self,
        component_type: Optional[str] = None,
    ) -> list[OSComponent]:
        """列出组件"""
        components = list(self.components.values())
        
        if component_type:
            components = [c for c in components if c.component_type == component_type]
        
        return components
    
    def get_modification_history(
        self,
        time_range: str = "24h",
        action_type: Optional[str] = None,
    ) -> list[dict]:
        """获取修改历史"""
        history = self.modification_history
        
        if action_type:
            history = [h for h in history if h["action"] == action_type]
        
        return history
    
    def get_statistics(self) -> dict[str, Any]:
        """获取统计"""
        return {
            "total_components": len(self.components),
            "instructions": len(self.instructions),
            "compiler_rules": len(self.compiler_rules),
            "executor_rules": len(self.executor_rules),
            "total_modifications": len(self.modification_history),
            "by_type": self._count_by_type(),
        }
    
    def _count_by_type(self) -> dict[str, int]:
        """按类型统计"""
        counts: dict[str, int] = {}
        for component in self.components.values():
            t = component.component_type
            counts[t] = counts.get(t, 0) + 1
        return counts


# =============================================================================
# 工厂函数
# =============================================================================


def create_self_modifying_os() -> SelfModifyingOS:
    """创建自修改 OS"""
    return SelfModifyingOS()


# =============================================================================
# 使用示例
# =============================================================================


async def demo_self_modifying_os():
    """演示自修改 OS"""
    from .meta_intent_executor import create_meta_intent_executor
    from intentos.apps import IntentPackageRegistry
    
    # 1. 创建自修改 OS
    os = create_self_modifying_os()
    
    # 2. 初始状态
    print(f"初始指令数：{len(os.instructions)}")
    
    # 3. 动态添加新指令
    def ar_render_handler(data: list, style: str = "bar") -> str:
        """AR 渲染指令"""
        return f"AR scene rendered: {len(data)} items, style={style}"
    
    os.define_instruction("AR_RENDER", ar_render_handler, "AR 渲染指令")
    
    print(f"添加后指令数：{len(os.instructions)}")
    
    # 4. 通过元指令添加
    registry = IntentPackageRegistry()
    executor = create_meta_intent_executor(registry=registry)
    os.set_meta_intent_executor(executor)
    
    # 5. 执行元指令添加新指令
    meta_intent = MetaIntent(
        type=MetaIntentType.DEFINE_INSTRUCTION,
        target="VR_RENDER",
        params={
            "name": "VR_RENDER",
            "description": "VR 渲染指令",
            "code": "def vr_render(...): ...",
        },
    )
    
    result = await executor.execute(meta_intent)
    
    print(f"通过元指令添加后指令数：{len(os.instructions)}")
    
    # 6. 查看修改历史
    history = os.get_modification_history()
    print(f"修改历史：{len(history)} 条")
    
    # 7. 查看统计
    stats = os.get_statistics()
    print(f"统计：{stats}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_self_modifying_os())
