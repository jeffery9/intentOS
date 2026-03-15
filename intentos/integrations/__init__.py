"""
IntentOS 集成模块

支持:
- Skill 规范 (Claude Skills)
- MCP (Model Context Protocol)
"""

from .skill import SkillSpec, SkillLoader, get_skill_loader
from .mcp import MCPClient, get_mcp_client

__all__ = [
    # Skill
    "SkillSpec",
    "SkillLoader",
    "get_skill_loader",
    
    # MCP
    "MCPClient",
    "get_mcp_client",
]
