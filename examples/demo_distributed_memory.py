"""
分布式记忆管理演示
"""

import asyncio
import time

from intentos import (
    MemoryPriority,
    MemoryType,
    create_memory_manager,
)


async def demo_short_term_memory():
    """演示短期记忆"""
    print("=" * 60)
    print("演示 1: 短期记忆 (Short-term Memory)")
    print("=" * 60)

    # 创建记忆管理器（仅短期记忆）
    manager = create_memory_manager(
        short_term_max=1000,
        long_term_enabled=False,
        sync_enabled=False,
    )
    await manager.initialize()

    # 设置记忆
    print("\n设置短期记忆:")
    entry1 = await manager.set_short_term(
        key="user:123:preference",
        value={"theme": "dark", "language": "zh-CN"},
        tags=["user", "preference"],
        priority=MemoryPriority.HIGH,
        ttl_seconds=60,
    )
    print(f"  已设置：{entry1.key}, 过期时间：{entry1.expires_at - time.time():.1f}s")

    # 获取记忆
    print("\n获取记忆:")
    entry = await manager.get_short_term("user:123:preference")
    if entry:
        print(f"  键：{entry.key}")
        print(f"  值：{entry.value}")
        print(f"  访问次数：{entry.access_count}")

    # 按标签检索
    print("\n按标签检索 (tag='user'):")
    entries = await manager.get_by_tag("user")
    for e in entries:
        print(f"  - {e.key}: {e.value}")

    # 搜索
    print("\n搜索记忆 (query='theme'):")
    results = await manager.search("theme")
    for r in results:
        print(f"  - {r.key}: {r.value}")

    # 统计
    stats = await manager.get_stats()
    print("\n统计信息:")
    print(f"  短期记忆数量：{stats.get('short_term_size', 0)}")
    print(f"  命中次数：{stats['hit_count']}")
    print(f"  未命中次数：{stats['miss_count']}")

    await manager.shutdown()


async def demo_long_term_memory():
    """演示长期记忆"""
    print("\n" + "=" * 60)
    print("演示 2: 长期记忆 (Long-term Memory)")
    print("=" * 60)

    # 创建记忆管理器（带长期记忆，使用内存后端模拟）
    manager = create_memory_manager(
        short_term_max=100,
        long_term_enabled=True,
        long_term_backend="file",
        sync_enabled=False,
    )
    await manager.initialize()

    try:
        # 设置长期记忆（实际存储到短期，因为长期后端可能不可用）
        print("\n设置记忆:")
        for i in range(5):
            entry = await manager.set(
                key=f"knowledge:fact:{i}",
                value={
                    "fact": f"这是第{i+1}个知识点",
                    "category": "general",
                    "confidence": 0.9 - i * 0.1,
                },
                memory_type=MemoryType.LONG_TERM,
                tags=["knowledge", "fact"],
                priority=MemoryPriority.NORMAL,
            )
            print(f"  已设置：{entry.key}")

        # 获取记忆
        print("\n获取记忆:")
        entry = await manager.get("knowledge:fact:0")
        if entry:
            print(f"  键：{entry.key}")
            print(f"  值：{entry.value}")
            print(f"  类型：{entry.memory_type.value}")

        # 统计
        stats = await manager.get_stats()
        print("\n统计信息:")
        print(f"  命中次数：{stats['hit_count']}")
        print(f"  未命中次数：{stats['miss_count']}")

    finally:
        await manager.clear()
        await manager.shutdown()


async def demo_memory_priority():
    """演示记忆优先级"""
    print("\n" + "=" * 60)
    print("演示 3: 记忆优先级 (Memory Priority)")
    print("=" * 60)

    manager = create_memory_manager(
        short_term_max=5,  # 小容量测试 LRU
        long_term_enabled=False,
        sync_enabled=False,
    )
    await manager.initialize()

    try:
        # 设置不同优先级的记忆
        print("\n设置记忆（容量限制为 5）:")

        for i in range(7):
            priority = MemoryPriority.CRITICAL if i < 2 else MemoryPriority.NORMAL
            await manager.set_short_term(
                key=f"item:{i}",
                value=f"值{i}",
                priority=priority,
                ttl_seconds=3600,
            )
            print(f"  设置 item:{i}, 优先级：{priority.name}")

        # 检查哪些记忆还在
        print("\n当前记忆:")
        stats = await manager.get_stats()
        print(f"  短期记忆数量：{stats.get('short_term_size', 0)}")

        # 尝试获取所有记忆
        for i in range(7):
            entry = await manager.get(f"item:{i}")
            if entry:
                print(f"  ✓ item:{i} - {entry.value}")
            else:
                print(f"  ✗ item:{i} - 已被淘汰")

    finally:
        await manager.shutdown()


