# -*- coding: utf-8 -*-
"""
IntentOS Skill Layer Models

技能数据模型：Skill, Workflow, SkillStep 等
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class SkillLevel(Enum):
    """技能等级"""
    BEGINNER = "beginner"      # 初级
    INTERMEDIATE = "intermediate"  # 中级
    ADVANCED = "advanced"      # 高级
    EXPERT = "expert"          # 专家


@dataclass
class SkillParam:
    """技能参数"""
    name: str
    type: str  # string, number, boolean, array, object
    description: str = ""
    required: bool = False
    default: Any = None
    enum: Optional[list[str]] = None  # 枚举值
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "enum": self.enum,
        }


@dataclass
class SkillStep:
    """技能步骤"""
    name: str
    action: str  # 动作类型：query, execute, analyze, generate 等
    description: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    output_var: Optional[str] = None  # 输出绑定变量
    condition: Optional[str] = None  # 执行条件
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "action": self.action,
            "description": self.description,
            "params": self.params,
            "output_var": self.output_var,
            "condition": self.condition,
        }


@dataclass
class SkillTrigger:
    """技能触发器"""
    # 关键词触发
    keywords: list[str] = field(default_factory=list)
    # 意图模式匹配
    intent_pattern: Optional[str] = None
    # 文件类型触发
    file_extensions: list[str] = field(default_factory=list)
    # 自动触发（满足条件时自动）
    auto_trigger: bool = False
    # 置信度阈值
    confidence_threshold: float = 0.7
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "keywords": self.keywords,
            "intent_pattern": self.intent_pattern,
            "file_extensions": self.file_extensions,
            "auto_trigger": self.auto_trigger,
            "confidence_threshold": self.confidence_threshold,
        }


@dataclass
class Workflow:
    """工作流"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    steps: list[SkillStep] = field(default_factory=list)
    params: list[SkillParam] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    source_session_id: Optional[str] = None  # 来源会话 ID
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "params": [p.to_dict() for p in self.params],
            "created_at": self.created_at.isoformat(),
            "source_session_id": self.source_session_id,
        }


@dataclass
class Skill:
    """
    技能
    
    从工作流提炼而来，可复用的能力单元
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    
    # 触发条件
    trigger: SkillTrigger = field(default_factory=SkillTrigger)
    
    # 技能步骤
    steps: list[SkillStep] = field(default_factory=list)
    
    # 参数定义
    params: list[SkillParam] = field(default_factory=list)
    
    # 等级和标签
    level: SkillLevel = SkillLevel.INTERMEDIATE
    tags: list[str] = field(default_factory=list)
    
    # 来源信息
    source_workflow_id: Optional[str] = None
    source_session_id: Optional[str] = None
    created_from: str = "manual"  # manual, skillify, import
    
    # 使用统计
    usage_count: int = 0
    success_rate: float = 0.0
    last_used_at: Optional[datetime] = None
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "trigger": self.trigger.to_dict(),
            "steps": [s.to_dict() for s in self.steps],
            "params": [p.to_dict() for p in self.params],
            "level": self.level.value,
            "tags": self.tags,
            "source_workflow_id": self.source_workflow_id,
            "source_session_id": self.source_session_id,
            "created_from": self.created_from,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def to_yaml(self) -> str:
        """导出为 YAML 格式（用于保存为技能文件）"""
        import yaml
        
        data = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "level": self.level.value,
            "tags": self.tags,
            "trigger": self.trigger.to_dict(),
            "params": [p.to_dict() for p in self.params],
            "steps": [s.to_dict() for s in self.steps],
        }
        
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Skill":
        """从字典创建"""
        trigger_data = data.get("trigger", {})
        trigger = SkillTrigger(
            keywords=trigger_data.get("keywords", []),
            intent_pattern=trigger_data.get("intent_pattern"),
            file_extensions=trigger_data.get("file_extensions", []),
            auto_trigger=trigger_data.get("auto_trigger", False),
            confidence_threshold=trigger_data.get("confidence_threshold", 0.7),
        )
        
        steps = [
            SkillStep(
                name=s.get("name", ""),
                action=s.get("action", ""),
                description=s.get("description", ""),
                params=s.get("params", {}),
                output_var=s.get("output_var"),
                condition=s.get("condition"),
            )
            for s in data.get("steps", [])
        ]
        
        params = [
            SkillParam(
                name=p.get("name", ""),
                type=p.get("type", "string"),
                description=p.get("description", ""),
                required=p.get("required", False),
                default=p.get("default"),
                enum=p.get("enum"),
            )
            for p in data.get("params", [])
        ]
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            trigger=trigger,
            steps=steps,
            params=params,
            level=SkillLevel(data.get("level", "intermediate")),
            tags=data.get("tags", []),
            source_workflow_id=data.get("source_workflow_id"),
            source_session_id=data.get("source_session_id"),
            created_from=data.get("created_from", "manual"),
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 0.0),
        )
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> "Skill":
        """从 YAML 字符串创建"""
        import yaml
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
