"""
Self-Modifying OS Module Tests

测试自修改操作系统模块：组件管理、动态修改、版本控制
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from intentos.bootstrap.self_modifying_os import (
    OSComponent,
    SelfModifyingOS,
)


class TestOSComponent:
    """测试 OS 组件"""

    def test_create_component_minimal(self):
        """创建最小组件"""
        component = OSComponent(
            name="test_component",
            component_type="instruction",
            module="intentos.test",
            class_name="TestComponent",
            code="def test(): pass"
        )

        assert component.name == "test_component"
        assert component.component_type == "instruction"
        assert component.module == "intentos.test"
        assert component.class_name == "TestComponent"
        assert component.code == "def test(): pass"
        assert component.version == "1.0.0"
        assert component.description == ""
        assert component.modified_at is None
        assert component.modified_by == "system"

    def test_create_component_full(self):
        """创建完整组件"""
        now = datetime.now()
        component = OSComponent(
            name="advanced_component",
            component_type="compiler_rule",
            module="intentos.compiler",
            class_name="AdvancedRule",
            code="class AdvancedRule: pass",
            version="2.0.0",
            description="Advanced compiler rule",
            modified_at=now,
            modified_by="admin"
        )

        assert component.name == "advanced_component"
        assert component.version == "2.0.0"
        assert component.description == "Advanced compiler rule"
        assert component.modified_at == now
        assert component.modified_by == "admin"

    def test_component_to_dict(self):
        """组件转换为字典"""
        component = OSComponent(
            name="dict_component",
            component_type="executor_rule",
            module="intentos.engine",
            class_name="ExecutorRule",
            code="rule = {}",
            version="1.5.0"
        )

        data = component.to_dict()

        assert data["name"] == "dict_component"
        assert data["component_type"] == "executor_rule"
        assert data["module"] == "intentos.engine"
        assert data["class_name"] == "ExecutorRule"
        assert data["code"] == "rule = {}"
        assert data["version"] == "1.5.0"

    def test_component_to_dict_with_timestamp(self):
        """带时间戳的字典转换"""
        now = datetime.now()
        component = OSComponent(
            name="timestamped_component",
            component_type="instruction",
            module="intentos.test",
            class_name="Test",
            code="pass",
            modified_at=now
        )

        data = component.to_dict()

        assert data["modified_at"] == now.isoformat()

    def test_component_to_dict_without_timestamp(self):
        """无时间戳的字典转换"""
        component = OSComponent(
            name="no_timestamp_component",
            component_type="instruction",
            module="intentos.test",
            class_name="Test",
            code="pass"
        )

        data = component.to_dict()

        assert data["modified_at"] is None


class TestSelfModifyingOSInitialization:
    """测试自修改 OS 初始化"""

    def test_init_empty(self):
        """初始化空 OS"""
        os = SelfModifyingOS()

        assert os.components == {}
        assert os.instructions == {}
        assert os.compiler_rules == {}
        assert os.executor_rules == {}
        assert os.modification_history == []
        assert os.meta_intent_executor is None

    def test_set_meta_intent_executor(self):
        """设置元意图执行器"""
        os = SelfModifyingOS()
        mock_executor = MagicMock()
        os.set_meta_intent_executor(mock_executor)

        assert os.meta_intent_executor is mock_executor


class TestSelfModifyingOSDefineInstruction:
    """测试定义指令"""

    def test_define_instruction(self):
        """定义新指令"""
        os = SelfModifyingOS()

        def test_instruction():
            return "test"

        component = os.define_instruction(
            name="test_instr",
            handler=test_instruction,
            description="Test instruction"
        )

        assert "test_instr" in os.instructions
        assert "test_instr" in os.components
        assert component.name == "test_instr"
        assert component.component_type == "instruction"

    def test_define_instruction_with_params(self):
        """定义带参数的指令"""
        os = SelfModifyingOS()

        def add(x, y):
            return x + y

        component = os.define_instruction(
            name="add",
            handler=add,
            description="Add two numbers"
        )

        assert os.instructions["add"](2, 3) == 5
        assert component.description == "Add two numbers"

    def test_define_instruction_records_history(self):
        """定义指令记录历史"""
        os = SelfModifyingOS()

        def test_instr():
            pass

        os.define_instruction("test", test_instr)

        assert len(os.modification_history) == 1
        assert os.modification_history[0]["action"] == "define_instruction"


class TestSelfModifyingOSModifyCompilerRule:
    """测试修改编译器规则"""

    def test_modify_compiler_rule(self):
        """修改编译器规则"""
        os = SelfModifyingOS()
        rule = {"pattern": "test", "action": "parse"}

        component = os.modify_compiler_rule("test_rule", rule)

        assert os.compiler_rules["test_rule"] == rule
        assert component.name == "test_rule"
        assert component.component_type == "compiler_rule"

    def test_modify_compiler_rule_records_history(self):
        """修改编译器规则记录历史"""
        os = SelfModifyingOS()
        rule = {"pattern": "test", "action": "parse"}

        os.modify_compiler_rule("test_rule", rule)

        assert len(os.modification_history) == 1
        assert os.modification_history[0]["action"] == "modify_compiler_rule"


class TestSelfModifyingOSModifyExecutorRule:
    """测试修改执行器规则"""

    def test_modify_executor_rule(self):
        """修改执行器规则"""
        os = SelfModifyingOS()
        rule = {"condition": "x > 0", "action": "execute"}

        component = os.modify_executor_rule("test_exec_rule", rule)

        assert os.executor_rules["test_exec_rule"] == rule
        assert component.name == "test_exec_rule"
        assert component.component_type == "executor_rule"

    def test_modify_executor_rule_records_history(self):
        """修改执行器规则记录历史"""
        os = SelfModifyingOS()
        rule = {"condition": "x > 0", "action": "execute"}

        os.modify_executor_rule("test_exec_rule", rule)

        assert len(os.modification_history) == 1
        assert os.modification_history[0]["action"] == "modify_executor_rule"


class TestSelfModifyingOSMultipleModifications:
    """测试多次修改"""

    def test_multiple_instructions(self):
        """定义多个指令"""
        os = SelfModifyingOS()

        for i in range(3):
            def make_instr(n):
                def instr():
                    return n
                return instr

            os.define_instruction(f"instr_{i}", make_instr(i))

        assert len(os.instructions) == 3
        assert len(os.components) == 3
        assert len(os.modification_history) == 3

    def test_mixed_modifications(self):
        """混合修改"""
        os = SelfModifyingOS()

        # 定义指令
        os.define_instruction("test", lambda: None)

        # 修改编译器规则
        os.modify_compiler_rule("rule1", {})

        # 修改执行器规则
        os.modify_executor_rule("exec_rule1", {})

        assert len(os.modification_history) == 3
        actions = [h["action"] for h in os.modification_history]
        assert "define_instruction" in actions
        assert "modify_compiler_rule" in actions
        assert "modify_executor_rule" in actions


class TestSelfModifyingOSComponentTypes:
    """测试自修改 OS 组件类型"""

    def test_instruction_component(self):
        """指令组件"""
        component = OSComponent(
            name="instr_component",
            component_type="instruction",
            module="intentos.test",
            class_name="Test",
            code="def instr(): pass"
        )

        assert component.component_type == "instruction"

    def test_compiler_rule_component(self):
        """编译器规则组件"""
        component = OSComponent(
            name="rule_component",
            component_type="compiler_rule",
            module="intentos.compiler",
            class_name="Rule",
            code="rule = {}"
        )

        assert component.component_type == "compiler_rule"

    def test_executor_rule_component(self):
        """执行器规则组件"""
        component = OSComponent(
            name="exec_rule_component",
            component_type="executor_rule",
            module="intentos.engine",
            class_name="ExecRule",
            code="exec_rule = {}"
        )

        assert component.component_type == "executor_rule"

    def test_protocol_component(self):
        """协议组件"""
        component = OSComponent(
            name="protocol_component",
            component_type="protocol",
            module="intentos.distributed",
            class_name="Protocol",
            code="protocol = {}"
        )

        assert component.component_type == "protocol"


class TestSelfModifyingOSModificationHistory:
    """测试修改历史"""

    def test_history_timestamp(self):
        """历史时间戳"""
        os = SelfModifyingOS()
        os.define_instruction("test", lambda: None)

        history_entry = os.modification_history[0]
        assert "timestamp" in history_entry
        assert "action" in history_entry
        assert "target" in history_entry

    def test_history_status(self):
        """历史状态"""
        os = SelfModifyingOS()
        os.define_instruction("test", lambda: None)

        history_entry = os.modification_history[0]
        assert history_entry["status"] == "completed"


class TestSelfModifyingOSVersioning:
    """测试版本控制"""

    def test_component_version(self):
        """组件版本"""
        component = OSComponent(
            name="versioned_component",
            component_type="instruction",
            module="test",
            class_name="Test",
            code="pass",
            version="1.0.0"
        )

        assert component.version == "1.0.0"

    def test_component_version_formats(self):
        """组件版本格式"""
        versions = ["1.0.0", "2.1.0", "10.5.3", "0.1.0"]

        for version in versions:
            component = OSComponent(
                name=f"component_{version}",
                component_type="instruction",
                module="test",
                class_name="Test",
                code="pass",
                version=version
            )
            assert component.version == version
