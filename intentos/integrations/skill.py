"""
Skill 规范支持

基于 Claude Skills 规范:
https://github.com/anthropics/awesome-claude-skills

一个 Skill 由以下文件组成:
- SKILL.md - Skill 元数据和规范
- scripts/ - 可执行代码
- references/ - 文档材料
- assets/ - 输出文件
"""

from __future__ import annotations

import os
import yaml
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path


@dataclass
class SkillSpec:
    """Skill 规范 (SKILL.md)

    基于 Claude Skills 规范:
    https://github.com/anthropics/awesome-claude-skills

    结构:
    skill-name/
    ├── SKILL.md (required)
    │   ├── YAML frontmatter metadata (required)
    │   │   ├── name: (required)
    │   │   └── description: (required)
    │   └── Markdown instructions (required)
    └── Bundled Resources (optional)
        ├── scripts/          - Executable code
        ├── references/       - Documentation
        └── assets/           - Output files
    """
    name: str
    description: str
    license: str = ""

    # 资源目录
    scripts_dir: str = "scripts"
    references_dir: str = "references"
    assets_dir: str = "assets"

    # 完整内容
    content: str = ""
    path: str = ""

    @classmethod
    def from_markdown(cls, content: str, path: str = "") -> "SkillSpec":
        """从 Markdown 内容解析"""
        # 提取 YAML front matter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                data = yaml.safe_load(yaml_content)

                # 提取必需字段
                name = data.get("name", "")
                description = data.get("description", "")

                if not name or not description:
                    raise ValueError("SKILL.md must have 'name' and 'description' in frontmatter")

                return cls(
                    name=name,
                    description=description,
                    license=data.get("license", ""),
                    content=content,
                    path=path,
                )

        raise ValueError("Invalid SKILL.md format - missing YAML frontmatter")

    @classmethod
    def from_file(cls, path: str) -> "SkillSpec":
        """从文件加载"""
        with open(path) as f:
            content = f.read()
        return cls.from_markdown(content, path)


@dataclass
class ToolSpec:
    """工具规范"""
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)


class SkillLoader:
    """
    Skill 加载器

    基于 Claude Skills 规范加载 Skill
    https://github.com/anthropics/awesome-claude-skills
    """

    def __init__(self, skills_dir: str = None):
        self.skills_dir = skills_dir or os.path.expanduser("~/.claude/skills")
        os.makedirs(self.skills_dir, exist_ok=True)

    def discover_skills(self) -> list[str]:
        """发现已安装的 Skills"""
        skill_ids = []

        # 扫描技能目录
        if os.path.exists(self.skills_dir):
            for item in os.listdir(self.skills_dir):
                skill_path = os.path.join(self.skills_dir, item)
                skill_md = os.path.join(skill_path, "SKILL.md")

                # 检查 SKILL.md 是否存在
                if os.path.exists(skill_md):
                    skill_ids.append(item)

        return skill_ids

    def load_skill(self, skill_id: str) -> Optional[dict]:
        """加载 Skill 规范"""
        skill_path = os.path.join(self.skills_dir, skill_id)
        skill_md = os.path.join(skill_path, "SKILL.md")

        if not os.path.exists(skill_md):
            return None

        try:
            # 加载 SKILL.md
            spec = SkillSpec.from_file(skill_md)

            # 获取资源路径
            resources = {
                "scripts": os.path.join(skill_path, spec.scripts_dir) if os.path.exists(os.path.join(skill_path, spec.scripts_dir)) else None,
                "references": os.path.join(skill_path, spec.references_dir) if os.path.exists(os.path.join(skill_path, spec.references_dir)) else None,
                "assets": os.path.join(skill_path, spec.assets_dir) if os.path.exists(os.path.join(skill_path, spec.assets_dir)) else None,
            }

            return {
                "spec": spec,
                "path": skill_path,
                "resources": resources,
            }
        except Exception as e:
            print(f"加载 Skill 失败：{skill_id}, 错误：{e}")
            return None


# ========== 单例 ==========

_skill_loader: Optional[SkillLoader] = None


def get_skill_loader() -> SkillLoader:
    """获取 Skill 加载器"""
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader()
    return _skill_loader
