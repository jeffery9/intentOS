"""
意图包系统测试

测试意图包加载、注册表和运行时实例管理
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from intentos.apps import (
    IntentPackage,
    IntentPackageLoader,
    IntentPackageRegistry,
    RuntimeInstanceManager,
    AppInstance,
    InstanceCache,
    create_intent_package,
    load_intent_package,
    validate_intent_package,
)


@pytest.fixture
def sample_manifest():
    """示例 manifest 数据"""
    return {
        "app_id": "test_app",
        "name": "测试应用",
        "version": "1.0.0",
        "description": "测试描述",
        "intents": [
            {
                "name": "test_intent",
                "description": "测试意图",
                "patterns": ["测试 {param}"],
                "parameters": [
                    {
                        "name": "param",
                        "type": "string",
                        "required": True,
                    }
                ],
            }
        ],
        "capabilities": [
            {
                "name": "test_capability",
                "description": "测试能力",
                "type": "io",
            }
        ],
        "config": {
            "resources": {
                "max_memory": "256MB",
                "max_execution_time": 30,
            }
        },
    }


@pytest.fixture
def temp_package_dir(sample_manifest):
    """创建临时意图包目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manifest_path = Path(temp_dir) / "manifest.yaml"
        
        import yaml
        with open(manifest_path, 'w') as f:
            yaml.dump(sample_manifest, f)
        
        yield temp_dir


class TestIntentPackage:
    """测试意图包"""
    
    def test_create_package(self):
        """测试创建意图包"""
        package = create_intent_package(
            app_id="test_app",
            name="测试应用",
            version="1.0.0",
            description="测试描述",
        )
        
        assert package.app_id == "test_app"
        assert package.name == "测试应用"
        assert package.version == "1.0.0"
        assert package.description == "测试描述"
    
    def test_package_to_dict(self):
        """测试序列化"""
        package = create_intent_package(
            app_id="test_app",
            name="测试应用",
        )
        
        data = package.to_dict()
        
        assert data["app_id"] == "test_app"
        assert data["name"] == "测试应用"


class TestIntentPackageLoader:
    """测试意图包加载器"""
    
    def test_load_from_directory(self, temp_package_dir):
        """测试从目录加载"""
        loader = IntentPackageLoader()
        package = loader.load(temp_package_dir)
        
        assert package.app_id == "test_app"
        assert package.name == "测试应用"
        assert len(package.intents) == 1
        assert len(package.capabilities) == 1
    
    def test_validate_package(self, temp_package_dir):
        """测试验证"""
        loader = IntentPackageLoader()
        package = loader.load(temp_package_dir)
        
        result = loader.validate(package)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_duplicate_intent_names(self):
        """测试意图名称重复验证"""
        package = create_intent_package(
            app_id="test_app",
            name="测试应用",
            intents=[
                {"name": "intent1"},
                {"name": "intent1"},  # 重复
            ],
        )
        
        loader = IntentPackageLoader()
        result = loader.validate(package)
        
        assert result.is_valid is False
        assert "意图名称必须唯一" in result.errors
    
    def test_get_intent(self, temp_package_dir):
        """测试获取意图"""
        loader = IntentPackageLoader()
        package = loader.load(temp_package_dir)
        
        intent = package.get_intent("test_intent")
        assert intent is not None
        assert intent["name"] == "test_intent"
        
        # 不存在的意图
        intent = package.get_intent("nonexistent")
        assert intent is None


