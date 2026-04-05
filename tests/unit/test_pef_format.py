"""
PEF v2.0 格式测试

测试覆盖:
- 数据模型创建
- 序列化/反序列化（YAML/JSON）
- 文件 I/O
- 验证器
- v1.0 向后兼容
- 编译器 v2.0
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from intentos.agent.compiler import PEF as PEFv1
from intentos.compiler import (
    PEF,
    CapabilityBinding,
    ContextBinding,
    IntentCompilerV2,
    IntentDeclaration,
    WorkflowDefinition,
    WorkflowStep,
    compile_intent,
    create_pef,
    load_pef,
    save_pef,
)


# =============================================================================
# 数据模型测试
# =============================================================================


class TestIntentDeclaration:
    """意图声明测试"""

    def test_create_simple(self):
        """创建简单意图"""
        intent = IntentDeclaration(goal="分析销售数据")
        assert intent.goal == "分析销售数据"
        assert intent.output_format == "json"

    def test_to_dict(self):
        """转换为字典"""
        intent = IntentDeclaration(
            goal="分析销售数据",
            description="详细分析",
            output_format="markdown",
        )
        data = intent.to_dict()
        assert data["goal"] == "分析销售数据"
        assert data["description"] == "详细分析"
        assert data["output_format"] == "markdown"

    def test_from_dict(self):
        """从字典创建"""
        data = {
            "goal": "查询订单",
            "description": "查询今日订单",
            "output_format": "json",
        }
        intent = IntentDeclaration.from_dict(data)
        assert intent.goal == "查询订单"
        assert intent.description == "查询今日订单"


class TestContextBinding:
    """上下文绑定测试"""

    def test_create_simple(self):
        """创建简单上下文"""
        ctx = ContextBinding(user_id="user_001")
        assert ctx.user_id == "user_001"

    def test_with_business_context(self):
        """带业务上下文"""
        ctx = ContextBinding(
            user_id="sales_manager",
            business_context={"region": "华东", "period": "Q3"},
        )
        assert ctx.business_context["region"] == "华东"


class TestCapabilityBinding:
    """能力绑定测试"""

    def test_create_simple(self):
        """创建简单能力"""
        cap = CapabilityBinding(name="query_sales_data")
        assert cap.name == "query_sales_data"
        assert cap.version == "*"

    def test_with_params(self):
        """带参数"""
        cap = CapabilityBinding(
            name="query_sales_data",
            params={"region": "华东"},
        )
        assert cap.params["region"] == "华东"


class TestWorkflowStep:
    """工作流步骤测试"""

    def test_create_simple(self):
        """创建简单步骤"""
        step = WorkflowStep(
            id="step1",
            name="查询数据",
            capability="query_sales_data",
        )
        assert step.id == "step1"
        assert step.depends_on == []

    def test_with_dependencies(self):
        """带依赖"""
        step = WorkflowStep(
            id="step2",
            name="分析数据",
            capability="analyze_data",
            depends_on=["step1"],
        )
        assert "step1" in step.depends_on


# =============================================================================
# PEF 核心测试
# =============================================================================


class TestPEF:
    """PEF v2.0 核心测试"""

    def test_create_simple(self):
        """创建简单 PEF"""
        pef = PEF(
            intent=IntentDeclaration(goal="分析销售数据"),
            context=ContextBinding(user_id="user_001"),
        )
        assert pef.version == "2.0"
        assert pef.intent.goal == "分析销售数据"
        assert pef.context.user_id == "user_001"
        assert pef.id.startswith("pef_")

    def test_auto_generate_id(self):
        """自动生成 ID"""
        pef1 = PEF()
        pef2 = PEF()
        assert pef1.id != pef2.id
        assert pef1.id.startswith("pef_")

    def test_auto_generate_compiled_at(self):
        """自动生成编译时间"""
        pef = PEF()
        assert pef.compiled_at != ""
        # 验证 ISO 8601 格式
        from datetime import datetime
        datetime.fromisoformat(pef.compiled_at)

    def test_with_capabilities(self):
        """带能力绑定"""
        pef = PEF(
            intent=IntentDeclaration(goal="分析销售数据"),
            context=ContextBinding(user_id="user_001"),
            capabilities=[
                CapabilityBinding(name="query_sales_data"),
                CapabilityBinding(name="analyze_trends"),
            ],
        )
        assert len(pef.capabilities) == 2
        assert pef.capabilities[0].name == "query_sales_data"

    def test_with_workflow(self):
        """带工作流"""
        pef = PEF(
            intent=IntentDeclaration(goal="分析销售数据"),
            context=ContextBinding(user_id="user_001"),
            workflow=WorkflowDefinition(
                steps=[
                    WorkflowStep(
                        id="query",
                        name="查询数据",
                        capability="query_sales_data",
                    ),
                    WorkflowStep(
                        id="analyze",
                        name="分析数据",
                        capability="analyze_data",
                        depends_on=["query"],
                    ),
                ]
            ),
        )
        assert pef.workflow is not None
        assert len(pef.workflow.steps) == 2

    def test_get_capability_names(self):
        """获取能力名称"""
        pef = PEF(
            capabilities=[
                CapabilityBinding(name="cap1"),
                CapabilityBinding(name="cap2"),
            ]
        )
        names = pef.get_capability_names()
        assert names == ["cap1", "cap2"]


# =============================================================================
# 序列化测试
# =============================================================================


class TestPEFSerialization:
    """PEF 序列化/反序列化测试"""

    def _create_sample_pef(self) -> PEF:
        """创建示例 PEF"""
        return PEF(
            intent=IntentDeclaration(
                goal="分析华东区 Q3 销售数据",
                output_format="markdown",
            ),
            context=ContextBinding(
                user_id="sales_manager",
                session_id="sess_001",
                business_context={"region": "华东", "period": "Q3"},
            ),
            capabilities=[
                CapabilityBinding(
                    name="query_sales_data",
                    params={"region": "华东"},
                ),
            ],
            constraints={"execution": {"temperature": 0.0}},
            metadata={"tags": ["sales", "analysis"]},
        )

    def test_to_dict(self):
        """转换为字典"""
        pef = self._create_sample_pef()
        data = pef.to_dict()

        assert data["version"] == "2.0"
        assert data["intent"]["goal"] == "分析华东区 Q3 销售数据"
        assert data["context"]["user_id"] == "sales_manager"
        assert len(data["capabilities"]) == 1
        assert "constraints" in data
        assert "metadata" in data

    def test_from_dict(self):
        """从字典创建"""
        data = {
            "version": "2.0",
            "id": "pef_test_001",
            "compiled_at": "2026-04-05T14:30:25",
            "intent": {"goal": "测试意图"},
            "context": {"user_id": "test_user"},
            "capabilities": [{"name": "test_cap"}],
        }
        pef = PEF.from_dict(data)
        assert pef.id == "pef_test_001"
        assert pef.intent.goal == "测试意图"
        assert pef.context.user_id == "test_user"
        assert len(pef.capabilities) == 1

    def test_to_yaml(self):
        """导出为 YAML"""
        pef = self._create_sample_pef()
        yaml_str = pef.to_yaml()

        # 验证 YAML 可解析
        data = yaml.safe_load(yaml_str)
        assert data["intent"]["goal"] == "分析华东区 Q3 销售数据"

    def test_from_yaml(self):
        """从 YAML 加载"""
        yaml_str = """
