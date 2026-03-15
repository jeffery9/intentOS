"""
意图模板

定义意图的匹配规则和处理方式
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class IntentTemplate:
    """
    意图模板
    
    定义如何匹配用户输入并路由到对应的处理函数
    """
    
    # 基本信息
    id: str
    name: str
    description: str
    
    # 匹配规则
    patterns: list[str] = field(default_factory=list)  # 正则表达式
    keywords: list[str] = field(default_factory=list)  # 关键词
    exact_matches: list[str] = field(default_factory=list)  # 精确匹配
    
    # 处理
    handler: Optional[Callable] = None  # 处理函数
    handler_name: str = ""  # 处理函数名称（用于延迟绑定）
    
    # 参数定义
    params_schema: dict[str, Any] = field(default_factory=dict)
    
    # 分类和标签
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    
    # 优先级 (数字越大优先级越高)
    priority: int = 0
    
    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def match(self, text: str) -> tuple[bool, dict[str, Any]]:
        """
        匹配文本
        
        Args:
            text: 用户输入文本
        
        Returns:
            (是否匹配，提取的参数)
        """
        # 1. 精确匹配
        for exact in self.exact_matches:
            if text.strip().lower() == exact.lower():
                return True, self._extract_params(text)
        
        # 2. 关键词匹配
        for keyword in self.keywords:
            if keyword.lower() in text.lower():
                return True, self._extract_params(text)
        
        # 3. 正则匹配
        for pattern in self.patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                params = self._extract_params(text)
                params.update(match.groupdict())
                return True, params
        
        return False, {}
    
    def _extract_params(self, text: str) -> dict[str, Any]:
        """提取参数"""
        params: dict[str, Any] = {"raw_text": text}

        # 提取时间
        time_patterns: list[tuple[str, str]] = [
            (r'(\d{1,2}[点时])', 'time'),
            (r'(\d{1,2}:\d{2})', 'time_24h'),
            (r'(今天 | 明天 | 后天 | 下周)', 'relative_date'),
        ]
        for pattern, name in time_patterns:
            match = re.search(pattern, text)
            if match:
                params[name] = match.group(1)

        # 提取数字
        numbers: list[str] = re.findall(r'\d+', text)
        if numbers:
            params['numbers'] = numbers

        return params
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "patterns": self.patterns,
            "keywords": self.keywords,
            "category": self.category,
            "tags": self.tags,
            "priority": self.priority,
        }


class TemplateRegistry:
    """
    意图模板注册表
    """
    
    _instance: Optional["TemplateRegistry"] = None
    _templates: dict[str, IntentTemplate] = {}
    _templates_by_category: dict[str, list[str]] = {}
    
    def __new__(cls) -> "TemplateRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, template: IntentTemplate) -> bool:
        """注册模板"""
        if template.id in self._templates:
            return False
        
        self._templates[template.id] = template
        
        # 按分类索引
        if template.category not in self._templates_by_category:
            self._templates_by_category[template.category] = []
        self._templates_by_category[template.category].append(template.id)
        
        return True
    
    def get_template(self, template_id: str) -> Optional[IntentTemplate]:
        """获取模板"""
        return self._templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> list[IntentTemplate]:
        """列出模板"""
        if category:
            ids = self._templates_by_category.get(category, [])
            return [self._templates[id] for id in ids if id in self._templates]
        return list(self._templates.values())
    
    def match_intent(self, text: str) -> Optional[IntentTemplate]:
        """匹配意图"""
        matched_templates = []
        
        for template in self._templates.values():
            matched, _ = template.match(text)
            if matched:
                matched_templates.append(template)
        
        if not matched_templates:
            return None
        
        # 返回优先级最高的
        return max(matched_templates, key=lambda t: t.priority)
    
    def search_templates(self, query: str) -> list[IntentTemplate]:
        """搜索模板"""
        query_lower = query.lower()
        return [
            t for t in self._templates.values()
            if (query_lower in t.name.lower() or
                query_lower in t.description.lower() or
                query_lower in t.category.lower() or
                any(query_lower in tag.lower() for tag in t.tags))
        ]
    
    def get_all_templates(self) -> dict[str, IntentTemplate]:
        """获取所有模板"""
        return self._templates.copy()
    
    def get_categories(self) -> list[str]:
        """获取所有分类"""
        return list(self._templates_by_category.keys())