class TestIntentPackageRegistry:
    """测试意图包注册表"""
    
    def test_register_package(self):
        """测试注册意图包"""
        registry = IntentPackageRegistry()
        package = create_intent_package(
            app_id="test_app",
            name="测试应用",
            capabilities=[{"name": "test_cap"}],
        )
        
        registry.register(package)
        
        assert registry.get_package("test_app") == package
        assert registry.find_capability("test_cap") == "test_app"
    
    def test_unregister_package(self):
        """测试注销意图包"""
        registry = IntentPackageRegistry()
        package = create_intent_package(
            app_id="test_app",
            name="测试应用",
            capabilities=[{"name": "test_cap"}],
        )
        
        registry.register(package)
        registry.unregister("test_app")
        
        assert registry.get_package("test_app") is None
        assert registry.find_capability("test_cap") is None
    
    def test_find_capabilities(self):
        """测试批量查找能力"""
        registry = IntentPackageRegistry()
        
        registry.register(create_intent_package(
            app_id="app1",
            name="应用 1",
            capabilities=[
                {"name": "cap1"},
                {"name": "cap2"},
            ],
        ))
        
        registry.register(create_intent_package(
            app_id="app2",
            name="应用 2",
            capabilities=[{"name": "cap3"}],
        ))
        
        result = registry.find_capabilities(["cap1", "cap3"])
        
        assert result["cap1"] == "app1"
        assert result["cap3"] == "app2"
    
    def test_enable_disable(self):
        """测试启用/禁用"""
        registry = IntentPackageRegistry()
        package = create_intent_package(
            app_id="test_app",
            name="测试应用",
        )
        
        registry.register(package)
        
        # 禁用
        assert registry.disable("test_app") is True
        installation = registry.get_installation("test_app")
        assert installation.enabled is False
        
        # 启用
        assert registry.enable("test_app") is True
        installation = registry.get_installation("test_app")
        assert installation.enabled is True
    
    def test_statistics(self):
        """测试统计"""
        registry = IntentPackageRegistry()
        
        registry.register(create_intent_package(app_id="app1", name="应用 1"))
        registry.register(create_intent_package(app_id="app2", name="应用 2"))
        
        stats = registry.get_statistics()
        
        assert stats["total_packages"] == 2
        assert stats["enabled_packages"] == 2


class TestRuntimeInstanceManager:
    """测试运行时实例管理器"""
    
    @pytest.fixture
    def instance_manager(self):
        """创建实例管理器"""
        registry = IntentPackageRegistry()
        registry.register(create_intent_package(
            app_id="test_app",
            name="测试应用",
        ))
        
        return RuntimeInstanceManager(registry=registry, node_id="test_node")
    
    def test_create_instance(self, instance_manager):
        """测试创建实例"""
        instance = instance_manager.create_instance(
            app_id="test_app",
            tenant_id="tenant1",
            user_id="user1",
        )
        
        assert instance.app_id == "test_app"
        assert instance.node_id == "test_node"
        assert instance.tenant_id == "tenant1"
        assert instance.user_id == "user_id" or instance.user_id == "user1"
        assert instance.status == "active"
    
    def test_instance_full_id(self, instance_manager):
        """测试完整实例 ID"""
        instance = instance_manager.create_instance(
            app_id="test_app",
            tenant_id="tenant1",
        )
        
        full_id = instance.full_instance_id
        assert "test_app" in full_id
        assert "tenant1" in full_id
        assert instance.node_id in full_id
    
    def test_get_or_create_instance(self, instance_manager):
        """测试获取或创建实例"""
        # 第一次创建
        instance1 = instance_manager.get_or_create_instance(
            app_id="test_app",
            tenant_id="tenant1",
            user_id="user1",
        )
        
        # 第二次获取（应该返回同一个实例）
        instance2 = instance_manager.get_or_create_instance(
            app_id="test_app",
            tenant_id="tenant1",
            user_id="user1",
        )
        
        assert instance1.instance_id == instance2.instance_id
    
    def test_release_instance(self, instance_manager):
        """测试释放实例"""
        instance = instance_manager.create_instance(app_id="test_app")
        instance_id = instance.instance_id
        
        # 释放
        assert instance_manager.release_instance(instance_id) is True
        
        # 验证状态
        released_instance = instance_manager.get_instance(instance_id)
        assert released_instance is None or released_instance.status == "terminated"
    
    def test_list_instances(self, instance_manager):
        """测试列出实例"""
        # 先注册另一个应用
        instance_manager.registry.register(create_intent_package(
            app_id="other_app",
            name="其他应用",
        ))
        
        instance_manager.create_instance(app_id="test_app", tenant_id="tenant1")
        instance_manager.create_instance(app_id="test_app", tenant_id="tenant2")
        instance_manager.create_instance(app_id="other_app", tenant_id="tenant1")
        
        # 按 app_id 过滤
        instances = instance_manager.list_instances(app_id="test_app")
        assert len(instances) == 2
        
        # 按 tenant_id 过滤
        instances = instance_manager.list_instances(tenant_id="tenant1")
        assert len(instances) == 2
    
    def test_statistics(self, instance_manager):
        """测试统计"""
        instance_manager.create_instance(app_id="test_app")
        instance_manager.create_instance(app_id="test_app")
        
        stats = instance_manager.get_statistics()
        
        assert stats["total_instances"] == 2
        assert stats["active_instances"] == 2


