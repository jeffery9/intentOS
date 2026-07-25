"""
测试 intentos.bootstrap.meta_intent_executor - 元意图执行器

覆盖:
- MetaIntentType 枚举
- MetaIntent (创建, to_dict)
"""

import pytest


class TestMetaIntentType:
    """元意图类型枚举测试"""

    def test_all_types_exist(self):
        from intentos.bootstrap.meta_intent_executor import MetaIntentType
        types = [t.value for t in MetaIntentType]
        assert "modify_protocol" in types
        assert "register_capability" in types
        assert "define_instruction" in types
        assert "modify_os_component" in types


class TestMetaIntent:
    """元意图测试"""

    def test_create_meta_intent(self):
        from intentos.bootstrap.meta_intent_executor import MetaIntent, MetaIntentType
        mi = MetaIntent(
            meta_intent_type=MetaIntentType.REGISTER_CAPABILITY,
            params={"name": "new_cap"},
          )
        assert mi.meta_intent_type == MetaIntentType.REGISTER_CAPABILITY

    def test_to_dict(self):
        from intentos.bootstrap.meta_intent_executor import MetaIntent, MetaIntentType
        mi = MetaIntent(
            meta_intent_type=MetaIntentType.MODIFY_PROTOCOL,
            params={"action": "add_rule"},
          )
        d = mi.to_dict()
        assert isinstance(d, dict)
        assert "meta_intent_type" in d or "type" in d


# =============================================================================
# Protocol Extender 测试
# =============================================================================

class TestCapabilityGap:
    """能力缺口测试"""

    def test_create_capability_gap(self):
        from intentos.bootstrap.protocol_extender import CapabilityGap
        gap = CapabilityGap(
            capability_name="missing_feature",
            description="缺少某功能",
            required_by="user_intent_123",
          )
        assert gap.capability_name == "missing_feature"

    def test_to_dict(self):
        from intentos.bootstrap.protocol_extender import CapabilityGap
        gap = CapabilityGap(
            capability_name="new_api",
            description="新API支持",
            required_by="intent_x",
            confidence=0.95,
          )
        d = gap.to_dict()
        assert d["capability_name"] == "new_api"
        assert d["confidence"] == 0.95


class TestExtensionSuggestion:
    """扩展建议测试"""

    def test_create_extension_suggestion(self):
        from intentos.bootstrap.protocol_extender import CapabilityGap, ExtensionSuggestion
        gap = CapabilityGap(
            capability_name="gap_1",
            description="描述",
            required_by="intent_x",
          )
        suggestion = ExtensionSuggestion(
            gap=gap,
            suggestion_type="register_capability",
            params={"name": "new_cap"},
            reason="能力缺口检测",
          )
        assert suggestion.suggestion_type == "register_capability"

    def test_to_meta_intent(self):
        from intentos.bootstrap.protocol_extender import CapabilityGap, ExtensionSuggestion
        gap = CapabilityGap(
            capability_name="gap_1",
            description="描述",
            required_by="intent_x",
          )
        suggestion = ExtensionSuggestion(
            gap=gap,
            suggestion_type="register_capability",
            params={"name": "new_cap"},
            reason="测试",
          )
        mi = suggestion.to_meta_intent()
        assert mi is not None
