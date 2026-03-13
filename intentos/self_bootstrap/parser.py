"""
元意图解析器

将自然语言解析为元意图，或从 PEF 文件加载元意图
"""

from __future__ import annotations
import re
import json
from typing import Optional, Any

# 本地导入
from . import MetaIntent, MetaAction, TargetType


class MetaIntentParser:
    """
    元意图解析器
    
    支持三种输入方式:
    1. 自然语言："创建一个名为 sales_analysis 的意图模板"
    2. PEF 文件内容 (YAML/JSON)
    3. MetaIntent 字典
    """
    
    # 动作关键词映射
    ACTION_KEYWORDS = {
        "创建": MetaAction.CREATE,
        "新建": MetaAction.CREATE,
        "建立": MetaAction.CREATE,
        "create": MetaAction.CREATE,
        
        "修改": MetaAction.MODIFY,
        "更新": MetaAction.MODIFY,
        "更改": MetaAction.MODIFY,
        "modify": MetaAction.MODIFY,
        "update": MetaAction.MODIFY,
        
        "删除": MetaAction.DELETE,
        "移除": MetaAction.DELETE,
        "delete": MetaAction.DELETE,
        "remove": MetaAction.DELETE,
        
        "查询": MetaAction.QUERY,
        "查看": MetaAction.QUERY,
        "获取": MetaAction.QUERY,
        "list": MetaAction.QUERY,
        "query": MetaAction.QUERY,
        "get": MetaAction.QUERY,
    }
    
    # 目标类型关键词映射
    TARGET_KEYWORDS = {
        "模板": TargetType.TEMPLATE,
        "意图模板": TargetType.TEMPLATE,
        "template": TargetType.TEMPLATE,
        
        "能力": TargetType.CAPABILITY,
        "能力注册": TargetType.CAPABILITY,
        "capability": TargetType.CAPABILITY,
        
        "策略": TargetType.POLICY,
        "政策": TargetType.POLICY,
        "执行策略": TargetType.POLICY,
        "policy": TargetType.POLICY,
        "超时": TargetType.POLICY,  # 超时时间属于策略
        "重试": TargetType.POLICY,  # 重试次数属于策略
        
        "配置": TargetType.CONFIG,
        "系统配置": TargetType.CONFIG,
        "config": TargetType.CONFIG,
        "configuration": TargetType.CONFIG,
    }
    
    def parse(self, source: str | dict) -> MetaIntent:
        """
        解析元意图
        
        Args:
            source: 自然语言字符串、PEF 字典、或 MetaIntent 字典
        
        Returns:
            解析后的 MetaIntent
        """
        if isinstance(source, str):
            return self._parse_natural_language(source)
        elif isinstance(source, dict):
            # 检查是否是 MetaIntent 字典
            if "action" in source and "target_type" in source:
                return MetaIntent.from_dict(source)
            # 否则假设是 PEF 格式
            return self._parse_pef(source)
        else:
            raise ValueError(f"不支持的输入类型：{type(source)}")
    
    def _parse_natural_language(self, text: str) -> MetaIntent:
        """解析自然语言"""
        text = text.strip()
        
        # 提取动作
        action = self._extract_action(text)
        if not action:
            raise ValueError(f"无法识别动作：{text}")
        
        # 提取目标类型
        target_type = self._extract_target_type(text)
        if not target_type:
            raise ValueError(f"无法识别目标类型：{text}")
        
        # 提取目标名称/ID
        target_id = self._extract_target_id(text, action)
        
        # 提取参数
        parameters = self._extract_parameters(text, action, target_type)
        
        return MetaIntent(
            action=action,
            target_type=target_type,
            target_id=target_id,
            parameters=parameters,
        )
    
    def _extract_action(self, text: str) -> Optional[MetaAction]:
        """提取动作"""
        for keyword, action in self.ACTION_KEYWORDS.items():
            if keyword in text:
                return action
        return None
    
    def _extract_target_type(self, text: str) -> Optional[TargetType]:
        """提取目标类型"""
        for keyword, target_type in self.TARGET_KEYWORDS.items():
            if keyword in text:
                return target_type
        return None
    
    def _extract_target_id(self, text: str, action: MetaAction) -> Optional[str]:
        """提取目标 ID"""
        if action in [MetaAction.MODIFY, MetaAction.DELETE]:
            # 尝试提取引号内的名称
            match = re.search(r'["\']([^"\']+)["\']', text)
            if match:
                return match.group(1)
            
            # 尝试提取"名为 XXX"的格式
            match = re.search(r'名为?\s*(\S+)', text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_parameters(self, text: str, action: MetaAction, target_type: TargetType) -> dict[str, Any]:
        """提取参数"""
        params = {}
        
        # 提取名称参数
        if action == MetaAction.CREATE:
            # "名为 XXX"
            match = re.search(r'名为?\s*(\S+)', text)
            if match:
                params["name"] = match.group(1)
            
            # "叫 XXX"
            match = re.search(r'叫\s*(\S+)', text)
            if match:
                params["name"] = match.group(1)
        
        # 提取策略参数
        if target_type == TargetType.POLICY:
            # "超时时间为 XXX 秒"
            match = re.search(r'超时 (?:时间)?(?:为)?\s*(\d+)\s*秒', text)
            if match:
                params["timeout_seconds"] = int(match.group(1))
            
            # "重试次数为 X"
            match = re.search(r'重试 (?:次数)?(?:为)?\s*(\d+)', text)
            if match:
                params["retry_count"] = int(match.group(1))
        
        return params
    
    def _parse_pef(self, pef_data: dict) -> MetaIntent:
        """解析 PEF 格式"""
        # PEF 格式转换
        intent = pef_data.get("intent", {})
        metadata = pef_data.get("metadata", {})
        
        action_str = intent.get("action", "")
        target_type_str = intent.get("target_type", "")
        
        # 字符串转枚举
        action = MetaAction(action_str) if action_str else MetaAction.QUERY
        target_type = TargetType(target_type_str) if target_type_str else TargetType.TEMPLATE
        
        return MetaIntent(
            action=action,
            target_type=target_type,
            target_id=intent.get("target_id"),
            parameters=intent.get("parameters", {}),
            constraints=intent.get("constraints", {}),
            created_by=metadata.get("author"),
        )
    
    def validate(self, meta_intent: MetaIntent) -> list[str]:
        """验证元意图有效性"""
        return meta_intent.validate()
    
    def parse_and_validate(self, source: str | dict) -> tuple[MetaIntent, list[str]]:
        """解析并验证"""
        meta_intent = self.parse(source)
        errors = self.validate(meta_intent)
        return meta_intent, errors


# =============================================================================
# 便捷函数
# =============================================================================

def parse_meta_intent(source: str | dict) -> MetaIntent:
    """便捷函数：解析元意图"""
    parser = MetaIntentParser()
    return parser.parse(source)


def create_meta_intent(
    action: MetaAction,
    target_type: TargetType,
    target_id: Optional[str] = None,
    **parameters,
) -> MetaIntent:
    """便捷函数：创建元意图"""
    return MetaIntent(
        action=action,
        target_type=target_type,
        target_id=target_id,
        parameters=parameters,
    )


# =============================================================================
# 示例
# =============================================================================

if __name__ == "__main__":
    parser = MetaIntentParser()
    
    # 示例 1: 自然语言 - 创建模板
    text1 = "创建一个名为 sales_analysis 的意图模板"
    meta1 = parser.parse(text1)
    print(f"示例 1: {meta1.to_dict()}")
    
    # 示例 2: 自然语言 - 修改策略
    text2 = '修改 sales_analysis 的超时时间为 600 秒'
    meta2 = parser.parse(text2)
    print(f"示例 2: {meta2.to_dict()}")
    
    # 示例 3: 自然语言 - 查询模板
    text3 = "查询所有 sales 相关的意图模板"
    meta3 = parser.parse(text3)
    print(f"示例 3: {meta3.to_dict()}")
    
    # 示例 4: PEF 格式
    pef_data = {
        "metadata": {"author": "admin"},
        "intent": {
            "action": "create",
            "target_type": "template",
            "parameters": {
                "name": "customer_report",
                "description": "客户报告模板",
            },
        },
    }
    meta4 = parser.parse(pef_data)
    print(f"示例 4: {meta4.to_dict()}")
