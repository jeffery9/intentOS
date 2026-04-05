"""
PEF v2.0 使用示例

展示如何：
1. 创建 PEF
2. 序列化为 YAML/JSON
3. 从文件加载
4. 验证 PEF
5. 与 v1.0 格式互操作
"""

from pathlib import Path

from intentos.compiler import (
    PEF,
    CapabilityBinding,
    ContextBinding,
    IntentCompilerV2,
    IntentDeclaration,
    WorkflowDefinition,
    WorkflowStep,
    compile_intent,
    load_pef,
    save_pef,
)


def example_1_create_pef():
    """示例 1: 创建 PEF"""
    print("=" * 60)
    print("示例 1: 创建 PEF")
    print("=" * 60)

    # 使用便捷函数
    pef = compile_intent(
        goal="分析华东区 Q3 销售数据",
        user_id="sales_manager",
        capabilities=["query_sales_data", "analyze_trends"],
        context={"region": "华东", "period": "Q3"},
    )

    print(f"PEF ID: {pef.id}")
    print(f"意图: {pef.intent.goal}")
    print(f"用户: {pef.context.user_id}")
    print(f"能力: {pef.get_capability_names()}")
    print()


def example_2_serialize_pef():
    """示例 2: 序列化 PEF"""
    print("=" * 60)
    print("示例 2: 序列化 PEF")
    print("=" * 60)

    pef = PEF(
        intent=IntentDeclaration(
            goal="生成月度报告",
            output_format="markdown",
        ),
        context=ContextBinding(
            user_id="report_user",
            business_context={"month": "2024-03"},
        ),
        capabilities=[
            CapabilityBinding(name="generate_report"),
        ],
    )

    # 导出为 YAML
    print("YAML 格式:")
    print("-" * 60)
    print(pef.to_yaml()[:300] + "...")
    print()

    # 导出为 JSON
    print("JSON 格式:")
    print("-" * 60)
    print(pef.to_json()[:300] + "...")
    print()


def example_3_file_io():
    """示例 3: 文件 I/O"""
    print("=" * 60)
    print("示例 3: 文件 I/O")
    print("=" * 60)

    # 创建 PEF
    pef = PEF(
        intent=IntentDeclaration(goal="文件 I/O 示例"),
        context=ContextBinding(user_id="test_user"),
        capabilities=[CapabilityBinding(name="test_capability")],
    )

    # 保存到文件
    output_file = Path("/tmp/example.pef.yaml")
    save_pef(pef, output_file)
    print(f"✓ 保存到: {output_file}")

    # 从文件加载
    loaded_pef = load_pef(output_file)
    print(f"✓ 从文件加载: {loaded_pef.intent.goal}")
    print()

    # 清理
    output_file.unlink()


def example_4_validation():
    """示例 4: 验证 PEF"""
    print("=" * 60)
    print("示例 4: 验证 PEF")
    print("=" * 60)

    # 有效的 PEF
    valid_pef = PEF(
        intent=IntentDeclaration(goal="有效意图"),
        context=ContextBinding(user_id="valid_user"),
    )
    errors = valid_pef.validate()
    print(f"有效 PEF 验证: {len(errors)} 个错误")

    # 无效的 PEF
    invalid_pef = PEF(
        intent=IntentDeclaration(goal=""),  # 缺少 goal
        context=ContextBinding(user_id=""),  # 缺少 user_id
    )
    errors = invalid_pef.validate()
    print(f"无效 PEF 验证: {len(errors)} 个错误")
    for err in errors:
        print(f"  - {err}")
    print()


def example_5_workflow():
    """示例 5: 工作流"""
    print("=" * 60)
    print("示例 5: 工作流")
    print("=" * 60)

    pef = PEF(
        intent=IntentDeclaration(goal="数据分析工作流"),
        context=ContextBinding(user_id="analyst"),
        capabilities=[
            CapabilityBinding(name="query_data"),
            CapabilityBinding(name="analyze"),
            CapabilityBinding(name="visualize"),
        ],
        workflow=WorkflowDefinition(
            steps=[
                WorkflowStep(
                    id="query",
                    name="查询数据",
                    capability="query_data",
                    output_var="data",
                ),
                WorkflowStep(
                    id="analyze",
                    name="分析数据",
                    capability="analyze",
                    depends_on=["query"],
                    output_var="analysis",
                ),
                WorkflowStep(
                    id="visualize",
                    name="可视化",
                    capability="visualize",
                    depends_on=["analyze"],
                    output_var="visualization",
                ),
            ]
        ),
    )

    print(f"工作流步骤: {len(pef.workflow.steps)}")
    for step in pef.workflow.steps:
        deps = f" (依赖: {', '.join(step.depends_on)})" if step.depends_on else ""
        print(f"  - {step.name}{deps}")
    print()


def example_6_v1_compatibility():
    """示例 6: v1.0 兼容"""
    print("=" * 60)
    print("示例 6: v1.0 兼容")
    print("=" * 60)

    from intentos.agent.compiler import PEF as PEFv1

    # 创建 v1.0 PEF
    v1_pef = PEFv1(
        intent="v1.0 兼容示例",
        capabilities=["cap1", "cap2"],
        metadata={"user_id": "v1_user"},
    )

    print(f"v1.0 PEF: {v1_pef.intent}")

    # 转换为 v2.0
    v2_pef = PEF.from_v1(v1_pef)
    print(f"转换为 v2.0: {v2_pef.intent.goal}")
    print(f"能力: {v2_pef.get_capability_names()}")

    # 转换回 v1.0
    v1_converted = v2_pef.to_v1()
    print(f"转换回 v1.0: {v1_converted.intent}")
    print()


def example_7_compiler_v2():
    """示例 7: 编译器 v2.0"""
    print("=" * 60)
    print("示例 7: 编译器 v2.0")
    print("=" * 60)

    compiler = IntentCompilerV2()

    # 编译简单意图
    pef = compiler.compile(
        goal="分析销售趋势",
        user_id="analyst",
        capabilities=["query_sales", "analyze_trends"],
        context={"region": "华东"},
    )

    print(f"编译结果:")
    print(f"  ID: {pef.id}")
    print(f"  意图: {pef.intent.goal}")
    print(f"  能力: {len(pef.capabilities)} 个")
    print(f"  约束: {pef.constraints.get('execution', {})}")

    # 查看编译统计
    stats = compiler.get_stats()
    print(f"  编译次数: {stats['compile_count']}")
    print()


def example_8_load_example_file():
    """示例 8: 加载示例文件"""
    print("=" * 60)
    print("示例 8: 加载示例文件")
    print("=" * 60)

    example_file = Path(__file__).parent / "sales_analysis.pef.yaml"

    if example_file.exists():
        pef = load_pef(example_file)
        print(f"加载文件: {example_file.name}")
        print(f"  意图: {pef.intent.goal}")
        print(f"  用户: {pef.context.user_id}")
        print(f"  能力: {len(pef.capabilities)} 个")
        if pef.workflow:
            print(f"  工作流: {len(pef.workflow.steps)} 步")

        # 验证
        errors = pef.validate()
        if errors:
            print(f"  验证错误: {len(errors)}")
            for err in errors[:3]:
                print(f"    - {err}")
        else:
            print("  ✓ 验证通过")
    else:
        print(f"示例文件不存在: {example_file}")
    print()


def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "PEF v2.0 使用示例" + " " * 24 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    example_1_create_pef()
    example_2_serialize_pef()
    example_3_file_io()
    example_4_validation()
    example_5_workflow()
    example_6_v1_compatibility()
    example_7_compiler_v2()
    example_8_load_example_file()

    print("=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
