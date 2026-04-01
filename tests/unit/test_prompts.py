#!/usr/bin/env python3
"""
测试改进的提示词生成器

验证：
1. 提示词分段生成
2. 静态/动态部分分离
3. 缓存键计算
4. 完整的系统提示词构建
"""

from intentos.semantic_vm.prompts import (
    PromptConfig,
    build_system_prompt,
    compute_prompt_cache_key,
    join_prompt_sections,
    SYSTEM_PROMPT_BOUNDARY,
    get_intro_section,
    get_system_section,
    get_tools_section,
    get_code_style_section,
    get_tone_section,
    get_efficiency_section,
    get_actions_section,
    get_language_section,
    get_env_section,
)


def test_static_sections():
    """测试静态部分生成"""
    print("=" * 60)
    print("测试静态部分")
    print("=" * 60)
    
    sections = [
        ("Intro", get_intro_section()),
        ("System", get_system_section()),
        ("Tools", get_tools_section()),
        ("Code Style", get_code_style_section()),
        ("Actions", get_actions_section()),
        ("Tone", get_tone_section()),
        ("Efficiency", get_efficiency_section()),
    ]
    
    for name, content in sections:
        lines = content.split("\n")
        print(f"\n{name}: {len(lines)} 行")
        print(f"  前 100 字符：{content[:100]}...")
    
    return [content for _, content in sections]


def test_dynamic_sections():
    """测试动态部分生成"""
    print("\n" + "=" * 60)
    print("测试动态部分")
    print("=" * 60)
    
    # 语言部分
    lang_zh = get_language_section("zh-CN")
    print(f"\nLanguage (zh-CN): {len(lang_zh.split(chr(10)))} 行")
    
    lang_en = get_language_section("en-US")
    print(f"Language (en-US): {len(lang_en.split(chr(10)))} 行")
    
    # 环境部分
    env = get_env_section()
    env_lines = env.split("\n")
    print(f"\nEnvironment: {len(env_lines)} 行")
    for line in env_lines[:10]:
        print(f"  {line}")
    
    return [lang_zh, env]


def test_full_prompt():
    """测试完整提示词构建"""
    print("\n" + "=" * 60)
    print("测试完整提示词构建")
    print("=" * 60)
    
    # 默认配置
    config = PromptConfig()
    sections = build_system_prompt(config)
    
    print(f"\n总段数：{len(sections)}")
    
    # 查找边界标记
    boundary_index = -1
    for i, section in enumerate(sections):
        if SYSTEM_PROMPT_BOUNDARY in section:
            boundary_index = i
            print(f"边界标记位置：{i}")
            break
    
    if boundary_index >= 0:
        static_count = boundary_index
        dynamic_count = len(sections) - boundary_index - 1
        print(f"静态部分：{static_count} 段")
        print(f"动态部分：{dynamic_count} 段")
    
    # 计算总字符数
    full_prompt = join_prompt_sections(sections)
    print(f"\n完整提示词：{len(full_prompt):,} 字符")
    print(f"约 {len(full_prompt) // 4:,} tokens")
    
    return sections, full_prompt


def test_cache_key():
    """测试缓存键计算"""
    print("\n" + "=" * 60)
    print("测试缓存键计算")
    print("=" * 60)
    
    config1 = PromptConfig(language="zh-CN")
    config2 = PromptConfig(language="zh-CN")
    config3 = PromptConfig(language="en-US")
    
    sections1 = build_system_prompt(config1)
    sections2 = build_system_prompt(config2)
    sections3 = build_system_prompt(config3)
    
    key1 = compute_prompt_cache_key(sections1)
    key2 = compute_prompt_cache_key(sections2)
    key3 = compute_prompt_cache_key(sections3)
    
    print(f"\n配置 1 (zh-CN): {key1}")
    print(f"配置 2 (zh-CN): {key2}")
    print(f"配置 3 (en-US): {key3}")
    
    print(f"\n配置 1 和 2 缓存键相同：{key1 == key2}")
    print(f"配置 1 和 3 缓存键相同：{key1 == key3}")
    
    # 验证缓存键稳定性
    key1_again = compute_prompt_cache_key(sections1)
    print(f"配置 1 再次计算：{key1_again}")
    print(f"缓存键稳定：{key1 == key1_again}")
    
    return key1, key2, key3


def test_custom_config():
    """测试自定义配置"""
    print("\n" + "=" * 60)
    print("测试自定义配置")
    print("=" * 60)
    
    config = PromptConfig(
        language="zh-CN",
        output_style="detailed",
        token_budget=100000,
        additional_dirs=["/tmp", "/var/log"],
        keep_coding_instructions=False,
    )
    
    sections = build_system_prompt(config)
    full_prompt = join_prompt_sections(sections)
    
    print(f"\n自定义配置提示词：{len(full_prompt):,} 字符")
    
    # 检查是否包含 token budget
    if "Token Budget" in full_prompt:
        print("✓ 包含 Token Budget 部分")
    else:
        print("✗ 未包含 Token Budget 部分")
    
    # 检查是否包含额外目录
    if "/tmp" in full_prompt:
        print("✓ 包含额外工作目录")
    else:
        print("✗ 未包含额外工作目录")
    
    # 检查代码风格（应禁用）
    if "Code style" not in full_prompt:
        print("✓ 代码风格部分已禁用")
    else:
        print("✗ 代码风格部分仍存在")
    
    return sections, full_prompt


def test_compiler_integration():
    """测试与编译器集成"""
    print("\n" + "=" * 60)
    print("测试编译器集成")
    print("=" * 60)
    
    from intentos.compiler import IntentCompiler
    from intentos.core.models import Intent, IntentType, Context
    
    # 创建编译器
    compiler = IntentCompiler(
        prompt_config=PromptConfig(language="zh-CN"),
        enable_cache=True,
    )
    
    # 创建简单意图
    intent = Intent(
        name="test_intent",
        intent_type=IntentType.ATOMIC,
        goal="测试提示词生成",
        description="验证改进的提示词系统",
        context=Context(user_id="test_user"),
    )
    
    # 编译
    compiled = compiler.compile(intent)
    
    print(f"\n编译成功：{compiled.metadata['template']}")
    print(f"System Prompt: {len(compiled.system_prompt):,} 字符")
    print(f"User Prompt: {len(compiled.user_prompt):,} 字符")
    print(f"缓存键：{compiled.metadata.get('cache_key', 'N/A')[:16]}...")
    
    # 再次编译（应命中缓存）
    compiled2 = compiler.compile(intent)
    
    # 获取统计
    stats = compiler.get_stats()
    print(f"\n编译器统计:")
    print(f"  编译次数：{stats['compilations']}")
    print(f"  缓存命中：{stats['cache_hits']}")
    print(f"  缓存未命中：{stats['cache_misses']}")
    print(f"  缓存大小：{stats['cache_size']}")
    
    return compiler, compiled


def main():
    """运行所有测试（pytest 模式）"""
    print("IntentOS 改进的提示词生成器测试")
    print("=" * 60)
    
    # 1. 静态部分
    test_static_sections()
    
    # 2. 动态部分
    test_dynamic_sections()
    
    # 3. 完整提示词
    test_full_prompt()
    
    # 4. 缓存键
    test_cache_key()
    
    # 5. 自定义配置
    test_custom_config()
    
    # 6. 编译器集成
    test_compiler_integration()
    
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    # 支持直接运行：python tests/unit/test_prompts.py
    main()
