
import pytest
import asyncio
from intentos.llm.executor import BackendConfig, LLMRouter
from intentos.llm.backends.base import Message, LLMRole

@pytest.mark.anyio
async def test_consultant_strategy_easy_task():
    """测试顾问策略：简单任务（由常规模型处理）"""
    
    # 定义配置
    configs = [
        BackendConfig(
            name="regular_model",
            model="gpt-3.5-turbo",
            is_consultant=True,
            priority=10
        ),
        BackendConfig(
            name="high_precision_model",
            model="gpt-4o",
            is_consultant=False,
            priority=5
        )
    ]
    
    router = LLMRouter(configs)
    
    # 模拟简单任务，常规模型直接回答
    messages = [Message.user("你好，请问 1+1 等于几？")]
    
    response = await router.generate(messages, strategy="consultant")
    
    # 验证是否使用了常规模型
    assert response.model == "gpt-3.5-turbo"
    assert "[HARD_TASK]" not in response.content
    
    # 验证统计
    stats = router.get_stats()
    assert stats["regular_model"]["total_requests"] == 1
    assert stats["high_precision_model"]["total_requests"] == 0

@pytest.mark.anyio
async def test_consultant_strategy_hard_task():
    """测试顾问策略：困难任务（由常规模型转向高精度专家）"""
    
    # 定义配置
    from intentos.llm.backends.mock_backend import MockBackend
    
    configs = [
        BackendConfig(
            name="regular",
            model="regular-model",
            is_consultant=True,
            priority=10
        ),
        BackendConfig(
            name="expert",
            model="high-precision-model",
            is_consultant=False,
            priority=5
        )
    ]
    
    router = LLMRouter(configs)
    
    # 注入自定义 Mock 行为
    # 常规模型遇到特定关键词返回 [HARD_TASK]
    def regular_callback(messages, tools):
        for msg in messages:
            if "量子物理" in msg.content:
                return "[HARD_TASK] 这个问题需要极高精度的专家协助。"
        return "这是一个简单问题。"

    router.backends["regular"].response_callback = regular_callback
    
    # 提交困难任务
    messages = [Message.user("请解释量子物理中的纠缠态。")]
    
    response = await router.generate(messages, strategy="consultant")
    
    # 验证是否最终由高精度专家模型回答
    assert response.model == "high-precision-model"
    
    # 验证统计
    stats = router.get_stats()
    assert stats["regular"]["total_requests"] == 1
    assert stats["expert"]["total_requests"] == 1

@pytest.mark.anyio
async def test_consultant_strategy_no_experts():
    """测试顾问测试模式：没有专家模型时的情况"""
    
    configs = [
        BackendConfig(
            name="consultant",
            model="consultant-model",
            is_consultant=True,
            priority=10
        )
    ]
    
    router = LLMRouter(configs)
    
    # 顾问标记为难题
    router.backends["consultant"].response_callback = lambda m, t: "[HARD_TASK] 难题"
    
    messages = [Message.user("困难问题")]
    
    # 即使标记为 HARD，如果没有专家模型，也应该返回顾问的结果
    response = await router.generate(messages, strategy="consultant")
    
    assert response.model == "consultant-model"
    assert "[HARD_TASK]" in response.content
