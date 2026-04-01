"""
提示词构建器

将静态和动态部分组合成完整的系统提示词。
支持缓存优化：静态部分可缓存，动态部分每回合更新。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional

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
    SYSTEM_PROMPT_BOUNDARY,
)


@dataclass
class PromptConfig:
    """
    提示词配置
    
    用于动态生成提示词的配置项。
    """
    # 语言设置
    language: str = "zh-CN"
    
    # 输出风格：concise, detailed, verbose
    output_style: str = "concise"
    
    # Token 预算（可选）
    token_budget: Optional[int] = None
    
    # 额外工作目录
    additional_dirs: list[str] = field(default_factory=list)
    
    # 是否启用代码风格指导
    keep_coding_instructions: bool = True
    
    # 工作目录（默认当前目录）
    cwd: Optional[str] = None
    
    # Git 仓库检测
    is_git: Optional[bool] = None


def build_system_prompt(config: Optional[PromptConfig] = None) -> list[str]:
    """
    构建系统提示词
    
    返回分段的提示词列表，静态部分在前，动态边界标记，然后是动态部分。
    这种结构支持缓存优化：静态部分可复用，动态部分每回合更新。
    
    Args:
        config: 提示词配置，None 则使用默认配置
        
    Returns:
        提示词分段列表
    """
    if config is None:
        config = PromptConfig()
    
    # --- 静态部分（可缓存）---
    static_sections = [
        get_intro_section(),
        get_system_section(),
        get_tools_section(),
    ]
    
    # 代码风格（可选）
    if config.keep_coding_instructions:
        static_sections.append(get_code_style_section())
    
    static_sections.extend([
        get_actions_section(),
        get_tone_section(),
        get_efficiency_section(),
    ])
    
    # --- 动态边界标记 ---
    boundary = [get_dynamic_boundary()]
    
    # --- 动态部分（每回合可变）---
    dynamic_sections = [
        get_language_section(config.language),
        get_env_section(
            cwd=config.cwd,
            is_git=config.is_git,
            additional_dirs=config.additional_dirs,
        ),
    ]
    
    # Token 预算（可选）
    if config.token_budget:
        dynamic_sections.append(get_token_budget_section(config.token_budget))
    
    # 输出风格调整
    dynamic_sections.append(get_output_style_section(config.output_style))
    
    return [*static_sections, *boundary, *dynamic_sections]


def get_token_budget_section(budget: int) -> str:
    """
    Token 预算配置
    
    当用户指定 Token 目标时，指导模型 productive 地使用预算。
    """
    return f"""# Token Budget

用户指定的 Token 目标：{budget:,} tokens

- 规划你的工作以 productive 地填 full 预算
- 目标是 hard minimum，不是建议
- 如果提前停止，系统会自动继续
- 每回合会显示已用 Token 数"""


def get_output_style_section(style: str) -> str:
    """
    输出风格配置
    """
    styles = {
        "concise": """# Output Style: Concise

- 直接给出答案，最小化解释
- 优先使用单句回复
- 避免不必要的格式化和结构""",
        
        "detailed": """# Output Style: Detailed

- 提供完整的解释和推理
- 包含相关背景和上下文
- 使用结构化格式（标题、列表）""",
        
        "verbose": """# Output Style: Verbose

- 详尽的解释和分析
- 包含所有相关细节
- 提供多种角度和替代方案""",
    }
    
    return styles.get(style, styles["concise"])


def compute_prompt_cache_key(prompt_sections: list[str]) -> str:
    """
    计算提示词缓存键
    
    使用 Blake2b 哈希算法生成缓存键，用于 LLM API 缓存。
    只哈希静态部分，动态部分每回合变化。
    
    Args:
        prompt_sections: 提示词分段列表
        
    Returns:
        32 字符十六进制缓存键
    """
    # 找到边界标记，只哈希静态部分
    try:
        boundary_index = next(
            i for i, section in enumerate(prompt_sections)
            if SYSTEM_PROMPT_BOUNDARY in section
        )
        static_content = "".join(prompt_sections[:boundary_index])
    except StopIteration:
        # 没有边界标记，哈希全部内容
        static_content = "".join(prompt_sections)
    
    # Blake2b 哈希，16 字节摘要 = 32 字符十六进制
    return hashlib.blake2b(
        static_content.encode("utf-8"),
        digest_size=16,
    ).hexdigest()


def join_prompt_sections(sections: list[str], separator: str = "\n\n") -> str:
    """
    将提示词分段连接为完整字符串
    
    Args:
        sections: 提示词分段列表
        separator: 分段分隔符，默认双换行
        
    Returns:
        完整的提示词字符串
    """
    return separator.join(sections)


def extract_static_sections(sections: list[str]) -> list[str]:
    """
    提取静态部分（用于缓存）
    
    Args:
        sections: 完整提示词分段列表
        
    Returns:
        静态部分列表
    """
    try:
        boundary_index = next(
            i for i, section in enumerate(sections)
            if SYSTEM_PROMPT_BOUNDARY in section
        )
        return sections[:boundary_index]
    except StopIteration:
        return sections


def extract_dynamic_sections(sections: list[str]) -> list[str]:
    """
    提取动态部分（每回合更新）
    
    Args:
        sections: 完整提示词分段列表
        
    Returns:
        动态部分列表
    """
    try:
        boundary_index = next(
            i for i, section in enumerate(sections)
            if SYSTEM_PROMPT_BOUNDARY in section
        )
        return sections[boundary_index + 1:]
    except StopIteration:
        return []
