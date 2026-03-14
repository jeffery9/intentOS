"""
真实 LLM 后端演示

演示如何使用不同的 LLM 提供商:
- OpenAI
- Anthropic
- Ollama (本地)
- 多后端路由
"""

import asyncio
import os

from intentos.llm import (
    BackendConfig,
    Message,
    ToolDefinition,
    create_executor,
    create_router,
)


async def demo_mock():
    """演示 Mock 后端"""
    print("=" * 60)
    print("演示 1: Mock 后端 (测试用)")
    print("=" * 60)

    executor = create_executor(provider="mock")

    messages = [
        Message.system("你是一个有用的助手"),
        Message.user("帮我分析一下销售数据"),
    ]

    response = await executor.execute(messages)

    print(f"模型：{response.model}")
    print(f"响应：{response.content[:100]}...")
    print(f"Token 使用：{response.usage.total_tokens}")
    print(f"延迟：{response.latency_ms}ms")
    print()


async def demo_openai():
    """演示 OpenAI 后端"""
    print("=" * 60)
    print("演示 2: OpenAI 后端")
    print("=" * 60)

    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        print("⚠️  未设置 OPENAI_API_KEY 环境变量，跳过此演示")
        print("   设置方法：export OPENAI_API_KEY=sk-...")
        print()
        return

    executor = create_executor(
        provider="openai",
        model="gpt-4o-mini",
        api_key=api_key,
    )

    messages = [
        Message.system("你是一个有用的助手，用简洁的语言回答"),
        Message.user("什么是 AI 原生软件？请用一句话回答"),
    ]

    try:
        response = await executor.execute(messages, max_tokens=100)

        print(f"模型：{response.model}")
        print(f"响应：{response.content}")
        print(f"Token 使用：{response.usage}")
        print(f"延迟：{response.latency_ms}ms")
    except Exception as e:
        print(f"❌ 错误：{e}")

    print()


async def demo_anthropic():
    """演示 Anthropic 后端"""
    print("=" * 60)
    print("演示 3: Anthropic 后端")
    print("=" * 60)

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("⚠️  未设置 ANTHROPIC_API_KEY 环境变量，跳过此演示")
        print("   设置方法：export ANTHROPIC_API_KEY=...")
        print()
        return

    executor = create_executor(
        provider="anthropic",
        model="claude-3-haiku-20240307",
        api_key=api_key,
    )

    messages = [
        Message.system("你是一个有用的助手"),
        Message.user("什么是 IntentOS？请用一句话回答"),
    ]

    try:
        response = await executor.execute(messages, max_tokens=100)

        print(f"模型：{response.model}")
        print(f"响应：{response.content}")
        print(f"Token 使用：{response.usage}")
        print(f"延迟：{response.latency_ms}ms")
    except Exception as e:
        print(f"❌ 错误：{e}")

    print()


async def demo_ollama():
    """演示 Ollama 后端"""
    print("=" * 60)
    print("演示 4: Ollama 后端 (本地模型)")
    print("=" * 60)

    executor = create_executor(
        provider="ollama",
        model="llama3.1",
        base_url="http://localhost:11434",
    )

    messages = [
        Message.user("你好，请介绍一下自己"),
    ]

    try:
        response = await executor.execute(messages, max_tokens=100)

        print(f"模型：{response.model}")
        print(f"响应：{response.content[:100]}...")
        print(f"Token 使用：{response.usage}")
        print(f"延迟：{response.latency_ms}ms")
    except Exception as e:
        print(f"❌ 错误：{e}")
        print("   确保 Ollama 正在运行：ollama serve")

    print()


async def demo_tool_calling():
    """演示工具调用"""
    print("=" * 60)
    print("演示 5: 工具调用 (Function Calling)")
    print("=" * 60)

    executor = create_executor(provider="mock")

    # 定义工具
    tools = [
        ToolDefinition(
            name="query_sales",
            description="查询销售数据",
            parameters={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "string",
                        "description": "区域名称",
                    },
                    "period": {
                        "type": "string",
                        "description": "时间段",
                    },
                },
                "required": ["region"],
            },
        ),
    ]

    messages = [
        Message.system("你是一个销售分析助手"),
        Message.user("帮我查询华东区 Q3 的销售数据"),
    ]

    response = await executor.execute(messages, tools=tools)

    print(f"响应内容：{response.content}")
    print(f"工具调用：{response.tool_calls}")
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"  - 调用工具：{tc.name}")
            print(f"    参数：{tc.arguments}")

    print()


async def demo_router():
    """演示多后端路由"""
    print("=" * 60)
    print("演示 6: 多后端路由和故障转移")
    print("=" * 60)

    # 创建路由器配置
    configs = [
        BackendConfig(
            name="primary",
            model="gpt-4o-mini",
            api_key=os.environ.get("OPENAI_API_KEY"),
            priority=10,
        ),
        BackendConfig(
            name="backup",
            model="claude-3-haiku-20240307",
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
            priority=5,
        ),
        BackendConfig(
            name="local",
            model="llama3.1",
            base_url="http://localhost:11434",
            priority=1,
        ),
    ]

    router = create_router(configs)

    messages = [
        Message.user("你好"),
    ]

    try:
        response = await router.generate(messages)

        print(f"✅ 响应：{response.content[:50]}...")
        print(f"   延迟：{response.latency_ms}ms")

        # 显示统计
        stats = router.get_stats()
        print("\n后端统计:")
        for name, s in stats.items():
            print(
                f"  {name}: {s['success_rate']:.1f}% 成功率，{s['avg_latency_ms']:.0f}ms 平均延迟"
            )

    except Exception as e:
        print(f"❌ 错误：{e}")

    print()


async def demo_streaming():
    """演示流式输出"""
    print("=" * 60)
    print("演示 7: 流式输出")
    print("=" * 60)

    executor = create_executor(provider="mock")

    messages = [
        Message.user("请用 50 字介绍人工智能"),
    ]

    print("流式输出：", end="", flush=True)

    async for chunk in executor.generate_stream(messages):
        print(chunk, end="", flush=True)

    print("\n")


async def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print("LLM 后端集成演示")
    print("支持：OpenAI, Anthropic, Ollama, 多后端路由")
    print("=" * 70 + "\n")

    # Mock 后端 (总是可用)
    await demo_mock()

    # 真实后端 (需要 API Key)
    await demo_openai()
    await demo_anthropic()
    await demo_ollama()

    # 高级功能
    await demo_tool_calling()
    await demo_router()
    await demo_streaming()

    print("=" * 70)
    print("演示完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
