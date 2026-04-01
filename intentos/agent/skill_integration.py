"""
Skill 集成

支持 Claude Skills 规范 (SKILL.md) 和 IntentOS 自动提炼技能
"""

from __future__ import annotations

import os
from typing import Any, Optional


class SkillIntegration:
    """
    Skill 集成

    加载和管理基于 SKILL.md 规范的 Skills
    整合 intentos/skill/自动提炼的技能系统
    """

    def __init__(
        self,
        registry: Any,
        skills_dir: Optional[str] = None,
        skill_store: Optional[Any] = None,  # intentos.skill.store.SkillStore
    ):
        self.registry = registry
        self.skills_dir: str = skills_dir or os.path.expanduser("~/.claude/skills")
        self.loaded_skills: dict[str, dict[str, Any]] = {}
        self.skill_store = skill_store  # 整合自动提炼的技能存储

    def discover_skills(self) -> list[str]:
        """发现已安装的 Skills（包括自动提炼的）"""
        skill_ids: list[str] = []

        # 1. 发现 SKILL.md 规范的 Skills
        if os.path.exists(self.skills_dir):
            for item in os.listdir(self.skills_dir):
                skill_path: str = os.path.join(self.skills_dir, item)
                skill_md: str = os.path.join(skill_path, "SKILL.md")

                if os.path.exists(skill_md):
                    skill_ids.append(f"file:{item}")  # 标记为文件来源

        # 2. 发现自动提炼的 Skills
        if self.skill_store:
            from intentos.skill.store import SkillStore
            if isinstance(self.skill_store, SkillStore):
                for skill in self.skill_store.list_skills(limit=100):
                    skill_ids.append(f"auto:{skill.id}:{skill.name}")

        return skill_ids

    async def load_skill(self, skill_id: str) -> bool:
        """加载 Skill（支持文件来源和自动提炼）"""
        # 处理文件来源的 Skill
        if skill_id.startswith("file:"):
            return await self._load_file_skill(skill_id[5:])
        
        # 处理自动提炼的 Skill
        if skill_id.startswith("auto:"):
            return await self._load_auto_skill(skill_id[5:])
        
        return False

    async def _load_file_skill(self, skill_id: str) -> bool:
        """加载文件来源的 Skill（原有逻辑）"""
        skill_path: str = os.path.join(self.skills_dir, skill_id)
        skill_md: str = os.path.join(skill_path, "SKILL.md")

        if not os.path.exists(skill_md):
            return False

        try:
            # 解析 SKILL.md
            skill_data: dict[str, Any] = self._parse_skill_md(skill_md)

            # 注册 Skill 定义的能力
            await self._register_skill_capabilities(skill_id, skill_data)

            self.loaded_skills[skill_id] = skill_data
            return True
        except Exception as e:
            print(f"加载 Skill 失败：{skill_id}, 错误：{e}")
            return False

    async def _load_auto_skill(self, skill_ref: str) -> bool:
        """加载自动提炼的 Skill"""
        if not self.skill_store:
            return False
        
        try:
            # 解析 skill_ref: id:name
            parts = skill_ref.split(":", 1)
            skill_id = parts[0]
            
            from intentos.skill.store import SkillStore
            if isinstance(self.skill_store, SkillStore):
                skill = self.skill_store.get_skill(skill_id)
                if not skill:
                    return False
                
                # 注册自动提炼的 Skill
                await self._register_auto_skill_capabilities(skill)
                
                self.loaded_skills[f"auto:{skill_id}"] = {
                    "name": skill.name,
                    "description": skill.description,
                    "steps": len(skill.steps),
                }
                return True
        except Exception as e:
            print(f"加载自动 Skill 失败：{skill_ref}, 错误：{e}")
            return False
        
        return False

    def _parse_skill_md(self, path: str) -> dict[str, Any]:
        """解析 SKILL.md 文件"""
        import yaml

        with open(path) as f:
            content: str = f.read()

        # 提取 YAML front matter
        if content.startswith("---"):
            parts: list[str] = content.split("---", 2)
            if len(parts) >= 3:
                yaml_content: str = parts[1].strip()
                data: dict[str, Any] = yaml.safe_load(yaml_content)

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

    def _scan_resources(self, skill_path: str) -> dict[str, Optional[str]]:
        """扫描 Skill 资源"""
        return {
            "scripts": os.path.join(skill_path, "scripts")
            if os.path.exists(os.path.join(skill_path, "scripts"))
            else None,
            "references": os.path.join(skill_path, "references")
            if os.path.exists(os.path.join(skill_path, "references"))
            else None,
            "assets": os.path.join(skill_path, "assets")
            if os.path.exists(os.path.join(skill_path, "assets"))
            else None,
        }

    async def _register_skill_capabilities(self, skill_id: str, skill_data: dict[str, Any]) -> None:
        """注册 Skill 定义的能力"""
        spec: dict[str, str] = skill_data.get("spec", {})

        # 注册一个通用的 Skill 执行能力
        async def skill_handler(**kwargs: Any) -> dict[str, Any]:
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

    async def _register_auto_skill_capabilities(self, skill: Any) -> None:
        """注册自动提炼的 Skill 能力"""
        # 为每个步骤注册能力
        for i, step in enumerate(skill.steps):
            step_id = f"skill_{skill.id}_step{i}"
            
            async def step_handler(step=step, **kwargs: Any) -> dict[str, Any]:
                return {
                    "skill_id": skill.id,
                    "skill_name": skill.name,
                    "step": step.name,
                    "action": step.action,
                    "kwargs": kwargs,
                }
            
            self.registry.register(
                id=step_id,
                name=f"{skill.name} - {step.name}",
                description=step.description or f"执行 {skill.name} 的步骤 {i+1}",
                handler=step_handler,
                tags=["skill", "auto_generated", skill.id],
                metadata=skill.to_dict(),
                source="auto_skill",
            )

    def get_loaded_skills(self) -> list[str]:
        """获取已加载的 Skills"""
        return list(self.loaded_skills.keys())
