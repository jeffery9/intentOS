"""
Parser 和 Registry 模块测试
"""

import pytest
from intentos.parser.parser import IntentParser
from intentos.registry.registry import IntentRegistry, capability
from intentos.core import Context, IntentTemplate, IntentType, Capability


class TestIntentParser:
    """IntentParser 测试"""

    def test_parser_creation(self):
        """测试解析器创建"""
        parser = IntentParser()
        assert parser is not None
        assert parser.registry is None

    def test_parser_with_registry(self):
        """测试带注册表的解析器"""
        registry = IntentRegistry()
        parser = IntentParser(registry=registry)
        assert parser.registry == registry

    def test_register_pattern(self):
        """测试注册模式"""
        parser = IntentParser()
        parser.register_pattern(r"查询.*数据", "query_data")
        assert len(parser._patterns) == 1

    def test_parse_simple_text(self):
        """测试解析简单文本"""
        parser = IntentParser()
        context = Context(user_id="test_user")
        intent = parser.parse("查询销售数据", context)
        assert intent is not None
        assert intent.name == "generic_intent"

    def test_parse_without_context(self):
        """测试不带上下文解析"""
        parser = IntentParser()
        intent = parser.parse("分析数据")
        assert intent is not None
        assert intent.context.user_id == "anonymous"

    def test_classify_intent_type(self):
        """测试意图类型分类"""
        parser = IntentParser()
        intent_type = parser._classify_intent("分析对比数据")
        assert intent_type == IntentType.COMPOSITE

    def test_classify_scenario_intent(self):
        """测试场景意图分类"""
        parser = IntentParser()
        intent_type = parser._classify_intent("生成周报")
        assert intent_type == IntentType.SCENARIO or intent_type == IntentType.COMPOSITE

    def test_classify_atomic_intent(self):
        """测试原子意图分类"""
        parser = IntentParser()
        intent_type = parser._classify_intent("查询数据")
        assert intent_type == IntentType.ATOMIC

    def test_extract_goal(self):
        """测试目标提取"""
        parser = IntentParser()
        goal = parser._extract_goal("查询销售数据")
        assert goal == "查询销售数据"

    def test_match_registered_without_registry(self):
        """测试无注册表时匹配"""
        parser = IntentParser()
        context = Context(user_id="test")
        result = parser._match_registered("test", context)
        assert result is None


