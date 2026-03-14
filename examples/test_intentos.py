"""
IntentOS 单元测试
"""

import asyncio

import pytest

from intentos import (
    Capability,
    Context,
    Intent,
    IntentOS,
    IntentRegistry,
    IntentStatus,
    IntentStep,
    IntentTemplate,
    IntentType,
)


class TestContext:
    """测试上下文"""

    def test_context_creation(self):
        """测试上下文创建"""
        ctx = Context(user_id="user_001")
        assert ctx.user_id == "user_001"
        assert ctx.user_role == "user"
        assert ctx.session_id is not None

    def test_context_permissions(self):
        """测试权限检查"""
        ctx = Context(user_id="user_001", permissions=["read", "write"])
        assert ctx.has_permission("read") is True
        assert ctx.has_permission("delete") is False
        assert ctx.has_permission("admin") is False

    def test_context_admin_permission(self):
        """测试管理员权限"""
        ctx = Context(user_id="admin", permissions=["admin"])
        assert ctx.has_permission("anything") is True

    def test_context_variables(self):
        """测试上下文变量"""
        ctx = Context(user_id="user_001")
        ctx.set_variable("region", "华东")
        assert ctx.get_variable("region") == "华东"
        assert ctx.get_variable("unknown", "default") == "default"


class TestIntent:
    """测试意图"""

    def test_intent_creation(self):
        """测试意图创建"""
        intent = Intent(
            name="test_intent",
            intent_type=IntentType.ATOMIC,
            goal="测试目标",
        )
        assert intent.name == "test_intent"
        assert intent.intent_type == IntentType.ATOMIC
        assert intent.status == IntentStatus.PENDING
        assert intent.id is not None

    def test_intent_to_dict(self):
        """测试意图序列化"""
        intent = Intent(
            name="test",
            intent_type=IntentType.COMPOSITE,
            goal="测试",
            params={"key": "value"},
        )
        d = intent.to_dict()
        assert d["name"] == "test"
        assert d["intent_type"] == "composite"
        assert d["params"]["key"] == "value"

    def test_intent_status_update(self):
        """测试状态更新"""
        intent = Intent(name="test", intent_type=IntentType.ATOMIC)
        intent.update_status(IntentStatus.EXECUTING)
        assert intent.status == IntentStatus.EXECUTING


class TestCapability:
    """测试能力"""

    def test_capability_creation(self):
        """测试能力创建"""
        def dummy_func(context, **kwargs):
            return {"result": "ok"}

        cap = Capability(
            name="test_cap",
            description="测试能力",
            input_schema={},
            output_schema={},
            func=dummy_func,
        )
        assert cap.name == "test_cap"

    def test_capability_execute(self):
        """测试能力执行"""
        def add(context, a: int, b: int) -> int:
            return a + b

        cap = Capability(
            name="add",
            description="加法",
            input_schema={"a": "int", "b": "int"},
            output_schema={"result": "int"},
            func=add,
        )

        ctx = Context(user_id="user_001")
        result = cap.execute(ctx, a=3, b=5)
        assert result == 8

    def test_capability_permission_check(self):
        """测试能力权限检查"""
        def secure_func(context) -> str:
            return "secret"

        cap = Capability(
            name="secure",
            description="安全功能",
            input_schema={},
            output_schema={},
            func=secure_func,
            requires_permissions=["admin"],
        )

        ctx = Context(user_id="user_001")
        with pytest.raises(PermissionError):
            cap.execute(ctx)


class TestIntentTemplate:
    """测试意图模板"""

    def test_template_creation(self):
        """测试模板创建"""
        template = IntentTemplate(
            name="analysis_template",
            description="分析模板",
            steps=[
                IntentStep(capability_name="query_data", params={"source": "sales"}),
            ],
        )
        assert template.name == "analysis_template"
        assert len(template.steps) == 1

    def test_template_instantiation(self):
        """测试模板实例化"""
        template = IntentTemplate(
            name="greet",
            description="问候",
            params_schema={"name": "string"},
            steps=[],
        )

        ctx = Context(user_id="user_001")
        intent = template.instantiate(ctx, name="张三")

        assert intent.name == "greet"
        assert intent.params["name"] == "张三"

    def test_template_param_resolution(self):
        """测试模板参数解析"""
        template = IntentTemplate(
            name="report",
            description="报告",
            params_schema={"region": "string"},
            steps=[
                IntentStep(
                    capability_name="query",
                    params={"region": "{{region}}"},
                ),
            ],
        )

        ctx = Context(user_id="user_001")
        intent = template.instantiate(ctx, region="华东")

        assert intent.steps[0].params["region"] == "华东"