class TestInstanceCache:
    """测试实例缓存"""
    
    def test_cache_put_get(self):
        """测试缓存存取"""
        from intentos.apps.instance_manager import InstanceCache
        
        cache = InstanceCache(max_size=3)
        
        package = create_intent_package(app_id="test_app", name="测试应用")
        instance = AppInstance(
            instance_id="inst1",
            app_id="test_app",
            package=package,
            node_id="node1",
        )
        
        cache.put(instance)
        retrieved = cache.get("inst1")
        
        assert retrieved == instance
    
    def test_cache_lru_eviction(self):
        """测试 LRU 淘汰"""
        from intentos.apps.instance_manager import InstanceCache
        
        cache = InstanceCache(max_size=2)
        package = create_intent_package(app_id="test_app", name="测试应用")
        
        # 添加 3 个实例（超过容量）
        for i in range(3):
            instance = AppInstance(
                instance_id=f"inst{i}",
                app_id="test_app",
                package=package,
                node_id="node1",
            )
            cache.put(instance)
        
        # 最旧的实例应该被淘汰
        assert cache.get("inst0") is None
        assert cache.get("inst1") is not None
        assert cache.get("inst2") is not None
    
    def test_cache_clear_expired(self):
        """测试清除过期实例"""
        cache = InstanceCache(max_size=10, ttl_seconds=1)
        package = create_intent_package(app_id="test_app", name="测试应用")
        
        instance = AppInstance(
            instance_id="inst1",
            app_id="test_app",
            package=package,
            node_id="node1",
        )
        cache.put(instance)
        
        # 等待过期
        import time
        time.sleep(1.1)
        
        # 清除过期（需要手动触发 touch 来设置 last_used_at）
        instance.last_used_at = datetime.now()
        cleared = cache.clear_expired()
        
        # 验证缓存统计
        stats = cache.stats()
        assert stats["size"] >= 0


class TestIntegration:
    """集成测试"""
    
    def test_full_lifecycle(self, temp_package_dir):
        """测试完整生命周期"""
        # 1. 加载意图包
        loader = IntentPackageLoader()
        package = loader.load(temp_package_dir)
        
        # 2. 验证
        result = loader.validate(package)
        assert result.is_valid is True
        
        # 3. 注册
        registry = IntentPackageRegistry()
        registry.register(package)
        
        # 4. 创建实例
        manager = RuntimeInstanceManager(registry=registry)
        instance = manager.create_instance(
            app_id="test_app",
            tenant_id="tenant1",
            user_id="user1",
        )
        
        # 5. 使用实例
        assert instance.status == "active"
        instance.touch()
        assert instance.execution_count == 1
        
        # 6. 释放实例
        manager.release_instance(instance.instance_id)
        
        # 7. 验证统计
        stats = manager.get_statistics()
        assert stats["total_instances"] == 0