async def demo_distributed_sync():
    """演示分布式同步（模拟）"""
    print("\n" + "=" * 60)
    print("演示 4: 分布式记忆同步 (Distributed Sync)")
    print("=" * 60)

    # 创建两个"节点"
    manager1 = create_memory_manager(
        short_term_max=100,
        long_term_enabled=True,
        long_term_backend="file",
        sync_enabled=False,  # 简化演示，禁用实际同步
        node_id="node-001",
    )

    manager2 = create_memory_manager(
        short_term_max=100,
        long_term_enabled=True,
        long_term_backend="file",
        sync_enabled=False,
        node_id="node-002",
    )

    await manager1.initialize()
    await manager2.initialize()

    try:
        # 在节点 1 设置记忆
        print("\n节点 1 设置记忆:")
        entry = await manager1.set_long_term(
            key="shared:config",
            value={"setting": "value", "version": 1},
            tags=["shared", "config"],
        )
        print(f"  节点 1: {entry.key} = {entry.value}")
        print(f"  节点 ID: {entry.node_id}")

        # 手动"同步"到节点 2（模拟）
        print("\n手动同步到节点 2:")
        entry.node_id = "node-002"
        entry.synced = True
        await manager2.set_long_term(
            key="shared:config",
            value=entry.value,
            tags=entry.tags,
            metadata={"synced_from": "node-001"},
        )

        # 在节点 2 获取
        entry2 = await manager2.get_long_term("shared:config")
        print(f"  节点 2: {entry2.key} = {entry2.value}")
        print(f"  元数据：{entry2.metadata}")

        # 统计
        stats1 = await manager1.get_stats()
        stats2 = await manager2.get_stats()
        print("\n节点统计:")
        print(f"  节点 1 命中：{stats1['hit_count']}, 未命中：{stats1['miss_count']}")
        print(f"  节点 2 命中：{stats2['hit_count']}, 未命中：{stats2['miss_count']}")

    finally:
        await manager1.clear()
        await manager2.clear()
        await manager1.shutdown()
        await manager2.shutdown()


async def demo_memory_expiry():
    """演示记忆过期"""
    print("\n" + "=" * 60)
    print("演示 5: 记忆过期 (Memory Expiry)")
    print("=" * 60)

    manager = create_memory_manager(
        short_term_max=100,
        long_term_enabled=False,
        sync_enabled=False,
    )
    await manager.initialize()

    try:
        # 设置短期过期记忆
        print("\n设置过期记忆 (2 秒后过期):")
        await manager.set_short_term(
            key="temp:data",
            value="临时数据",
            ttl_seconds=2,
        )

        # 立即获取
        entry = await manager.get("temp:data")
        print(f"  立即获取：{entry.value if entry else 'None'}")

        # 等待过期
        print("\n等待 3 秒...")
        await asyncio.sleep(3)

        # 再次获取
        entry = await manager.get("temp:data")
        print(f"  3 秒后获取：{entry.value if entry else 'None'} (已过期)")

    finally:
        await manager.shutdown()


async def demo_memory_tags():
    """演示标签索引"""
    print("\n" + "=" * 60)
    print("演示 6: 标签索引 (Tag Index)")
    print("=" * 60)

    manager = create_memory_manager(
        short_term_max=100,
        long_term_enabled=False,
        sync_enabled=False,
    )
    await manager.initialize()

    try:
        # 设置带标签的记忆
        print("\n设置带标签的记忆:")

        memories = [
            ("doc:1", "文档 1 内容", ["doc", "important", "work"]),
            ("doc:2", "文档 2 内容", ["doc", "archive", "work"]),
            ("note:1", "笔记 1 内容", ["note", "personal"]),
            ("note:2", "笔记 2 内容", ["note", "important", "personal"]),
            ("config:1", "配置 1", ["config", "system"]),
        ]

        for key, value, tags in memories:
            await manager.set_short_term(
                key=key,
                value=value,
                tags=tags,
            )
            print(f"  {key}: tags={tags}")

        # 按标签检索
        print("\n按标签检索:")

        for tag in ["doc", "note", "important", "work"]:
            entries = await manager.get_by_tag(tag)
            print(f"  标签 '{tag}': {len(entries)} 条")
            for e in entries:
                print(f"    - {e.key}")

        # 搜索
        print("\n搜索 '内容':")
        results = await manager.search("内容")
        for r in results:
            print(f"  - {r.key}: {r.value[:20]}...")

    finally:
        await manager.shutdown()


async def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print("分布式记忆管理演示")
    print("短期记忆 + 长期记忆 + 分布式同步")
    print("=" * 70 + "\n")

    await demo_short_term_memory()
    await demo_long_term_memory()
    await demo_memory_priority()
    await demo_distributed_sync()
    await demo_memory_expiry()
    await demo_memory_tags()

    print("\n" + "=" * 70)
    print("演示完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
