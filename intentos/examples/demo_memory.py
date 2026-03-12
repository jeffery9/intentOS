"""
内存管理和 Map/Reduce 演示
"""

import asyncio
import time
from intentos import (
    create_memory_manager,
    create_map_reduce_task,
    create_map_reduce_executor,
    MemoryManager,
    MemoryLevel,
    MapReduceTask,
)


async def demo_memory_manager():
    """演示内存管理器"""
    print("=" * 60)
    print("演示 1: 内存管理器 (Memory Manager)")
    print("=" * 60)
    
    # 创建内存管理器（限制 100MB）
    mm = create_memory_manager(max_memory_mb=100)
    
    # 注册内存变化回调
    def on_change(level: MemoryLevel, stats):
        print(f"  [内存告警] 级别：{level.value}, 使用：{stats.usage_percent:.1f}%")
    
    mm.on_memory_change(on_change)
    
    # 模拟内存分配
    print("\n模拟内存分配:")
    data = []
    for i in range(10):
        chunk = [0] * (1024 * 1024)  # 1MB
        mm.allocate(chunk, f"chunk_{i}")
        data.append(chunk)
        
        stats = mm.get_stats()
        print(f"  分配后：{stats.used_bytes / 1024 / 1024:.1f}MB ({stats.usage_percent:.1f}%)")
    
    # 强制 GC
    print("\n强制垃圾回收...")
    collected = await mm.force_gc()
    print(f"  回收对象数：{collected}")
    
    # 释放内存
    print("\n释放内存:")
    for i in range(5):
        mm.deallocate(f"chunk_{i}")
        data[i] = None
    
    stats = mm.get_stats()
    print(f"  释放后：{stats.used_bytes / 1024 / 1024:.1f}MB ({stats.usage_percent:.1f}%)")
    
    print(f"\n最终统计:")
    print(f"  峰值内存：{mm.get_stats().peak_bytes / 1024 / 1024:.1f}MB")
    print(f"  GC 次数：{mm.get_stats().gc_collections}")


async def demo_word_count():
    """演示经典 Word Count Map/Reduce"""
    print("\n" + "=" * 60)
    print("演示 2: Word Count Map/Reduce")
    print("=" * 60)
    
    # 输入数据
    documents = [
        "hello world hello",
        "world peace world",
        "hello python world",
        "python is great python",
        "great world great",
    ] * 100  # 放大数据
    
    # Map 函数：将文本拆分为 (word, 1)
    def map_func(doc):
        words = doc.split()
        for word in words:
            yield (word.lower(), 1)
    
    # Reduce 函数：累加计数
    def reduce_func(key, values):
        return sum(values)
    
    # 创建任务
    task = create_map_reduce_task(
        name="word_count",
        map_func=map_func,
        reduce_func=reduce_func,
        input_data=documents,
        num_mappers=4,
        num_reducers=4,
        chunk_size=10,
    )
    
    # 执行
    executor = create_map_reduce_executor(max_memory_mb=50)
    results = await executor.execute(task)
    
    print(f"\n词频统计结果 (Top 10):")
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)[:10]
    for word, count in sorted_results:
        print(f"  {word}: {count}")


async def demo_log_analysis():
    """演示日志分析 Map/Reduce"""
    print("\n" + "=" * 60)
    print("演示 3: 日志分析 Map/Reduce")
    print("=" * 60)
    
    # 模拟日志数据
    import random
    log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    services = ["api", "web", "db", "cache"]
    
    logs = []
    for i in range(1000):
        level = random.choice(log_levels)
        service = random.choice(services)
        logs.append(f"{level} [{service}] Message {i}")
    
    # Map: 按服务 + 级别分组
    def map_func(log):
        parts = log.split()
        level = parts[0]
        service = parts[1].strip("[]")
        key = f"{service}_{level}"
        yield (key, 1)
    
    # Reduce: 计数
    def reduce_func(key, values):
        return {"count": sum(values), "level": key.split("_")[1], "service": key.split("_")[0]}
    
    task = create_map_reduce_task(
        name="log_analysis",
        map_func=map_func,
        reduce_func=reduce_func,
        input_data=logs,
        num_reducers=8,
    )
    
    executor = create_map_reduce_executor(max_memory_mb=30)
    results = await executor.execute(task)
    
    print(f"\n日志分析结果:")
    for key, value in sorted(results.items()):
        print(f"  {key}: {value['count']} 条")


