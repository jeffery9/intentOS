#!/usr/bin/env python3
"""
Skill 初始化工具

基于 Claude Skills 规范创建新的 Skill
https://github.com/anthropics/awesome-claude-skills

用法:
    python -m intentos.integrations.init_skill <skill-name> --path <output-directory>
"""

import argparse
import os
import sys
from pathlib import Path


SKILL_TEMPLATE = """---
name: {skill_name}
description: {skill_description}
license: MIT
---

# {skill_title}

This skill provides {{specialized functionality}}.

## About This Skill

{{Describe what this skill does and why it's useful.}}

## When to Use This Skill

Use this skill when:
- {{Trigger condition 1}}
- {{Trigger condition 2}}
- {{Trigger condition 3}}

## How to Use This Skill

{{Describe how Claude should use this skill in practice.}}

### Examples

```
User: {{Example user query}}
Assistant: {{How the skill should respond}}
```

## Resources

This skill includes the following resources:

### Scripts

{{List and describe scripts in scripts/ directory}}

### References

{{List and describe reference materials in references/ directory}}

### Assets

{{List and describe assets in assets/ directory}}

## Configuration

{{Describe any configuration needed to use this skill.}}

## Notes

{{Additional notes, limitations, or important information.}}
"""


def create_skill(skill_name: str, output_path: str) -> None:
    """创建新的 Skill"""
    
    # 生成技能标题
    skill_title = skill_name.replace('-', ' ').title()
    
    # 生成描述
    skill_description = f"This skill should be used when users want to {{describe use case}}. It extends Claude's capabilities with specialized knowledge and workflows for {skill_title}."
    
    # 创建目录结构
    skill_dir = Path(output_path) / skill_name
    scripts_dir = skill_dir / "scripts"
    references_dir = skill_dir / "references"
    assets_dir = skill_dir / "assets"
    
    print(f"Creating skill: {skill_name}")
    print(f"Output directory: {skill_dir}\n")
    
    # 创建目录
    skill_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(exist_ok=True)
    references_dir.mkdir(exist_ok=True)
    assets_dir.mkdir(exist_ok=True)
    
    # 创建 SKILL.md
    skill_md_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_description=skill_description,
        skill_title=skill_title,
    )
    
    skill_md_path = skill_dir / "SKILL.md"
    with open(skill_md_path, 'w') as f:
        f.write(skill_md_content)
    print(f"✓ Created: {skill_md_path}")
    
    # 创建示例脚本
    example_script = scripts_dir / "example.py"
    with open(example_script, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""
Example script for """ + skill_title + """

This script demonstrates how to include executable code in your skill.
"""

def main():
    """Main function."""
    print("Hello from skill script!")

if __name__ == "__main__":
    main()
''')
    print(f"✓ Created: {example_script}")
    
    # 创建示例参考文档
    example_reference = references_dir / "example.md"
    with open(example_reference, 'w') as f:
        f.write(f"""# {skill_title} Reference

This reference document provides detailed information about {skill_title}.

## Overview

{{Detailed information about the domain.}}

## Key Concepts

### Concept 1

{{Description}}

### Concept 2

{{Description}}

## Examples

{{Examples and use cases}}

## Related Resources

- {{Link to relevant documentation}}
""")
    print(f"✓ Created: {example_reference}")
    
    # 创建 README
    readme_path = skill_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(f"""# {skill_title}

A Claude Skill for {skill_title}.

## Installation

Copy this skill directory to `~/.claude/skills/`:

```bash
cp -r {skill_name} ~/.claude/skills/
```

## Usage

Once installed, Claude will automatically use this skill when appropriate.

## Structure

```
{skill_name}/
├── SKILL.md          # Skill definition and instructions
├── scripts/          # Executable code
├── references/       # Documentation
└── assets/           # Output files
```

## License

MIT
""")
    print(f"✓ Created: {readme_path}")
    
    print(f"\n✅ Skill '{skill_name}' created successfully!")
    print(f"\nNext steps:")
    print(f"1. Edit {skill_md_path} to define your skill")
    print(f"2. Add scripts to {scripts_dir}")
    print(f"3. Add references to {references_dir}")
    print(f"4. Add assets to {assets_dir}")
    print(f"5. Copy to ~/.claude/skills/ to install")


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Claude Skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s weather-skill --path ./skills
  %(prog)s pdf-editor -o ~/.claude/skills
        """
    )
    
    parser.add_argument(
        "skill_name",
        help="Name of the skill (e.g., weather-skill, pdf-editor)"
    )
    
    parser.add_argument(
        "--path", "-p",
        default=".",
        help="Output directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # 验证技能名称
    if not args.skill_name.replace('-', '').isalnum():
        print("Error: Skill name must contain only letters, numbers, and hyphens")
        sys.exit(1)
    
    # 创建技能
    try:
        create_skill(args.skill_name, args.path)
    except Exception as e:
        print(f"Error creating skill: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
