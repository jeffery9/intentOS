# -*- coding: utf-8 -*-
"""
IntentOS Meditation Layer Tests

测试冥想层功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from intentos.memory.models import MemoryEntry, MemoryContentType, SessionMemory, Pattern
from intentos.meditation.engine import MeditationEngine, MeditationConfig, MeditationResult
from intentos.meditation.merger import MemoryMerger
from intentos.meditation.conflict_resolver import ConflictResolver
from intentos.meditation.pruner import MemoryPruner


class TestMemoryMerger:
    """测试记忆合并器"""

    def test_merge_duplicates_empty(self):
        """空列表合并"""
        merger = MemoryMerger()
        merged, count = merger.merge_duplicates([])
        assert merged == []
        assert count == 0

    def test_merge_duplicates_single(self):
        """单条记忆合并"""
        merger = MemoryMerger()
        memory = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="测试内容",
        )
        merged, count = merger.merge_duplicates([memory])
        assert len(merged) == 1
        assert count == 0

    def test_merge_similar_memories(self):
        """合并相似记忆"""
        merger = MemoryMerger(similarity_threshold=0.6)
        
        # 创建两条相似记忆
        mem1 = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="使用 Python 处理文件",
            tags=["python", "file"],
            importance=6.0,
        )
        mem2 = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="用 Python 处理文件操作",
            tags=["python", "file"],
            importance=7.0,
        )
        
        merged, count = merger.merge_duplicates([mem1, mem2])
        
        # 应该合并为一条
        assert len(merged) == 1
        assert count == 1
        
        # 合并后的重要性应该更高
        assert merged[0].importance >= max(mem1.importance, mem2.importance)

    def test_merge_preserves_different_types(self):
        """不同类型记忆不合并"""
        merger = MemoryMerger()
        
        mem1 = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="成功完成任务",
        )
        mem2 = MemoryEntry(
            memory_type=MemoryContentType.FAILURE,
            content="成功完成任务",  # 内容相同但类型不同
        )
        
        merged, count = merger.merge_duplicates([mem1, mem2])
        
        # 不同类型不应合并
        assert len(merged) == 2
        assert count == 0


class TestConflictResolver:
    """测试矛盾解决器"""

    def test_resolve_conflicts_empty(self):
        """空列表解决矛盾"""
        resolver = ConflictResolver()
        resolved, count = resolver.resolve_conflicts([])
        assert resolved == []
        assert count == 0

    def test_detect_contradiction_keywords(self):
        """检测否定词矛盾"""
        resolver = ConflictResolver()
        
        mem1 = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="这个方法可行",
        )
        mem2 = MemoryEntry(
            memory_type=MemoryContentType.FAILURE,
            content="这个方法不可行",
        )
        
        # 应该检测到矛盾
        assert resolver._are_contradictory(mem1, mem2) is True

    def test_no_contradiction_same_sentiment(self):
        """相同表述不矛盾"""
        resolver = ConflictResolver()
        
        mem1 = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="使用 touch 创建文件",
        )
        mem2 = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="用 touch 命令创建文件",
        )
        
        # 不应检测为矛盾
        assert resolver._are_contradictory(mem1, mem2) is False

    def test_select_winner_by_importance(self):
        """按重要性选择获胜者"""
        resolver = ConflictResolver()
        
        mem1 = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="方案 A",
            importance=5.0,
        )
        mem2 = MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="方案 B",
            importance=8.0,
        )
        
        winner = resolver._select_winner([mem1, mem2])
        assert winner == mem2


class TestMemoryPruner:
    """测试记忆剪枝器"""

    def test_prune_empty(self):
        """空列表剪枝"""
        pruner = MemoryPruner()
        pruned, count = pruner.prune_outdated([])
        assert pruned == []
        assert count == 0

    def test_prune_old_low_importance(self):
        """淘汰过期且低重要性的记忆"""
        pruner = MemoryPruner(retention_days=30, min_importance=5.0)
        
        # 旧的低重要性记忆
        old_memory = MemoryEntry(
            memory_type=MemoryContentType.CONTEXT,
            content="旧内容",
            importance=3.0,
            timestamp=datetime.now() - timedelta(days=60),
        )
        
        pruned, count = pruner.prune_outdated([old_memory])
        
        assert len(pruned) == 0
        assert count == 1

    def test_keep_recent_low_importance(self):
        """保留最近的低重要性记忆"""
        pruner = MemoryPruner(retention_days=30, min_importance=5.0)
        
        # 新的低重要性记忆（内容足够长，不是低质量）
        new_memory = MemoryEntry(
            memory_type=MemoryContentType.CONTEXT,
            content="这是一个新的记忆内容，有足够的长度来避免被判定为低质量",
            importance=3.0,
            timestamp=datetime.now(),
            tags=["test"],
        )
        
        pruned, count = pruner.prune_outdated([new_memory])
        
        # 应该保留
        assert len(pruned) == 1
        assert count == 0

    def test_keep_high_importance_old(self):
        """保留高重要性的旧记忆"""
        pruner = MemoryPruner(retention_days=30, min_importance=5.0)
        
        # 旧的高重要性记忆（内容足够长，不是低质量）
        old_memory = MemoryEntry(
            memory_type=MemoryContentType.PATTERN,
            content="这是一个重要的原则，内容足够长来避免被判定为低质量",
            importance=9.0,
            timestamp=datetime.now() - timedelta(days=60),
            tags=["principle"],
        )
        
        pruned, count = pruner.prune_outdated([old_memory])
        
        # 应该保留（高重要性覆盖时间过期）
        assert len(pruned) == 1
        assert count == 0

    def test_prune_low_quality(self):
        """淘汰低质量记忆"""
        pruner = MemoryPruner()
        
        # 低质量记忆：内容太短
        low_quality = MemoryEntry(
            memory_type=MemoryContentType.CONTEXT,
            content="短",  # 太短
            importance=5.0,
            timestamp=datetime.now(),
        )
        
        pruned, count = pruner.prune_outdated([low_quality])
        
        assert len(pruned) == 0
        assert count == 1


class TestMeditationEngine:
    """测试冥想引擎"""

    def test_engine_init(self):
        """引擎初始化"""
        config = MeditationConfig(session_threshold=3)
        engine = MeditationEngine(config)
        
        assert engine.config.session_threshold == 3
        assert engine.get_pending_count() == 0

    def test_add_session_triggers_meditation(self):
        """添加会话触发冥想"""
        config = MeditationConfig(session_threshold=2)
        engine = MeditationEngine(config)
        
        # 添加第一个 session
        session1 = SessionMemory(session_id="session_001")
        triggered = engine.add_session(session1)
        assert triggered is False
        assert engine.get_pending_count() == 1
        
        # 添加第二个 session，应触发冥想
        session2 = SessionMemory(session_id="session_002")
        triggered = engine.add_session(session2)
        assert triggered is True
        assert engine.get_pending_count() == 2

    def test_meditate_process(self):
        """冥想处理流程"""
        config = MeditationConfig(
            session_threshold=2,
            auto_merge=True,
            auto_resolve_conflicts=True,
            auto_prune=True,
        )
        engine = MeditationEngine(config)
        
        # 添加会话
        session1 = SessionMemory(session_id="session_001")
        session1.add_memory_entry(MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="成功经验 1",
            importance=7.0,
        ))
        
        session2 = SessionMemory(session_id="session_002")
        session2.add_memory_entry(MemoryEntry(
            memory_type=MemoryContentType.SUCCESS,
            content="成功经验 2",
            importance=8.0,
        ))
        
        engine.add_session(session1)
        engine.add_session(session2)
        
        # 执行冥想
        result = asyncio.run(engine.meditate())
        
        assert isinstance(result, MeditationResult)
        assert result.sessions_processed == 2
        assert result.memories_processed == 2

    def test_distill_principles(self):
        """提炼核心原则"""
        engine = MeditationEngine()
        
        # 创建多条包含相同模式的记忆
        memories = [
            MemoryEntry(
                memory_type=MemoryContentType.SUCCESS,
                content=f"经验 {i}",
                importance=8.0,
                patterns=[Pattern(
                    name="测试模式",
                    description="共同的模式",
                    occurrences=1,
                )],
            )
            for i in range(3)
        ]
        
        principles = engine._distill_principles(memories)
        
        # 应该提炼出原则
        assert len(principles) >= 1

    def test_meditation_result_dict(self):
        """冥想结果序列化"""
        result = MeditationResult(
            sessions_processed=5,
            memories_processed=20,
            memories_merged=3,
            conflicts_resolved=2,
            memories_pruned=5,
        )
        
        data = result.to_dict()
        
        assert data["sessions_processed"] == 5
        assert data["memories_processed"] == 20
        assert "timestamp" in data


class TestMeditationIntegration:
    """冥想层集成测试"""

    def test_full_meditation_cycle(self):
        """完整冥想周期"""
        config = MeditationConfig(session_threshold=3)
        engine = MeditationEngine(config)
        
        # 模拟 3 个会话
        for i in range(3):
            session = SessionMemory(session_id=f"session_{i:03d}")
            session.add_memory_entry(MemoryEntry(
                memory_type=MemoryContentType.SUCCESS,
                content=f"会话 {i} 的成功经验",
                importance=6.0 + i,
                tags=[f"tag{i}"],
            ))
            
            triggered = engine.add_session(session)
            if i < 2:
                assert triggered is False
            else:
                assert triggered is True
        
        # 执行冥想
        result = asyncio.run(engine.meditate())
        
        # 验证结果
        assert result.sessions_processed == 3
        assert result.memories_processed == 3
        assert engine.get_pending_count() == 0  # 队列已清空


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
