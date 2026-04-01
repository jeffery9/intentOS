#!/usr/bin/env python3
"""
IntentOS 改进的提示词系统演示

展示基于 Claude Code 提示词设计改进的系统：
- 静态/动态部分分离（缓存优化）
- 数值化输出约束
- 代码风格原则
- 风险控制机制
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from intentos.compiler import IntentCompiler
from intentos.core.models import Intent, IntentType, Context
from intentos.semantic_vm.prompts import (
    PromptConfig,
    build_system_prompt,
    compute_prompt_cache_key,
    join_prompt_sections,
    SYSTEM_PROMPT_BOUNDARY,
)


def demo_basic_usage():
    """基础使用演示"""
    print("=" * 70)
    print("1. 基础使用：构建系统提示词")
    print("=" * 70)
    
    # 使用默认配置构建提示词
    config = PromptConfig()
    sections = build_system_prompt(config)
    full_prompt = join_prompt_sections(sections)
    
    print(f"\n完整提示词：{len(full_prompt):,} 字符 (~{len(full_prompt)//4} tokens)")
    print(f"分段数量：{len(sections)}")
    
    # 显示边界标记
    for i, section in enumerate(sections):
        if SYSTEM_PROMPT_BOUNDARY in section:
            print(f"\n边界标记位置：第 {i} 段")
            print(f"静态部分：{i} 段 | 动态部分：{len(sections)-i-1} 段")
            break
    
    # 显示前 500 字符
    print(f"\n提示词预览 (前 500 字符):")
    print("-" * 70)
    print(full_prompt[:500] + "...")
    print("-" * 70)


def demo_cache_optimization():
    """缓存优化演示"""
    print("\n" + "=" * 70)
    print("2. 缓存优化：Blake2b 哈希键")
    print("=" * 70)
    
    # 相同配置应生成相同缓存键
    sections1 = build_system_prompt(PromptConfig(language="zh-CN"))
    sections2 = build_system_prompt(PromptConfig(language="zh-CN"))
    
    key1 = compute_prompt_cache_key(sections1)
    key2 = compute_prompt_cache_key(sections2)
    
    print(f"\n配置 1 缓存键：{key1}")
    print(f"配置 2 缓存键：{key2}")
    print(f"缓存键匹配：{key1 == key2} ✓" if key1 == key2 else f"缓存键不匹配 ✗")
    
    # 缓存键用于 LLM API 缓存，减少重复计算
    print(f"\n缓存键用途:")
    print(f"  - LLM API 请求缓存（相同提示词复用响应）")
    print(f"  - 减少 Token 消耗")
    print(f"  - 提升响应速度")


def demo_custom_config():
    """自定义配置演示"""
    print("\n" + "=" * 70)
    print("3. 自定义配置：语言、风格、Token 预算")
    print("=" * 70)
    
    config = PromptConfig(
        language="en-US",
        output_style="detailed",
        token_budget=50000,
        additional_dirs=["/data", "/models"],
        keep_coding_instructions=True,
    )
    
    sections = build_system_prompt(config)
    full_prompt = join_prompt_sections(sections)
    
    print(f"\n自定义配置提示词：{len(full_prompt):,} 字符")
    
    # 检查关键部分
    checks = [
        ("Language (English)", "Always respond in en-US" in full_prompt),
        ("Token Budget", "Token Budget" in full_prompt and "50,000" in full_prompt),
        ("Output Style (detailed)", "Output Style: Detailed" in full_prompt),
        ("Additional Directories", "/data" in full_prompt and "/models" in full_prompt),
        ("Code Style", "Code style" in full_prompt),
    ]
    
    print(f"\n配置检查:")
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")


def demo_compiler_integration():
    """编译器集成演示"""
    print("\n" + "=" * 70)
    print("4. 编译器集成：意图编译 + 缓存统计")
    print("=" * 70)
    
    # 创建编译器（启用缓存）
    compiler = IntentCompiler(
        prompt_config=PromptConfig(language="zh-CN"),
        enable_cache=True,
    )
    
    # 创建意图
    intents = [
        Intent(
            name="analyze_sales",
            intent_type=IntentType.ATOMIC,
            goal="分析华东区 Q3 销售数据",
            description="查询并分析销售趋势",
            context=Context(user_id="user_001"),
        ),
        Intent(
            name="generate_report",
            intent_type=IntentType.COMPOSITE,
            goal="生成月度报告",
            description="整合数据生成 PDF 报告",
            context=Context(user_id="user_001"),
        ),
    ]
    
    print(f"\n编译 {len(intents)} 个意图:")
    
    for intent in intents:
        compiled = compiler.compile(intent)
        print(f"\n  意图：{intent.name}")
        print(f"  System Prompt: {len(compiled.system_prompt):,} 字符")
        print(f"  User Prompt: {len(compiled.user_prompt):,} 字符")
        print(f"  缓存键：{compiled.metadata.get('cache_key', 'N/A')[:16]}...")
    
    # 再次编译相同意图（应命中缓存）
    print(f"\n再次编译相同意图（缓存测试）:")
    compiler.compile(intents[0])
    compiler.compile(intents[0])
    
    # 显示统计
    stats = compiler.get_stats()
    print(f"\n编译器统计:")
    print(f"  总编译次数：{stats['compilations']}")
    print(f"  缓存命中：{stats['cache_hits']} ✓")
    print(f"  缓存未命中：{stats['cache_misses']}")
    print(f"  缓存大小：{stats['cache_size']} 条目")
    print(f"  缓存命中率：{stats['cache_hits']/stats['compilations']*100:.1f}%")


def demo_prompt_sections():
    """提示词章节展示"""
    print("\n" + "=" * 70)
    print("5. 提示词章节详情")
    print("=" * 70)
    
    from intentos.semantic_vm.prompts import (
        get_intro_section,
        get_code_style_section,
        get_efficiency_section,
        get_actions_section,
    )
    
    # 代码风格原则
    print("\n[代码风格原则]")
    code_style = get_code_style_section()
    lines = code_style.split("\n")[2:8]  # 显示部分
    for line in lines:
        print(f"  {line}")
    
    # 输出效率约束
    print("\n[输出效率约束]")
    efficiency = get_efficiency_section()
    lines = efficiency.split("\n")[2:6]
    for line in lines:
        print(f"  {line}")
    
    # 风险控制
    print("\n[风险控制（摘要）]")
    actions = get_actions_section()
    lines = actions.split("\n")[4:10]
    for line in lines:
        print(f"  {line}")


def demo_comparison():
    """新旧对比"""
    print("\n" + "=" * 70)
    print("6. 改进对比：Claude Code 启发 vs 原始设计")
    print("=" * 70)
    
    improvements = [
        ("静态/动态分离", "✓ 支持边界标记", "✗ 无分离"),
        ("缓存优化", "✓ Blake2b 哈希键", "✗ 无缓存"),
        ("数值化约束", "✓ 50 字/200 字限制", "✗ 定性描述"),
        ("代码风格", "✓ 9 条详细原则", "✗ 简单说明"),
        ("风险控制", "✓ 分类详细列表", "✗ 基础警告"),
        ("输出风格", "✓ 3 种模式可选", "✗ 单一模式"),
        ("Token 预算", "✓ 可配置目标", "✗ 无支持"),
    ]
    
    print(f"\n{'特性':<15} | {'改进后':<25} | {'原始':<15}")
    print("-" * 60)
    for feature, improved, original in improvements:
        print(f"{feature:<15} | {improved:<25} | {original:<15}")


def main():
    """运行所有演示"""
    print("\n" + "=" * 70)
    print(" IntentOS 改进的提示词系统演示")
    print(" 基于 Claude Code 提示词设计优化")
    print("=" * 70)
    
    demo_basic_usage()
    demo_cache_optimization()
    demo_custom_config()
    demo_compiler_integration()
    demo_prompt_sections()
    demo_comparison()
    
    print("\n" + "=" * 70)
    print(" 演示完成!")
    print("=" * 70)
    print("\n关键收获:")
    print("  1. 静态/动态分离 → LLM API 缓存优化")
    print("  2. 数值化约束 → 更一致的输出质量")
    print("  3. 代码风格原则 → 减少过度工程")
    print("  4. 风险控制 → 更安全的生产操作")
    print("  5. 可配置输出风格 → 适应不同场景")
    print()


if __name__ == "__main__":
    main()
