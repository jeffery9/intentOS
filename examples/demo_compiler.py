"""
IntentOS 编译器演示
展示意图 → Prompt 编译和 LLM 执行流程
"""

import asyncio

from intentos import (
    Capability,
    Context,
    Intent,
    IntentCompiler,
    IntentOS,
    IntentType,
    LLMExecutor,
)


async def demo_compiler():
    """演示编译器功能"""
    print("=" * 60)
    print("演示 1: 意图编译器 - 将结构化意图编译为 Prompt")
    print("=" * 60)

    os = IntentOS()
    os.initialize()

    # 创建一个结构化意图
    intent = Intent(
        name="sales_analysis",
        intent_type=IntentType.COMPOSITE,
        goal="分析华东区 Q3 销售数据并生成报告",
        description="销售数据分析任务",
        context=Context(user_id="manager_001", user_role="manager"),
        params={
            "region": "华东",
            "period": "Q3",
            "metrics": ["revenue", "growth", "market_share"],
        },
        constraints={
            "data_sensitivity": "confidential",
            "output_format": "executive_dashboard",
        },
    )

    # 编译意图为 Prompt
    compiler = IntentCompiler(os.registry)
    compiled = compiler.compile(intent)

    print("\n📋 编译后的 System Prompt:")
    print("-" * 40)
    print(compiled.system_prompt[:1000] + "...")

    print("\n💬 编译后的 User Prompt:")
    print("-" * 40)
    print(compiled.user_prompt)

    print("\n📊 编译元数据:")
    print(f"  - 模板：{compiled.metadata['template']}")
    print(f"  - 意图类型：{compiled.metadata['intent_type']}")

    # 演示 JSON 格式编译
    print("\n📄 JSON 格式 Prompt:")
    print("-" * 40)
    json_prompt = compiler.compile_to_json(intent)
    print(json_prompt[:500] + "...")


async def demo_llm_execution():
    """演示 LLM 执行"""
    print("\n" + "=" * 60)
    print("演示 2: LLM 执行 - 使用编译后的 Prompt 调用 LLM")
    print("=" * 60)

    os = IntentOS()
    os.initialize()

    # 创建意图
    intent = Intent(
        name="customer_insight",
        intent_type=IntentType.ATOMIC,
        goal="分析客户流失原因",
        context=Context(user_id="analyst_001", user_role="analyst"),
        params={
            "segment": "enterprise",
            "time_range": "last_6_months",
        },
    )

    # 创建编译器
    compiler = IntentCompiler(os.registry)
    compiled = compiler.compile(intent)

    # 创建 LLM 执行器（使用 mock 模式）
    llm = LLMExecutor(provider="mock")

    print("\n🔮 调用 LLM 执行...")
    response = await llm.execute(compiled)

    print("\n✅ LLM 响应内容:")
    print(f"  {response.content}")

    print("\n📊 解析结果:")
    print(f"  {response.parsed_result}")


async def demo_tool_calling():
    """演示工具调用"""
    print("\n" + "=" * 60)
    print("演示 3: 工具调用 - LLM 决定调用哪些能力")
    print("=" * 60)

    os = IntentOS()
    os.initialize()

    # 注册一个工具能力
    def send_email(context, to: str, subject: str, body: str) -> dict:
        return {
            "status": "sent",
            "to": to,
            "subject": subject,
        }

    email_cap = Capability(
        name="send_email",
        description="发送邮件通知",
        input_schema={"to": "string", "subject": "string", "body": "string"},
        output_schema={"status": "string"},
        func=send_email,
        tags=["notification"],
    )
    os.registry.register_capability(email_cap)

    # 创建意图
    intent = Intent(
        name="notify_team",
        intent_type=IntentType.ATOMIC,
        goal="发送项目完成通知给团队",
        context=Context(user_id="pm_001", user_role="project_manager"),
        params={
            "to": "team@example.com",
            "subject": "项目完成通知",
            "body": "项目已按时完成",
        },
    )

    # 编译并执行
    compiler = IntentCompiler(os.registry)
    compiled = compiler.compile(intent)

    llm = LLMExecutor(provider="mock")

    print("\n🔮 调用 LLM (带工具调用)...")
    response = await llm.execute(compiled)

    print("\n✅ 响应:")
    print(f"  内容：{response.content}")
    print(f"  工具调用：{response.tool_calls}")


async def demo_full_pipeline():
    """演示完整流程：自然语言 → 意图 → Prompt → LLM → 执行"""
    print("\n" + "=" * 60)
    print("演示 4: 完整流程 - 从自然语言到执行结果")
    print("=" * 60)

    # 创建带 LLM 执行的 IntentOS
    os = IntentOS()
    os.initialize()

    # 启用 LLM 执行模式
    os.interface.engine.use_llm = True

    print("\n📝 用户输入：帮我分析一下上季度的销售数据")

    # 执行
    result = await os.execute("帮我分析一下上季度的销售数据")

    print("\n✅ 执行结果:")
    print(f"  {result}")

    # 查看对话历史
    history = os.interface.get_history()
    print("\n📜 对话历史:")
    for turn in history:
        print(f"  [{turn.role}]: {turn.content[:50]}...")


async def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print("IntentOS 编译器演示")
    print("意图 → Prompt → LLM → 执行")
    print("=" * 70 + "\n")

    await demo_compiler()
    await demo_llm_execution()
    await demo_tool_calling()
    await demo_full_pipeline()

    print("\n" + "=" * 70)
    print("演示完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
