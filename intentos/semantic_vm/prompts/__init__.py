"""
IntentOS 提示词生成器模块

基于 Claude Code 提示词设计改进，适用于 IntentOS 语义 VM。

架构:
- 静态部分（可缓存）：身份、系统指令、工具使用、风格约束
- 动态边界标记：分隔静态/动态内容
- 动态部分（每回合可变）：环境信息、语言、配置

使用示例:
    from intentos.semantic_vm.prompts import build_system_prompt, PromptConfig
    
    config = PromptConfig(language="zh-CN", output_style="concise")
    prompt_sections = build_system_prompt(config)
    system_prompt = "\n\n".join(prompt_sections)
"""

from .builder import (
    PromptConfig,
    build_system_prompt,
    compute_prompt_cache_key,
    join_prompt_sections,
    extract_static_sections,
    extract_dynamic_sections,
    SYSTEM_PROMPT_BOUNDARY,
)
from .sections import (
    get_intro_section,
    get_system_section,
    get_tools_section,
    get_code_style_section,
    get_tone_section,
    get_efficiency_section,
    get_actions_section,
    get_language_section,
    get_env_section,
    get_dynamic_boundary,
)

__all__ = [
    # 主构建器
    "build_system_prompt",
    "PromptConfig",
    "compute_prompt_cache_key",
    "join_prompt_sections",
    "extract_static_sections",
    "extract_dynamic_sections",
    "SYSTEM_PROMPT_BOUNDARY",
    # 静态部分
    "get_intro_section",
    "get_system_section",
    "get_tools_section",
    "get_code_style_section",
    "get_tone_section",
    "get_efficiency_section",
    "get_actions_section",
    # 动态部分
    "get_language_section",
    "get_env_section",
    "get_dynamic_boundary",
]