class TestIntentRegistry:
    """测试意图注册中心"""

    def test_register_capability(self):
        """测试注册能力"""
        registry = IntentRegistry()

        def dummy(context):
            return "ok"

        cap = Capability(
            name="test",
            description="测试",
            input_schema={},
            output_schema={},
            func=dummy,
        )

        registry.register_capability(cap)
        assert registry.get_capability("test") == cap

    def test_register_template(self):
        """测试注册模板"""
        registry = IntentRegistry()

        template = IntentTemplate(
            name="test_template",
            description="测试模板",
        )

        registry.register_template(template)
        assert registry.get_template("test_template") == template

    def test_list_templates(self):
        """测试列出模板"""
        registry = IntentRegistry()

        t1 = IntentTemplate(name="t1", description="T1", tags=["sales"])
        t2 = IntentTemplate(name="t2", description="T2", tags=["hr"])

        registry.register_template(t1)
        registry.register_template(t2)

        all_templates = registry.list_templates()
        assert len(all_templates) == 2

        sales_templates = registry.list_templates(tags=["sales"])
        assert len(sales_templates) == 1

    def test_introspect(self):
        """测试自省"""
        registry = IntentRegistry()

        cap = Capability(
            name="test_cap",
            description="测试能力",
            input_schema={},
            output_schema={},
            func=lambda ctx: None,
            tags=["test"],
        )
        registry.register_capability(cap)

        result = registry.introspect()
        assert "test_cap" in result["capabilities"]
        assert "templates" in result
        assert "policies" in result

    def test_search(self):
        """测试搜索"""
        registry = IntentRegistry()

        template = IntentTemplate(
            name="sales_analysis",
            description="销售数据分析",
        )
        registry.register_template(template)

        results = registry.search("sales")
        assert "sales_analysis" in results["templates"]


class TestIntentOS:
    """测试 IntentOS 主类"""

    def test_initialization(self):
        """测试系统初始化"""
        os = IntentOS()
        os.initialize()

        # 检查内置能力是否注册
        assert os.registry.get_capability("query_data") is not None
        assert os.registry.get_capability("generate_report") is not None
        assert os.registry.get_capability("analyze_data") is not None

    def test_execute_basic(self):
        """测试基本执行"""
        os = IntentOS()
        os.initialize()

        result = asyncio.run(os.interface.chat("查询数据"))
        assert result is not None

    def test_set_user(self):
        """测试设置用户"""
        os = IntentOS()
        os.initialize()

        os.interface.set_user(
            user_id="test_user",
            role="manager",
            permissions=["read", "write"],
        )

        ctx = os.context
        assert ctx.user_id == "test_user"
        assert ctx.user_role == "manager"
        assert ctx.has_permission("read") is True


class TestIntentParser:
    """测试意图解析器"""

    def test_parse_simple(self):
        """测试简单解析"""
        from intentos.parser import IntentParser

        parser = IntentParser()
        ctx = Context(user_id="user_001")

        intent = parser.parse("帮我分析一下", ctx)

        assert intent is not None
        assert intent.context.user_id == "user_001"

    def test_parse_with_pattern(self):
        """测试模式匹配解析"""
        from intentos import IntentTemplate
        from intentos.parser import IntentParser

        registry = IntentRegistry()
        parser = IntentParser(registry)

        # 注册模板
        template = IntentTemplate(
            name="query_sales",
            description="查询销售",
            params_schema={"region": "string"},
        )
        registry.register_template(template)

        # 注册模式
        parser.register_pattern(r"查询.*销售", "query_sales")

        ctx = Context(user_id="user_001")
        intent = parser.parse("查询华东销售", ctx)

        assert intent.name == "query_sales"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