version: "2.0"
id: "pef_yaml_test"
compiled_at: "2026-04-05T14:30:25"
intent:
  goal: "YAML 测试"
context:
  user_id: "test_user"
capabilities:
  - name: "test_cap"
"""
        pef = PEF.from_yaml(yaml_str)
        assert pef.id == "pef_yaml_test"
        assert pef.intent.goal == "YAML 测试"

    def test_to_json(self):
        """导出为 JSON"""
        pef = self._create_sample_pef()
        json_str = pef.to_json()

        # 验证 JSON 可解析
        data = json.loads(json_str)
        assert data["intent"]["goal"] == "分析华东区 Q3 销售数据"

    def test_from_json(self):
        """从 JSON 加载"""
        json_str = json.dumps({
            "version": "2.0",
            "id": "pef_json_test",
            "compiled_at": "2026-04-05T14:30:25",
            "intent": {"goal": "JSON 测试"},
            "context": {"user_id": "test_user"},
            "capabilities": [{"name": "test_cap"}],
        })
        pef = PEF.from_json(json_str)
        assert pef.id == "pef_json_test"
        assert pef.intent.goal == "JSON 测试"

    def test_roundtrip_yaml(self):
        """YAML 往返测试"""
        pef1 = self._create_sample_pef()
        yaml_str = pef1.to_yaml()
        pef2 = PEF.from_yaml(yaml_str)

        assert pef2.intent.goal == pef1.intent.goal
        assert pef2.context.user_id == pef1.context.user_id
        assert len(pef2.capabilities) == len(pef1.capabilities)

    def test_roundtrip_json(self):
        """JSON 往返测试"""
        pef1 = self._create_sample_pef()
        json_str = pef1.to_json()
        pef2 = PEF.from_json(json_str)

        assert pef2.intent.goal == pef1.intent.goal
        assert pef2.context.user_id == pef1.context.user_id


# =============================================================================
# 文件 I/O 测试
# =============================================================================


class TestPEFFileIO:
    """PEF 文件 I/O 测试"""

    def _create_sample_pef(self) -> PEF:
        return PEF(
            intent=IntentDeclaration(goal="文件 I/O 测试"),
            context=ContextBinding(user_id="test_user"),
            capabilities=[CapabilityBinding(name="test_cap")],
        )

    def test_save_and_load_yaml(self):
        """保存和加载 YAML"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.pef.yaml"
            pef1 = self._create_sample_pef()
            pef1.to_file(filepath, format="yaml")

            # 验证文件存在
            assert filepath.exists()

            # 加载
            pef2 = PEF.from_file(filepath)
            assert pef2.intent.goal == "文件 I/O 测试"

    def test_save_and_load_json(self):
        """保存和加载 JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.pef.json"
            pef1 = self._create_sample_pef()
            pef1.to_file(filepath, format="json")

            # 验证文件存在
            assert filepath.exists()

            # 加载
            pef2 = PEF.from_file(filepath)
            assert pef2.intent.goal == "文件 I/O 测试"

    def test_convenience_functions(self):
        """便捷函数测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.pef.yaml"
            pef1 = self._create_sample_pef()

            # 保存
            save_pef(pef1, filepath)

            # 加载
            pef2 = load_pef(filepath)
            assert pef2.intent.goal == "文件 I/O 测试"

    def test_auto_detect_format(self):
        """自动检测格式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # YAML 文件
            yaml_path = Path(tmpdir) / "test.pef.yaml"
            pef1 = self._create_sample_pef()
            pef1.to_file(yaml_path, format="yaml")
            pef2 = PEF.from_file(yaml_path)
            assert pef2.intent.goal == "文件 I/O 测试"

            # JSON 文件
            json_path = Path(tmpdir) / "test.pef.json"
            pef1.to_file(json_path, format="json")
            pef3 = PEF.from_file(json_path)
            assert pef3.intent.goal == "文件 I/O 测试"


# =============================================================================
# 验证器测试
# =============================================================================


class TestPEFValidation:
    """PEF 验证器测试"""

    def test_valid_pef(self):
        """有效 PEF"""
        pef = PEF(
            intent=IntentDeclaration(goal="测试"),
            context=ContextBinding(user_id="user_001"),
        )
        errors = pef.validate()
        assert errors == []

    def test_missing_goal(self):
        """缺少 intent.goal"""
        pef = PEF(
            intent=IntentDeclaration(goal=""),
            context=ContextBinding(user_id="user_001"),
        )
        errors = pef.validate()
        assert any("intent.goal" in err for err in errors)

    def test_missing_user_id(self):
        """缺少 context.user_id"""
        pef = PEF(
            intent=IntentDeclaration(goal="测试"),
            context=ContextBinding(user_id=""),
        )
        errors = pef.validate()
        assert any("context.user_id" in err for err in errors)

    def test_invalid_workflow_dependency(self):
        """无效的工作流依赖"""
        pef = PEF(
            intent=IntentDeclaration(goal="测试"),
            context=ContextBinding(user_id="user_001"),
            workflow=WorkflowDefinition(
                steps=[
                    WorkflowStep(
                        id="step2",
                        name="步骤2",
                        capability="cap1",
                        depends_on=["step1"],  # step1 不存在
                    ),
                ]
            ),
        )
        errors = pef.validate()
        assert any("non-existent step" in err for err in errors)

    def test_empty_capability_name(self):
        """空能力名称"""
        pef = PEF(
            intent=IntentDeclaration(goal="测试"),
            context=ContextBinding(user_id="user_001"),
            capabilities=[CapabilityBinding(name="")],
        )
        errors = pef.validate()
        assert any("name is required" in err for err in errors)


# =============================================================================
# v1.0 向后兼容测试
# =============================================================================


class TestV1Compatibility:
    """v1.0 向后兼容测试"""

    def test_v1_to_v2(self):
        """v1.0 转 v2.0"""
        v1_pef = PEFv1(
            id="pef_v1_001",
            intent="分析销售数据",
            system_prompt="你是一个助手",
            user_prompt="请执行：分析销售数据",
            capabilities=["query_sales_data"],
            metadata={"user_id": "sales_manager"},
            compiled_at="2026-04-05T14:30:25",
        )

        v2_pef = PEF.from_v1(v1_pef)

        assert v2_pef.intent.goal == "分析销售数据"
        assert v2_pef.context.user_id == "sales_manager"
        assert len(v2_pef.capabilities) == 1
        assert v2_pef.capabilities[0].name == "query_sales_data"

    def test_v2_to_v1(self):
        """v2.0 转 v1.0"""
        v2_pef = PEF(
            id="pef_v2_001",
            intent=IntentDeclaration(goal="分析销售数据"),
            context=ContextBinding(user_id="sales_manager"),
            capabilities=[CapabilityBinding(name="query_sales_data")],
            compiled_at="2026-04-05T14:30:25",
        )

        v1_pef = v2_pef.to_v1()

        assert v1_pef.intent == "分析销售数据"
        assert v1_pef.capabilities == ["query_sales_data"]
        assert "sales_manager" in v1_pef.metadata.values()

    def test_v1_to_v2_to_v1_roundtrip(self):
        """v1 → v2 → v1 往返测试"""
        v1_original = PEFv1(
            id="pef_roundtrip",
            intent="测试往返转换",
            system_prompt="系统提示",
            user_prompt="请执行：测试往返转换",
            capabilities=["cap1"],
            metadata={"user_id": "test_user"},
        )

        v2_pef = PEF.from_v1(v1_original)
        v1_converted = v2_pef.to_v1()

        assert v1_converted.intent == v1_original.intent
        assert v1_converted.capabilities == v1_original.capabilities

    def test_v1_pef_to_v2_method(self):
        """v1 PEF 的 to_v2() 方法"""
        v1_pef = PEFv1(
            intent="测试方法",
            capabilities=["cap1"],
            metadata={"user_id": "test_user"},
        )

        v2_pef = v1_pef.to_v2()
        assert v2_pef.intent.goal == "测试方法"
        assert len(v2_pef.capabilities) == 1


# =============================================================================
# 编译器 v2.0 测试
# =============================================================================


class TestIntentCompilerV2:
    """编译器 v2.0 测试"""

    def test_compile_simple(self):
        """简单编译"""
        compiler = IntentCompilerV2()
        pef = compiler.compile(
            goal="分析销售数据",
            user_id="sales_manager",
        )

        assert pef.version == "2.0"
        assert pef.intent.goal == "分析销售数据"
        assert pef.context.user_id == "sales_manager"
        assert pef.id.startswith("pef_")

    def test_compile_with_capabilities(self):
        """带能力编译"""
        compiler = IntentCompilerV2()
        pef = compiler.compile(
            goal="分析销售数据",
            user_id="sales_manager",
            capabilities=["query_sales_data", "analyze_trends"],
        )

        assert len(pef.capabilities) == 2
        assert pef.capabilities[0].name == "query_sales_data"

    def test_compile_with_context(self):
        """带上下文编译"""
        compiler = IntentCompilerV2()
        pef = compiler.compile(
            goal="分析销售数据",
            user_id="sales_manager",
            context={"region": "华东", "period": "Q3"},
        )

        assert pef.context.business_context["region"] == "华东"

    def test_compile_with_constraints(self):
        """带约束编译"""
        compiler = IntentCompilerV2()
        constraints = {
            "resource_limits": {"max_tokens": 8192},
            "execution": {"temperature": 0.3},
        }
        pef = compiler.compile(
            goal="分析销售数据",
            user_id="sales_manager",
            constraints=constraints,
        )

        assert pef.constraints["resource_limits"]["max_tokens"] == 8192

    def test_compile_caching(self):
        """编译缓存"""
        compiler = IntentCompilerV2()
        pef1 = compiler.compile(
            goal="测试缓存",
            user_id="test_user",
        )
        pef2 = compiler.compile(
            goal="测试缓存",
            user_id="test_user",
        )

        # 应该返回相同的 PEF（从缓存）
        assert pef1.id == pef2.id

        stats = compiler.get_stats()
        assert stats["cache_hits"] == 1

    def test_compile_from_file(self):
        """从文件编译"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.pef.yaml"
            pef1 = create_pef(
                goal="文件编译测试",
                user_id="test_user",
                capabilities=["test_cap"],
            )
            save_pef(pef1, filepath)

            compiler = IntentCompilerV2()
            pef2 = compiler.compile_from_file(filepath)

            assert pef2.intent.goal == "文件编译测试"

    def test_save_pef(self):
        """保存 PEF"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.pef.yaml"
            compiler = IntentCompilerV2()
            pef = compiler.compile(
                goal="保存测试",
                user_id="test_user",
            )

            compiler.save_pef(pef, filepath)
            assert filepath.exists()

            # 验证内容
            pef2 = PEF.from_file(filepath)
            assert pef2.intent.goal == "保存测试"


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_compile_intent(self):
        """compile_intent 函数"""
        pef = compile_intent(
            goal="快速编译",
            user_id="test_user",
            capabilities=["cap1"],
        )

        assert pef.intent.goal == "快速编译"
        assert pef.context.user_id == "test_user"
        assert len(pef.capabilities) == 1

    def test_create_pef(self):
        """create_pef 函数"""
        pef = create_pef(
            goal="创建 PEF",
            user_id="test_user",
            capabilities=["cap1", "cap2"],
            context={"region": "华东"},
        )

        assert pef.intent.goal == "创建 PEF"
        assert len(pef.capabilities) == 2
        assert pef.context.business_context["region"] == "华东"


# =============================================================================
# 集成测试
# =============================================================================


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """完整工作流测试"""
        # 创建 PEF
        pef = PEF(
            intent=IntentDeclaration(
                goal="分析华东区 Q3 销售数据并生成报告",
                output_format="markdown",
            ),
            context=ContextBinding(
                user_id="sales_manager",
                business_context={"region": "华东", "period": "Q3"},
            ),
            capabilities=[
                CapabilityBinding(
                    name="query_sales_data",
                    params={"region": "${context.business_context.region}"},
                ),
                CapabilityBinding(name="analyze_trends"),
                CapabilityBinding(name="generate_report"),
            ],
            workflow=WorkflowDefinition(
                steps=[
                    WorkflowStep(
                        id="query",
                        name="查询销售数据",
                        capability="query_sales_data",
                        output_var="sales_data",
                    ),
                    WorkflowStep(
                        id="analyze",
                        name="分析趋势",
                        capability="analyze_trends",
                        depends_on=["query"],
                        output_var="analysis_result",
                    ),
                    WorkflowStep(
                        id="report",
                        name="生成报告",
                        capability="generate_report",
                        depends_on=["analyze"],
                        output_var="final_report",
                    ),
                ]
            ),
            constraints={
                "resource_limits": {"max_tokens": 8192, "timeout_seconds": 600},
                "execution": {"temperature": 0.3},
            },
            metadata={"tags": ["sales", "analysis", "q3"]},
        )

        # 验证
        errors = pef.validate()
        assert errors == []

        # 序列化
        yaml_str = pef.to_yaml()
        assert "分析华东区 Q3 销售数据并生成报告" in yaml_str

        # 反序列化
        pef2 = PEF.from_yaml(yaml_str)
        assert pef2.intent.goal == pef.intent.goal
        assert len(pef2.workflow.steps) == 3

        # 文件 I/O
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "sales_analysis.pef.yaml"
            save_pef(pef, filepath)
            pef3 = load_pef(filepath)
            assert pef3.intent.goal == pef.intent.goal

    def test_complex_yaml_output(self):
        """复杂 YAML 输出测试"""
        pef = create_pef(
            goal="分析销售数据",
            user_id="sales_manager",
            capabilities=["query_sales", "analyze_data"],
            context={"region": "华东", "period": "Q3", "year": 2024},
        )

        yaml_str = pef.to_yaml()
        
        # 验证 YAML 结构
        data = yaml.safe_load(yaml_str)
        assert data["version"] == "2.0"
        assert data["intent"]["goal"] == "分析销售数据"
        assert data["context"]["business_context"]["region"] == "华东"
        assert len(data["capabilities"]) == 2

    def test_json_output_pretty(self):
        """JSON 美化输出测试"""
        pef = create_pef(
            goal="测试 JSON",
            user_id="test_user",
        )

        json_str = pef.to_json(indent=2)
        
        # 验证 JSON 格式
        data = json.loads(json_str)
        assert data["intent"]["goal"] == "测试 JSON"
        
        # 验证缩进
        assert "  \"version\"" in json_str