async def demo_data_aggregation():
    """演示数据聚合 Map/Reduce"""
    print("\n" + "=" * 60)
    print("演示 4: 销售数据聚合 Map/Reduce")
    print("=" * 60)
    
    # 模拟销售数据
    import random
    regions = ["华东", "华南", "华北", "西部"]
    products = ["产品 A", "产品 B", "产品 C"]
    
    sales_records = []
    for i in range(500):
        record = {
            "region": random.choice(regions),
            "product": random.choice(products),
            "amount": random.randint(100, 10000),
            "quantity": random.randint(1, 100),
        }
        sales_records.append(record)
    
    # Map: 按区域 + 产品分组
    def map_func(record):
        key = f"{record['region']}_{record['product']}"
        yield (key, {"amount": record["amount"], "quantity": record["quantity"]})
    
    # Reduce: 聚合
    def reduce_func(key, values):
        total_amount = sum(v["amount"] for v in values)
        total_quantity = sum(v["quantity"] for v in values)
        return {
            "region": key.split("_")[0],
            "product": key.split("_")[1],
            "total_amount": total_amount,
            "total_quantity": total_quantity,
            "avg_price": total_amount / total_quantity if total_quantity > 0 else 0,
        }
    
    task = create_map_reduce_task(
        name="sales_aggregation",
        map_func=map_func,
        reduce_func=reduce_func,
        input_data=sales_records,
        num_reducers=4,
    )
    
    executor = create_map_reduce_executor(max_memory_mb=30)
    results = await executor.execute(task)
    
    print(f"\n销售数据聚合结果:")
    for key, value in sorted(results.items()):
        print(f"  {value['region']} - {value['product']}: "
              f"金额={value['total_amount']:,}, 数量={value['total_quantity']}, "
              f"均价={value['avg_price']:.2f}")


async def demo_streaming_processing():
    """演示流式处理（内存优化）"""
    print("\n" + "=" * 60)
    print("演示 5: 流式处理 (Streaming Processing)")
    print("=" * 60)
    
    from intentos import MemoryAwareExecutor, create_memory_manager
    
    mm = create_memory_manager(max_memory_mb=20)
    executor = MemoryAwareExecutor(mm)
    
    # 模拟大量数据
    large_dataset = list(range(10000))
    
    # Map 函数：计算平方
    def map_func(x):
        yield ("squared", x * x)
    
    print(f"处理 {len(large_dataset)} 条数据...")
    
    # 流式处理
    count = 0
    total = 0
    
    async for key, value in executor.execute_map(map_func, large_dataset, chunk_size=100):
        count += 1
        total += value
        
        # 定期报告进度
        if count % 1000 == 0:
            stats = mm.get_stats()
            print(f"  进度：{count}/{len(large_dataset)}, 内存：{stats.usage_percent:.1f}%")
    
    print(f"\n结果：总数={count}, 总和={total:,}")
    print(f"最终内存使用：{mm.get_stats().usage_percent:.1f}%")


async def demo_distributed_shuffle():
    """演示分布式 Shuffle"""
    print("\n" + "=" * 60)
    print("演示 6: 分布式 Shuffle")
    print("=" * 60)
    
    from intentos import DistributedShuffle
    
    shuffle = DistributedShuffle(num_partitions=4, spill_threshold_bytes=1024)  # 小阈值触发溢出
    
    # 添加数据
    print("添加数据到 Shuffle...")
    for i in range(100):
        key = f"key_{i % 10}"
        value = {"id": i, "data": "x" * 100}
        await shuffle.add(key, value)
    
    print(f"  已添加 100 条记录")
    print(f"  溢出文件数：{len(shuffle._spill_files)}")
    
    # 获取分组数据
    print("\n获取分组数据:")
    group_counts = {}
    async for key, values in shuffle.get_all():
        group_counts[key] = len(values)
    
    print(f"  分组数：{len(group_counts)}")
    print(f"  各组大小：{group_counts}")
    
    # 清理
    await shuffle.cleanup()
    print(f"\n已清理临时文件")


async def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print("内存管理和 Map/Reduce 演示")
    print("=" * 70 + "\n")
    
    await demo_memory_manager()
    await demo_word_count()
    await demo_log_analysis()
    await demo_data_aggregation()
    await demo_streaming_processing()
    await demo_distributed_shuffle()
    
    print("\n" + "=" * 70)
    print("演示完成")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
