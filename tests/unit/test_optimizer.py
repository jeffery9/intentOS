# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

import pytest

from intentos.compiler.optimizer import (
    CompilationStrategy,
    ContextManager,
    DataLocalityOptimizer,
    LLMProfile,
    LLMProvider,
    MapReduceOptimizer,
    MapReduceStrategy,
    NodeCapability,
    PromptOptimizer,
    StrategySelector,
    TokenOptimizer,
    get_llm_profile,
)


# Mock CompiledPrompt since it's only used for typing or simple attribute access
class MockCompiledPrompt:
    def __init__(self, system_prompt, user_prompt, intent=None, metadata=None):
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.intent = intent
        self.metadata = metadata or {}


class TestLLMProfile:
    """LLMProfile 测试"""

    def test_is_suitable(self):
        profile = LLMProfile(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            max_context_size=8192,
            max_output_tokens=4096,
            supports_tools=True,
        )
        assert profile.is_suitable_for("simple") is True
        assert profile.is_suitable_for("medium") is True
        assert profile.is_suitable_for("complex") is False  # requires 16000

    def test_estimate_cost(self):
        profile = LLMProfile(
            provider=LLMProvider.OPENAI,
            model="m",
            max_context_size=1000,
            max_output_tokens=100,
            input_cost_usd=0.01,
            output_cost_usd=0.02,
        )
        cost = profile.estimate_cost(1000, 2000)
        assert cost == pytest.approx(0.05)


class TestPromptOptimizer:
    """PromptOptimizer 测试"""

    @pytest.fixture
    def optimizer(self):
        profile = LLMProfile(
            provider=LLMProvider.OPENAI,
            model="m",
            max_context_size=1000,
            max_output_tokens=100,
            supports_json_mode=True,
            preferred_format="json",
        )
        return PromptOptimizer(profile)

    @pytest.fixture
    def compiled_prompt(self):
        intent = MagicMock()
        intent.to_dict.return_value = {"name": "test"}
        return MockCompiledPrompt("System prompt", "User prompt", intent=intent)

    def test_optimize_json_mode(self, optimizer, compiled_prompt):
        # We need to patch the import in the optimizer method
        with patch("intentos.compiler.compiler.CompiledPrompt", MockCompiledPrompt):
            optimized = optimizer.optimize(compiled_prompt)
            assert "JSON" in optimized.system_prompt

    def test_optimize_format_text(self, compiled_prompt):
        profile = LLMProfile(
            provider=LLMProvider.OPENAI,
            model="m",
            max_context_size=1000,
            max_output_tokens=100,
            preferred_format="text",
        )
        optimizer = PromptOptimizer(profile)
        compiled_prompt.system_prompt = "```json {key:val} ```"
        with patch("intentos.compiler.compiler.CompiledPrompt", MockCompiledPrompt):
            optimized = optimizer.optimize(compiled_prompt)
            assert "```json" not in optimized.system_prompt

    def test_optimize_format_yaml(self, optimizer, compiled_prompt):
        optimizer.profile.preferred_format = "yaml"
        with patch("intentos.compiler.compiler.CompiledPrompt", MockCompiledPrompt):
            optimized = optimizer.optimize(compiled_prompt)
            assert "YAML" in optimized.system_prompt

    def test_trim_prompt(self, optimizer, compiled_prompt):
        compiled_prompt.system_prompt = "A" * 3000
        with patch("intentos.compiler.compiler.CompiledPrompt", MockCompiledPrompt):
            optimized = optimizer.optimize(compiled_prompt, target_tokens=10)
            assert len(optimized.system_prompt) < 3000
            assert "..." in optimized.system_prompt


class TestStrategySelector:
    """StrategySelector 测试"""

    def test_select_strategy(self):
        profile = get_llm_profile("gpt-4o")
        selector = StrategySelector(profile)
        assert selector.select_strategy("simple") == CompilationStrategy.FAST
        assert selector.select_strategy("medium") == CompilationStrategy.STANDARD
        assert selector.select_strategy("complex") == CompilationStrategy.OPTIMIZED

    def test_estimate_time(self):
        profile = get_llm_profile("gpt-4o")
        selector = StrategySelector(profile)
        assert selector.estimate_compilation_time(CompilationStrategy.FAST) == 0.01
        assert selector.estimate_compilation_time(CompilationStrategy.OPTIMIZED) == 1.0


