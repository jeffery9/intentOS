"""
IntentOS 示例应用
演示如何使用 IntentOS 构建 AI 原生应用
"""

import asyncio

from intentos import Capability, Context, IntentOS, IntentStep, IntentTemplate, IntentType


async def example_basic():
    """基础示例：简单对话"""
    print("=" * 50)
    print("示例 1: 基础对话")
    print("=" * 50)

    os = IntentOS()
    os.initialize()

    # 执行指令
    result = await os.execute("查询销售数据")
    print("用户：查询销售数据")
    print(f"系统：{result}")
    print()


async def example_sales_analysis():
    """销售分析示例"""
    print("=" * 50)
    print("示例 2: 销售分析")
    print("=" * 50)

    os = IntentOS()
    os.initialize()

    # 设置用户权限
    os.interface.set_user(
        user_id="sales_manager_001",
        role="manager",
        permissions=["read_sales_data", "generate_report"],
    )

    # 执行分析指令
    result = await os.execute("分析华东区 Q3 销售数据")
    print("用户：分析华东区 Q3 销售数据")
    print(f"系统：{result}")
    print()

    # 查看系统注册信息
    print("系统能力注册:")
    introspect = os.registry_introspect
    for name, info in introspect["capabilities"].items():
        print(f"  - {name}: {info['description']}")
    print()


async def example_custom_capability():
    """自定义能力示例"""
    print("=" * 50)
    print("示例 3: 注册自定义能力")
    print("=" * 50)

    os = IntentOS()
    os.initialize()

    # 定义自定义能力
    def calculate_metric(context: Context, metric_name: str, value: float) -> dict:
        """计算指标"""
        return {
            "metric": metric_name,
            "value": value,
            "status": "good" if value > 0.8 else "needs_attention",
        }

    custom_cap = Capability(
        name="calculate_metric",
        description="计算业务指标",
        input_schema={"metric_name": "string", "value": "number"},
        output_schema={"metric": "string", "value": "number", "status": "string"},
        func=calculate_metric,
        tags=["metric", "analysis"],
    )

    os.registry.register_capability(custom_cap)
    print("已注册能力：calculate_metric")

    # 使用新能力
    result = await os.execute("计算客户满意度指标 0.85")
    print("用户：计算客户满意度指标 0.85")
    print(f"系统：{result}")
    print()


async def example_composite_intent():
    """复合意图示例"""
    print("=" * 50)
    print("示例 4: 复合意图 - 月度复盘")
    print("=" * 50)

    os = IntentOS()
    os.initialize()

    # 注册复合意图模板
    monthly_review_template = IntentTemplate(
        name="monthly_review",
        description="生成月度复盘报告",
        intent_type=IntentType.COMPOSITE,
        params_schema={
            "month": "string",
            "department": "string",
        },
        steps=[
            IntentStep(
                capability_name="query_data",
                params={"source": "performance", "month": "{{month}}", "dept": "{{department}}"},
                output_var="performance_data",
            ),
            IntentStep(
                capability_name="analyze_data",
                params={"data": "${performance_data}", "method": "monthly"},
                output_var="analysis",
            ),
            IntentStep(
                capability_name="generate_report",
                params={"title": "{{month}} 复盘报告", "content": "${analysis}"},
                output_var="final_report",
            ),
        ],
        tags=["review", "report"],
    )

    os.registry.register_template(monthly_review_template)
    print("已注册模板：monthly_review")

    # 执行复合意图
    result = await os.execute("生成 12 月技术部复盘报告")
    print("用户：生成 12 月技术部复盘报告")
    print(f"系统：{result}")
    print()


async def example_meta_intent():
    """元意图示例 - 系统自管理"""
    print("=" * 50)
    print("示例 5: 元意图 - 系统自管理")
    print("=" * 50)

    os = IntentOS()
    os.initialize()

    # 设置管理员权限
    os.interface.set_user(
        user_id="admin",
        role="admin",
        permissions=["admin"],
    )

    # 查看系统当前状态
    print("当前系统注册信息:")
    introspect = os.registry_introspect
    print(f"  模板数量：{len(introspect['templates'])}")
    print(f"  能力数量：{len(introspect['capabilities'])}")
    print()

    # 动态注册新能力（元意图）
    def send_notification(context: Context, message: str, channel: str = "email") -> dict:
        return {
            "status": "sent",
            "channel": channel,
            "message": message,
        }

    notify_cap = Capability(
        name="send_notification",
        description="发送通知",
        input_schema={"message": "string", "channel": "string"},
        output_schema={"status": "string", "channel": "string"},
        func=send_notification,
        tags=["notification", "communication"],
    )

    os.registry.register_capability(notify_cap)
    print("通过元意图注册了新能力：send_notification")

    # 再次查看系统状态
    introspect = os.registry_introspect
    print(f"  模板数量：{len(introspect['templates'])}")
    print(f"  能力数量：{len(introspect['capabilities'])}")
    print()


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("IntentOS 原型演示")
    print("AI 原生软件范式：语言即系统")
    print("=" * 60 + "\n")

    await example_basic()
    await example_sales_analysis()
    await example_custom_capability()
    await example_composite_intent()
    await example_meta_intent()

    print("=" * 60)
    print("演示完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
