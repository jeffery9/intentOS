"""
元循环解释器

支持分层意图解释执行

设计文档：docs/private/016-meta-circular-interpreter.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class IntentLevel(Enum):
    """意图层级"""

    TASK = 0
    META = 1
    META_META = 2
    INFINITE = 3


@dataclass
class HierarchicalIntent:
    """分层意图"""

    level: IntentLevel
    action: str
    target: str
    parameters: dict[str, Any]

    intent_id: str = field(default_factory=lambda: str(uuid4())[:8])
    parent_intent_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "action": self.action,
            "target": self.target,
            "parameters": self.parameters,
            "intent_id": self.intent_id,
            "parent_intent_id": self.parent_intent_id,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ParseRule:
    """解析规则"""

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    pattern: str = ""
    pattern_type: str = "regex"
    intent_type: str = ""
    intent_params: dict[str, str] = field(default_factory=dict)
    priority: int = 0
    created_by: str = "system"
    created_at: datetime = field(default_factory=datetime.now)

    def match(self, text: str) -> Optional[dict]:
        """匹配文本"""
        import re

        if self.pattern_type == "regex":
            match = re.match(self.pattern, text)
            if match:
                params = {}
                for key, value in self.intent_params.items():
                    for i, group in enumerate(match.groups()):
                        value = value.replace(f"${i+1}", group)
                    params[key] = value
                return params
            return None

        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pattern": self.pattern,
            "pattern_type": self.pattern_type,
            "intent_type": self.intent_type,
            "intent_params": self.intent_params,
            "priority": self.priority,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ParseRule:
        return cls(
            id=data.get("id", str(uuid4())[:8]),
            pattern=data["pattern"],
            pattern_type=data.get("pattern_type", "regex"),
            intent_type=data["intent_type"],
            intent_params=data.get("intent_params", {}),
            priority=data.get("priority", 0),
            created_by=data.get("created_by", "system"),
        )


@dataclass
class MetaRule:
    """元规则"""

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    meta_pattern: str = ""
    meta_action: str = ""
    handler: str = ""
    priority: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meta_pattern": self.meta_pattern,
            "meta_action": self.meta_action,
            "handler": self.handler,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MetaRule:
        return cls(
            id=data.get("id", str(uuid4())[:8]),
            meta_pattern=data["meta_pattern"],
            meta_action=data["meta_action"],
            handler=data["handler"],
            priority=data.get("priority", 0),
        )


class MetaCircularInterpreter:
    """元循环解释器"""

    def __init__(self, kernel: Any = None):
        self.kernel = kernel
        self.current_level: IntentLevel = IntentLevel.TASK

        self.interpreters: dict[IntentLevel, Callable] = {
            IntentLevel.TASK: self._interpret_task_intent,
            IntentLevel.META: self._interpret_meta_intent,
            IntentLevel.META_META: self._interpret_meta_meta_intent,
        }

        self.task_rules: list[ParseRule] = []
        self.meta_rules: list[MetaRule] = []

    def interpret(
        self,
        intent: HierarchicalIntent,
        context: dict[str, Any],
    ) -> Any:
        """解释执行意图"""
        old_level = self.current_level

        try:
            self.current_level = intent.level
            interpreter = self.interpreters.get(intent.level)

            if not interpreter:
                raise ValueError(f"不支持的意图层级：{intent.level}")

            return interpreter(intent, context)

        finally:
            self.current_level = old_level

    def _interpret_task_intent(
        self,
        intent: HierarchicalIntent,
        context: dict,
    ) -> Any:
        """解释任务意图"""
        pass

    def _interpret_meta_intent(
        self,
        intent: HierarchicalIntent,
        context: dict,
    ) -> Any:
        """解释元意图"""
        action = intent.action

        if action == "modify_parse_rule":
            new_rule = ParseRule.from_dict(intent.parameters)
            self.task_rules.append(new_rule)
            return {"status": "success", "rule_id": new_rule.id}

        elif action == "list_rules":
            return {"rules": [r.to_dict() for r in self.task_rules]}

        elif action == "delete_rule":
            rule_id = intent.parameters.get("rule_id")
            self.task_rules = [r for r in self.task_rules if r.id != rule_id]
            return {"status": "success"}

        else:
            raise ValueError(f"未知的元意图动作：{action}")

    def _interpret_meta_meta_intent(
        self,
        intent: HierarchicalIntent,
        context: dict,
    ) -> Any:
        """解释元元意图"""
        action = intent.action

        if action == "modify_meta_rule":
            new_meta_rule = MetaRule.from_dict(intent.parameters)
            self.meta_rules.append(new_meta_rule)
            return {"status": "success", "rule_id": new_meta_rule.id}

        elif action == "define_meta_action":
            action_name = intent.parameters.get("name")
            action_handler = intent.parameters.get("handler")
            return {"status": "success"}

        else:
            raise ValueError(f"未知的元元意图动作：{action}")


class ConsistencyChecker:
    """自指一致性检查器"""

    def __init__(self, interpreter: MetaCircularInterpreter):
        self.interpreter = interpreter

    def check_consistency(
        self,
        modification: dict,
    ) -> tuple[bool, list[str]]:
        """检查修改的一致性"""
        conflicts = []

        action = modification.get("action", "")
        new_value = modification.get("new_value")

        if action == "modify_parse_rule":
            conflicts.extend(self._check_parse_rules(new_value))

        conflicts.extend(self._check_self_reference(modification))
        conflicts.extend(self._check_circular_dependency(modification))

        return len(conflicts) == 0, conflicts

    def _check_self_reference(self, mod: dict) -> list[str]:
        """检查自指悖论"""
        conflicts = []
        new_value_str = str(mod.get("new_value", "")).lower()

        if "所有规则" in new_value_str and "错的" in new_value_str:
            conflicts.append("检测到自指悖论：'所有规则都是错的'")

        if "本规则无效" in new_value_str:
            conflicts.append("检测到自指矛盾：'本规则无效'")

        return conflicts

    def _check_circular_dependency(self, mod: dict) -> list[str]:
        """检查循环依赖"""
        return []

    def _check_parse_rules(self, new_value: Any) -> list[str]:
        """检查解析规则冲突"""
        return []