class TestTokenOptimizer:
    """TokenOptimizer 测试"""

    def test_compress_prompt_level1(self):
        text = "hello    world\n\nagain"
        compressed = TokenOptimizer.compress_prompt(text, compression_level=1)
        assert "  " not in compressed
        assert "\n\n" not in compressed

    def test_compress_prompt_level2(self):
        text = "please configuration"
        compressed = TokenOptimizer.compress_prompt(text, compression_level=2)
        assert "plz" in compressed
        assert "config" in compressed

    def test_compress_prompt_level3(self):
        text = "A" * 600
        compressed = TokenOptimizer.compress_prompt(text, compression_level=3)
        assert len(compressed) <= 503

    def test_batch_intents(self):
        intents = [1, 2, 3, 4, 5]
        batches = TokenOptimizer.batch_intents(intents, max_batch_size=2)
        assert len(batches) == 3
        assert len(batches[0]) == 2
        assert len(batches[2]) == 1


class TestContextManager:
    """ContextManager 测试"""

    def test_add_and_get_context(self):
        cm = ContextManager(max_context_size=100)
        cm.add_entry("k1", "v1", importance=1.0)
        cm.add_entry("k2", "v2", importance=0.5)

        ctx = cm.get_context()
        assert "k1: v1" in ctx
        assert "k2: v2" in ctx

    def test_context_expiration(self):
        cm = ContextManager(max_context_size=100)
        cm.add_entry("k1", "v1", ttl_seconds=-10)  # already expired
        cm.add_entry("k2", "v2", ttl_seconds=10)

        ctx = cm.get_context()
        assert "k1" not in ctx
        assert "k2" in ctx

    def test_context_trimming(self):
        # max_context_size is tokens. text is approx 4 chars/token.
        # so 10 tokens = 40 chars.
        cm = ContextManager(max_context_size=10)
        cm.add_entry("k1", "A" * 30, importance=1.0)
        cm.add_entry("k2", "B" * 30, importance=0.1)

        ctx = cm.get_context()
        assert "k1" in ctx
        assert "k2" not in ctx  # k1 already took most of the space


class TestMapReduceOptimizer:
    """MapReduceOptimizer 测试"""

    @pytest.fixture
    def nodes(self):
        return [
            NodeCapability(node_id="n1", has_llm=True, compute_power=1.0),
            NodeCapability(node_id="n2", has_llm=False, compute_power=0.5),
        ]

    def test_select_strategy(self, nodes):
        optimizer = MapReduceOptimizer(nodes)
        # Small data -> centralized
        assert optimizer.select_strategy(500) == MapReduceStrategy.CENTRALIZED
        # Large data + high LLM ratio (50% is enough here?)
        # 1/2 = 0.5. Code says ratio > 0.5 for MAP_REDUCE.
        # So 0.5 should be HYBRID.
        assert optimizer.select_strategy(2000) == MapReduceStrategy.HYBRID

    def test_plan_map_reduce(self, nodes):
        optimizer = MapReduceOptimizer(nodes)
        memories = {"n1": ["m1", "m2"], "n2": ["m3"]}
        plan = optimizer.plan_map_reduce("test intent", memories)
        assert len(plan["map_tasks"]) == 1  # only n1 has LLM
        assert plan["map_tasks"][0]["node_id"] == "n1"
        assert plan["estimated_network_cost"] > 0  # from n2


class TestDataLocalityOptimizer:
    """DataLocalityOptimizer 测试"""

    def test_calculate_score(self):
        node = NodeCapability(node_id="n1", has_llm=True, has_memory=True)
        score = DataLocalityOptimizer.calculate_data_locality_score(node, [], True)
        assert score == 1.0

        node_no_llm = NodeCapability(node_id="n2", has_llm=False, has_memory=True)
        score2 = DataLocalityOptimizer.calculate_data_locality_score(node_no_llm, [], True)
        assert score2 < 1.0

    def test_select_best_node(self):
        n1 = NodeCapability(node_id="n1", has_llm=True, has_memory=True)
        n2 = NodeCapability(node_id="n2", has_llm=False, has_memory=True)
        best = DataLocalityOptimizer.select_best_node([n1, n2], [], True)
        assert best.node_id == "n1"
