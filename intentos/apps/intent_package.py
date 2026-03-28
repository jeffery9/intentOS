"""
意图包加载器 (Intent Package Loader)

负责加载、验证和解析意图包
"""

from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class IntentPackage:
    """
    意图包
    
    从 manifest.yaml 加载的完整意图包
    """
    app_id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = "MIT"
    homepage: str = ""
    
    # 意图定义
    intents: list[dict[str, Any]] = field(default_factory=list)
    
    # 能力需求
    capabilities: list[dict[str, Any]] = field(default_factory=list)
    
    # 配置
    config: dict[str, Any] = field(default_factory=dict)
    
    # 依赖
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    
    # 分布式配置
    distributed: dict[str, Any] = field(default_factory=dict)
    
    # 监控配置
    monitoring: dict[str, Any] = field(default_factory=dict)
    
    # 发布配置
    publishing: dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    loaded_at: datetime = field(default_factory=datetime.now)
    package_path: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "app_id": self.app_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "homepage": self.homepage,
            "intents": self.intents,
            "capabilities": self.capabilities,
            "config": self.config,
            "dependencies": self.dependencies,
            "distributed": self.distributed,
            "monitoring": self.monitoring,
            "publishing": self.publishing,
        }
    
    def get_intent(self, intent_name: str) -> Optional[dict[str, Any]]:
        """获取指定意图"""
        for intent in self.intents:
            if intent["name"] == intent_name:
                return intent
        return None
    
    def get_capability(self, capability_name: str) -> Optional[dict[str, Any]]:
        """获取指定能力"""
        for cap in self.capabilities:
            if cap["name"] == capability_name:
                return cap
        return None


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """添加错误"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """添加警告"""
        self.warnings.append(warning)


class IntentPackageLoader:
    """
    意图包加载器
    
    支持从目录或 .intentos 压缩包加载
    """
    
    def __init__(self):
        self.loaded_packages: dict[str, IntentPackage] = {}
    
    def load(self, path: str) -> IntentPackage:
        """
        加载意图包
        
        Args:
            path: 目录路径或 .intentos 文件路径
            
        Returns:
            加载的意图包
        """
        path_obj = Path(path)
        
        if path_obj.suffix == ".intentos":
            return self._load_from_zip(path_obj)
        else:
            return self._load_from_directory(path_obj)
    
    def _load_from_directory(self, path: Path) -> IntentPackage:
        """从目录加载"""
        manifest_path = path / "manifest.yaml"
        
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest.yaml not found in {path}")
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = yaml.safe_load(f)
        
        package = self._parse_manifest(manifest_data, str(path))
        self.loaded_packages[package.app_id] = package
        
        return package
    
    def _load_from_zip(self, path: Path) -> IntentPackage:
        """从压缩包加载"""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            return self._load_from_directory(Path(temp_dir))
    
    def _parse_manifest(self, data: dict[str, Any], package_path: str) -> IntentPackage:
        """解析 manifest.yaml"""
        # 验证必需字段
        required_fields = ["app_id", "name", "version", "intents"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        package = IntentPackage(
            app_id=data["app_id"],
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            license=data.get("license", "MIT"),
            homepage=data.get("homepage", ""),
            intents=data.get("intents", []),
            capabilities=data.get("capabilities", []),
            config=data.get("config", {}),
            dependencies=data.get("dependencies", []),
            distributed=data.get("distributed", {}),
            monitoring=data.get("monitoring", {}),
            publishing=data.get("publishing", {}),
            package_path=package_path,
        )
        
        return package
    
    def validate(self, package: IntentPackage) -> ValidationResult:
        """
        验证意图包
        
        检查：
        1. Schema 合规性
        2. 意图名称唯一性
        3. 能力引用有效性
        4. 参数类型匹配
        5. 资源配置合理性
        """
        result = ValidationResult(is_valid=True)
        
        # 1. 检查意图名称唯一性
        intent_names = [i["name"] for i in package.intents]
        if len(intent_names) != len(set(intent_names)):
            result.add_error("意图名称必须唯一")
        
        # 2. 检查能力名称唯一性
        cap_names = [c["name"] for c in package.capabilities]
        if len(cap_names) != len(set(cap_names)):
            result.add_error("能力名称必须唯一")
        
        # 3. 检查意图中的能力引用
        capability_names = set(cap_names)
        for intent in package.intents:
            for binding in intent.get("capability_bindings", []):
                if binding["capability"] not in capability_names:
                    result.add_warning(
                        f"意图 {intent['name']} 引用了未声明的能力：{binding['capability']}"
                    )
        
        # 4. 检查参数定义
        for intent in package.intents:
            params = intent.get("parameters", [])
            param_names = [p["name"] for p in params]
            if len(param_names) != len(set(param_names)):
                result.add_error(f"意图 {intent['name']} 中存在重复参数")
            
            # 检查参数类型
            for param in params:
                param_type = param.get("type", "string")
                valid_types = ["string", "number", "integer", "boolean", "array", "object", "enum", "date", "datetime"]
                if param_type not in valid_types:
                    result.add_warning(
                        f"意图 {intent['name']} 的参数 {param['name']} 使用了非标准类型：{param_type}"
                    )
        
        # 5. 检查资源配置
        resources = package.config.get("resources", {})
        if resources:
            max_memory = resources.get("max_memory", "512MB")
            if not self._is_valid_memory(max_memory):
                result.add_warning(f"无效的资源配置：max_memory={max_memory}")
            
            max_time = resources.get("max_execution_time", 60)
            if max_time > 300:
                result.add_warning(f"执行时间过长：{max_time}秒，建议不超过 300 秒")
        
        # 6. 检查分布式配置
        distributed = package.distributed
        if distributed.get("enabled", False):
            if "data_partitions" not in distributed:
                result.add_warning("启用了分布式执行但未指定数据分区键")
        
        return result
    
    def _is_valid_memory(self, memory_str: str) -> bool:
        """验证内存配置"""
        import re
        pattern = r'^\d+(MB|GB|KB)$'
        return bool(re.match(pattern, memory_str, re.IGNORECASE))
    
    def get_package(self, app_id: str) -> Optional[IntentPackage]:
        """获取已加载的意图包"""
        return self.loaded_packages.get(app_id)
    
    def list_packages(self) -> list[IntentPackage]:
        """列出所有已加载的意图包"""
        return list(self.loaded_packages.values())
    
    def unload(self, app_id: str) -> bool:
        """卸载意图包"""
        if app_id in self.loaded_packages:
            del self.loaded_packages[app_id]
            return True
        return False


# =============================================================================
# 工厂函数
# =============================================================================


def load_intent_package(path: str) -> IntentPackage:
    """加载意图包"""
    loader = IntentPackageLoader()
    return loader.load(path)


def validate_intent_package(package: IntentPackage) -> ValidationResult:
    """验证意图包"""
    loader = IntentPackageLoader()
    return loader.validate(package)


def create_intent_package(
    app_id: str,
    name: str,
    version: str = "1.0.0",
    description: str = "",
    intents: Optional[list[dict]] = None,
    capabilities: Optional[list[dict]] = None,
) -> IntentPackage:
    """创建意图包"""
    return IntentPackage(
        app_id=app_id,
        name=name,
        version=version,
        description=description,
        intents=intents or [],
        capabilities=capabilities or [],
    )
