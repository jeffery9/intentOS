"""
Skill 集成

支持 Claude Skills 规范 (SKILL.md)
"""

from __future__ import annotations

import os
from typing import Any, Optional
from .registry import CapabilityRegistry


class SkillIntegration:
    """
    Skill 集成
    
    加载和管理基于 SKILL.md 规范的 Skills
    """
    
    def __init__(self, registry: CapabilityRegistry, skills_dir: str = None):
        self.registry = registry
        self.skills_dir = skills_dir or os.path.expanduser("~/.claude/skills")
        self.loaded_skills: dict[str, dict] = {}
    
    def discover_skills(self) -> list[str]:
        """发现已安装的 Skills"""
        skill_ids = []
        
        if os.path.exists(self.skills_dir):
            for item in os.listdir(self.skills_dir):
                skill_path = os.path.join(self.skills_dir, item)
                skill_md = os.path.join(skill_path, "SKILL.md")
                
                if os.path.exists(skill_md):
                    skill_ids.append(item)
        
        return skill_ids
    
    async def load_skill(self, skill_id: str) -> bool:
        """加载 Skill"""
        skill_path = os.path.join(self.skills_dir, skill_id)
        skill_md = os.path.join(skill_path, "SKILL.md")
        
        if not os.path.exists(skill_md):
            return False
        
        try:
            # 解析 SKILL.md
            skill_data = self._parse_skill_md(skill_md)
            
            # 注册 Skill 定义的能力
            await self._register_skill_capabilities(skill_id, skill_data)
            
            self.loaded_skills[skill_id] = skill_data
            return True
        except Exception as e:
            print(f"加载 Skill 失败：{skill_id}, 错误：{e}")
            return False
    
    def _parse_skill_md(self, path: str) -> dict:
        """解析 SKILL.md 文件"""
        import yaml
        
        with open(path) as f:
            content = f.read()
        
        # 提取 YAML front matter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content = parts[1].strip()
                data = yaml.safe_load(yaml_content)
                
                return {
                    "spec": {
                        "id": data.get("name", ""),
                        "name": data.get("name", ""),
                        "description": data.get("description", ""),
                        "license": data.get("license", ""),
                    },
                    "content": content,
                    "path": path,
                    "resources": self._scan_resources(os.path.dirname(path)),
                }
        
        return {}
    
    def _scan_resources(self, skill_path: str) -> dict:
        """扫描 Skill 资源"""
        return {
            "scripts": os.path.join(skill_path, "scripts") if os.path.exists(os.path.join(skill_path, "scripts")) else None,
            "references": os.path.join(skill_path, "references") if os.path.exists(os.path.join(skill_path, "references")) else None,
            "assets": os.path.join(skill_path, "assets") if os.path.exists(os.path.join(skill_path, "assets")) else None,
        }
    
    async def _register_skill_capabilities(self, skill_id: str, skill_data: dict) -> None:
        """注册 Skill 定义的能力"""
        # 简单实现：根据 Skill 内容动态生成能力
        # 实际应该解析 SKILL.md 中定义的具体能力
        
        spec = skill_data.get("spec", {})
        
        # 注册一个通用的 Skill 执行能力
        async def skill_handler(**kwargs):
            return {
                "skill_id": skill_id,
                "spec": spec,
                "kwargs": kwargs,
            }
        
        self.registry.register(
            id=f"skill_{skill_id}",
            name=spec.get("name", skill_id),
            description=spec.get("description", f"Skill: {skill_id}"),
            handler=skill_handler,
            tags=["skill", skill_id],
            metadata=skill_data,
            source="skill",
        )
    
    def get_loaded_skills(self) -> list[str]:
        """获取已加载的 Skills"""
        return list(self.loaded_skills.keys())