class TestIntentRegistry:
    """IntentRegistry 测试"""

    def test_registry_creation(self):
        """测试注册表创建"""
        registry = IntentRegistry()
        assert registry is not None
        assert registry._templates == {}
        assert registry._capabilities == {}

    def test_register_template(self):
        """测试注册模板"""
        registry = IntentRegistry()
        template = IntentTemplate(name="test_template", description="Test")
        registry.register_template(template)
        assert "test_template" in registry._templates

    def test_get_template(self):
        """测试获取模板"""
        registry = IntentRegistry()
        template = IntentTemplate(name="get_test", description="Get test")
        registry.register_template(template)
        retrieved = registry.get_template("get_test")
        assert retrieved is not None
        assert retrieved.name == "get_test"

    def test_get_nonexistent_template(self):
        """测试获取不存在的模板"""
        registry = IntentRegistry()
        template = registry.get_template("nonexistent")
        assert template is None

    def test_list_templates(self):
        """测试列出模板"""
        registry = IntentRegistry()
        registry.register_template(IntentTemplate(name="t1", description="T1"))
        registry.register_template(IntentTemplate(name="t2", description="T2"))
        templates = registry.list_templates()
        assert len(templates) == 2

    def test_remove_template(self):
        """测试删除模板"""
        registry = IntentRegistry()
        template = IntentTemplate(name="to_remove", description="Remove")
        registry.register_template(template)
        result = registry.remove_template("to_remove")
        assert result is True
        assert "to_remove" not in registry._templates

    def test_remove_nonexistent_template(self):
        """测试删除不存在的模板"""
        registry = IntentRegistry()
        result = registry.remove_template("nonexistent")
        assert result is False

    def test_register_capability(self):
        """测试注册能力"""
        registry = IntentRegistry()
        cap = Capability(name="test_cap", description="Test", input_schema={}, output_schema={}, func=lambda ctx: None)
        registry.register_capability(cap)
        assert "test_cap" in registry._capabilities

    def test_get_capability(self):
        """测试获取能力"""
        registry = IntentRegistry()
        cap = Capability(name="get_cap", description="Get", input_schema={}, output_schema={}, func=lambda ctx: None)
        registry.register_capability(cap)
        retrieved = registry.get_capability("get_cap")
        assert retrieved is not None

    def test_list_capabilities(self):
        """测试列出能力"""
        registry = IntentRegistry()
        registry.register_capability(Capability(name="c1", description="C1", input_schema={}, output_schema={}, func=lambda ctx: None))
        registry.register_capability(Capability(name="c2", description="C2", input_schema={}, output_schema={}, func=lambda ctx: None))
        capabilities = registry.list_capabilities()
        assert len(capabilities) == 2

    def test_remove_capability(self):
        """测试删除能力"""
        registry = IntentRegistry()
        cap = Capability(name="to_remove", description="Remove", input_schema={}, output_schema={}, func=lambda ctx: None)
        registry.register_capability(cap)
        result = registry.remove_capability("to_remove")
        assert result is True

    def test_register_policy(self):
        """测试注册策略"""
        registry = IntentRegistry()
        policy = {"constraints": {"max_tokens": 1000}}
        registry.register_policy("test_policy", policy)
        assert "test_policy" in registry._policies

    def test_get_policy(self):
        """测试获取策略"""
        registry = IntentRegistry()
        policy = {"key": "value"}
        registry.register_policy("get_policy", policy)
        retrieved = registry.get_policy("get_policy")
        assert retrieved is not None
        assert retrieved["key"] == "value"

    def test_introspect(self):
        """测试注册表自省"""
        registry = IntentRegistry()
        registry.register_template(IntentTemplate(name="t1", description="Template 1"))
        registry.register_capability(Capability(name="c1", description="Cap 1", input_schema={}, output_schema={}, func=lambda ctx: None))
        registry.register_policy("p1", {"key": "value"})
        introspection = registry.introspect()
        assert "templates" in introspection
        assert "capabilities" in introspection
        assert "policies" in introspection

    def test_search(self):
        """测试搜索"""
        registry = IntentRegistry()
        registry.register_template(IntentTemplate(name="sales_query", description="Query sales"))
        registry.register_capability(Capability(name="api_call", description="API capability", input_schema={}, output_schema={}, func=lambda ctx: None))
        results = registry.search("sales")
        assert "templates" in results
        assert "sales_query" in results["templates"]

    def test_search_no_match(self):
        """测试搜索无匹配"""
        registry = IntentRegistry()
        results = registry.search("nonexistent_xyz")
        assert results["templates"] == []
        assert results["capabilities"] == []


class TestCapabilityDecorator:
    """能力装饰器测试"""

    def test_capability_decorator_basic(self):
        """测试基本能力装饰器"""
        @capability("test_cap", description="Test capability")
        def test_func(context, data: str):
            return data
        assert hasattr(test_func, '_capability')
        assert test_func._capability.name == "test_cap"

    def test_capability_decorator_with_tags(self):
        """测试带标签的能力装饰器"""
        @capability("tagged_cap", tags=["api", "test"])
        def tagged_func(context):
            pass
        assert "api" in tagged_func._capability.tags
        assert "test" in tagged_func._capability.tags


class TestParserRegistryIntegration:
    """Parser 和 Registry 集成测试"""

    def test_parser_with_registered_template(self):
        """测试带注册模板的解析器"""
        registry = IntentRegistry()
        parser = IntentParser(registry=registry)
        template = IntentTemplate(name="query_data", description="Query data template")
        registry.register_template(template)
        parser.register_pattern(r"查询.*", "query_data")
        context = Context(user_id="integration_test")
        intent = parser.parse("查询数据", context)
        assert intent is not None

    def test_full_registration_workflow(self):
        """测试完整注册工作流"""
        registry = IntentRegistry()
        template = IntentTemplate(name="analyze_sales", description="Analyze sales data")
        registry.register_template(template)
        capability = Capability(name="sales_api", description="Sales API", input_schema={}, output_schema={}, func=lambda ctx: None)
        registry.register_capability(capability)
        registry.register_policy("rate_limit", {"max_requests": 100})
        results = registry.search("sales")
        assert "analyze_sales" in results["templates"]
