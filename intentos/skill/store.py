# -*- coding: utf-8 -*-
"""
IntentOS Skill Store

技能存储和检索
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import Skill, SkillLevel

logger = logging.getLogger(__name__)


class SkillStore:
    """
    技能存储器
    
    支持：
    - 技能存储和检索
    - 技能文件持久化（YAML）
    - 技能分类和标签索引
    - 使用统计追踪
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        初始化技能存储器
        
        Args:
            storage_dir: 存储目录，默认 ~/.intentos/skills
        """
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.intentos/skills")
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._skills: dict[str, Skill] = {}
        
        # 加载已存储的技能
        self._load_from_disk()
        
        logger.info(f"SkillStore 初始化完成：{self.storage_dir}")
    
    def save_skill(self, skill: Skill) -> None:
        """保存技能"""
        self._skills[skill.id] = skill
        
        # 持久化到 YAML 文件
        self._persist_skill(skill)
        logger.debug(f"技能 {skill.name} 已保存")
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        if skill_id in self._skills:
            return self._skills[skill_id]
        
        # 尝试从磁盘加载
        skill = self._load_skill_from_disk(skill_id)
        if skill:
            self._skills[skill_id] = skill
        return skill
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        if skill_id not in self._skills:
            skill = self._load_skill_from_disk(skill_id)
            if skill:
                self._skills[skill_id] = skill
        
        if skill_id in self._skills:
            skill = self._skills[skill_id]
            
            # 删除缓存
            del self._skills[skill_id]
            
            # 删除磁盘文件
            self._delete_skill_file(skill_id)
            
            logger.info(f"技能 {skill.name} 已删除")
            return True
        
        return False
    
    def list_skills(
        self,
        tag: Optional[str] = None,
        level: Optional[SkillLevel] = None,
        limit: int = 100,
    ) -> list[Skill]:
        """列出技能"""
        skills = list(self._skills.values())
        
        # 按标签过滤
        if tag:
            skills = [s for s in skills if tag in s.tags]
        
        # 按等级过滤
        if level:
            skills = [s for s in skills if s.level == level]
        
        # 按创建时间排序（最新的在前）
        skills.sort(key=lambda s: s.created_at, reverse=True)
        
        return skills[:limit]
    
    def search_skills(self, query: str, limit: int = 20) -> list[Skill]:
        """搜索技能"""
        query_lower = query.lower()
        results = []
        
        for skill in self._skills.values():
            # 搜索名称、描述、标签
            searchable = f"{skill.name} {skill.description} {' '.join(skill.tags)}".lower()
            
            if query_lower in searchable:
                results.append(skill)
        
        # 按相关度排序（简单实现：名称匹配优先）
        results.sort(
            key=lambda s: (
                query_lower in s.name.lower(),  # 名称匹配优先
                query_lower in s.description.lower(),
            ),
            reverse=True,
        )
        
        return results[:limit]
    
    def find_skills_by_trigger(
        self,
        input_text: str,
        confidence_threshold: float = 0.5,
    ) -> list[tuple[Skill, float]]:
        """
        根据输入文本查找匹配的技能
        
        Returns:
            [(技能，置信度), ...]
        """
        from .matcher import SkillMatcher
        
        matcher = SkillMatcher()
        results = []
        
        for skill in self._skills.values():
            confidence = matcher.match(skill, input_text)
            if confidence >= confidence_threshold:
                results.append((skill, confidence))
        
        # 按置信度排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def record_usage(self, skill_id: str, success: bool = True) -> None:
        """记录技能使用"""
        skill = self.get_skill(skill_id)
        if not skill:
            return
        
        skill.usage_count += 1
        skill.last_used_at = datetime.now()
        
        # 更新成功率（移动平均）
        alpha = 0.1  # 平滑因子
        if success:
            skill.success_rate = skill.success_rate * (1 - alpha) + 1.0 * alpha
        else:
            skill.success_rate = skill.success_rate * (1 - alpha) + 0.0 * alpha
        
        skill.updated_at = datetime.now()
        self.save_skill(skill)
    
    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total_skills = len(self._skills)
        
        # 按等级统计
        by_level = {}
        for skill in self._skills.values():
            level = skill.level.value
            by_level[level] = by_level.get(level, 0) + 1
        
        # 按来源统计
        by_source = {}
        for skill in self._skills.values():
            source = skill.created_from
            by_source[source] = by_source.get(source, 0) + 1
        
        # 热门标签
        tag_counts = {}
        for skill in self._skills.values():
            for tag in skill.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 使用最多的技能
        top_skills = sorted(
            self._skills.values(),
            key=lambda s: s.usage_count,
            reverse=True,
        )[:5]
        
        return {
            "total_skills": total_skills,
            "by_level": by_level,
            "by_source": by_source,
            "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "top_skills": [
                {"name": s.name, "usage_count": s.usage_count}
                for s in top_skills
            ],
        }
    
    def export_skill(self, skill_id: str) -> Optional[str]:
        """导出技能为 YAML 字符串"""
        skill = self.get_skill(skill_id)
        if not skill:
            return None
        
        return skill.to_yaml()
    
    def import_skill(self, yaml_str: str, source: str = "import") -> Optional[Skill]:
        """从 YAML 导入技能"""
        try:
            skill = Skill.from_yaml(yaml_str)
            skill.created_from = source
            skill.source_session_id = None
            skill.source_workflow_id = None
            self.save_skill(skill)
            return skill
        except Exception as e:
            logger.error(f"导入技能失败：{e}")
            return None
    
    def clear_all(self) -> None:
        """清除所有技能"""
        self._skills.clear()
        
        # 清除磁盘文件
        for file in self.storage_dir.glob("*.yaml"):
            file.unlink()
        
        logger.info("所有技能已清除")
    
    def _persist_skill(self, skill: Skill) -> None:
        """持久化技能到磁盘"""
        file_path = self.storage_dir / f"{skill.id}.yaml"
        
        yaml_content = skill.to_yaml()
        
        # 添加元数据头部
        metadata = {
            "---": "",
            "id": skill.id,
            "created_at": skill.created_at.isoformat(),
            "updated_at": skill.updated_at.isoformat(),
            "---": "",
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"---\n")
            f.write(f"id: {skill.id}\n")
            f.write(f"created_at: {skill.created_at.isoformat()}\n")
            f.write(f"updated_at: {skill.updated_at.isoformat()}\n")
            f.write(f"---\n\n")
            f.write(yaml_content)
    
    def _load_skill_from_disk(self, skill_id: str) -> Optional[Skill]:
        """从磁盘加载技能"""
        file_path = self.storage_dir / f"{skill_id}.yaml"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 跳过元数据头部
            if content.startswith("---"):
                parts = content.split("---", 3)
                if len(parts) >= 3:
                    yaml_content = parts[2].strip()
                else:
                    yaml_content = content
            else:
                yaml_content = content
            
            skill = Skill.from_yaml(yaml_content)
            return skill
        except Exception as e:
            logger.error(f"加载技能失败：{e}")
            return None
    
    def _load_from_disk(self) -> None:
        """从磁盘加载所有技能"""
        for file_path in self.storage_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 跳过元数据头部
                if content.startswith("---"):
                    parts = content.split("---", 3)
                    if len(parts) >= 3:
                        yaml_content = parts[2].strip()
                    else:
                        yaml_content = content
                else:
                    yaml_content = content
                
                skill = Skill.from_yaml(yaml_content)
                self._skills[skill.id] = skill
                
            except Exception as e:
                logger.error(f"加载文件 {file_path} 失败：{e}")
        
        logger.info(f"从磁盘加载了 {len(self._skills)} 个技能")
    
    def _delete_skill_file(self, skill_id: str) -> None:
        """删除技能文件"""
        file_path = self.storage_dir / f"{skill_id}.yaml"
        if file_path.exists():
            file_path.unlink()


# 全局技能存储器实例
_global_skill_store: Optional[SkillStore] = None


def get_skill_store(storage_dir: Optional[str] = None) -> SkillStore:
    """获取全局技能存储器"""
    global _global_skill_store
    if _global_skill_store is None:
        _global_skill_store = SkillStore(storage_dir)
    return _global_skill_store


def reset_skill_store() -> None:
    """重置技能存储器"""
    global _global_skill_store
    _global_skill_store = None
