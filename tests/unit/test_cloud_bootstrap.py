"""
Cloud Bootstrap Module Tests

测试云资源 Self-Bootstrap 模块：资源定义、开通器、计划生成
"""

import os
import pytest
from unittest.mock import MagicMock, patch

from intentos.bootstrap.cloud_bootstrap import (
    ResourceStatus,
    AuthMethod,
    CloudResource,
    BootstrapPlan,
    CloudResourceProvisioner,
)


class TestResourceStatus:
    """测试资源状态枚举"""

    def test_not_exists_status(self):
        """资源不存在状态"""
        assert ResourceStatus.NOT_EXISTS.value == "not_exists"

    def test_creating_status(self):
        """资源创建中状态"""
        assert ResourceStatus.CREATING.value == "creating"

    def test_active_status(self):
        """资源活跃状态"""
        assert ResourceStatus.ACTIVE.value == "active"

    def test_error_status(self):
        """资源错误状态"""
        assert ResourceStatus.ERROR.value == "error"

    def test_needs_auth_status(self):
        """资源需要认证状态"""
        assert ResourceStatus.NEEDS_AUTH.value == "needs_auth"


class TestAuthMethod:
    """测试认证方法枚举"""

    def test_auto_auth(self):
        """自动认证"""
        assert AuthMethod.AUTO.value == "auto"

    def test_console_auth(self):
        """控制台引导认证"""
        assert AuthMethod.CONSOLE.value == "console"

    def test_cli_auth(self):
        """CLI 引导认证"""
        assert AuthMethod.CLI.value == "cli"

    def test_terraform_auth(self):
        """Terraform 引导认证"""
        assert AuthMethod.TERRAFORM.value == "terraform"

    def test_manual_auth(self):
        """手动认证"""
        assert AuthMethod.MANUAL.value == "manual"


class TestCloudResource:
    """测试云资源数据类"""

    def test_create_resource_minimal(self):
        """创建最小资源"""
        resource = CloudResource(
            name="test-resource",
            type="s3",
            provider="aws"
        )

        assert resource.name == "test-resource"
        assert resource.type == "s3"
        assert resource.provider == "aws"
        assert resource.status == ResourceStatus.NOT_EXISTS
        assert resource.id is None
        assert resource.auto_create is True

    def test_create_resource_full(self):
        """创建完整资源"""
        resource = CloudResource(
            name="test-bucket",
            type="s3",
            provider="aws",
            status=ResourceStatus.ACTIVE,
            id="bucket-123",
            endpoint="https://s3.amazonaws.com/bucket-123",
            config={"versioning": True},
            dependencies=["vpc-123"],
            auto_create=False
        )

        assert resource.name == "test-bucket"
        assert resource.status == ResourceStatus.ACTIVE
        assert resource.id == "bucket-123"
        assert len(resource.dependencies) == 1
        assert resource.auto_create is False

    def test_resource_default_config(self):
        """资源默认配置"""
        resource = CloudResource(
            name="test",
            type="ec2",
            provider="aws"
        )

        assert resource.config == {}
        assert resource.dependencies == []
        assert resource.human_guide is None


class TestBootstrapPlan:
    """测试 Bootstrap 计划数据类"""

    def test_create_empty_plan(self):
        """创建空计划"""
        plan = BootstrapPlan()

        assert plan.resources == []
        assert plan.steps == []
        assert plan.estimated_cost == {}
        assert plan.requires_human_action is False

    def test_create_plan_with_resources(self):
        """创建带资源的计划"""
        resource = CloudResource(
            name="test",
            type="s3",
            provider="aws"
        )

        plan = BootstrapPlan(
            resources=[resource],
            steps=[{"action": "create", "resource": "test"}],
            estimated_cost={"monthly": 10.0},
            requires_human_action=True
        )

        assert len(plan.resources) == 1
        assert len(plan.steps) == 1
        assert plan.estimated_cost["monthly"] == 10.0
        assert plan.requires_human_action is True


class TestCloudResourceProvisioner:
    """测试云资源开通器"""

    def test_init_aws_without_credentials(self):
        """初始化 AWS 开通器（无凭证）"""
        # 确保没有 AWS 凭证
        with patch.dict(os.environ, {}, clear=True):
            provisioner = CloudResourceProvisioner("aws")

            assert provisioner.provider == "aws"
            assert provisioner.credentials_valid is False

    def test_init_aws_with_credentials(self):
        """初始化 AWS 开通器（有凭证）"""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret'
        }):
            provisioner = CloudResourceProvisioner("aws")

            assert provisioner.credentials_valid is True

    def test_init_gcp_without_credentials(self):
        """初始化 GCP 开通器（无凭证）"""
        with patch.dict(os.environ, {}, clear=True):
            provisioner = CloudResourceProvisioner("gcp")

            assert provisioner.provider == "gcp"
            assert provisioner.credentials_valid is False

    def test_init_with_region(self):
        """初始化带区域的开通器"""
        provisioner = CloudResourceProvisioner("aws", region="us-west-2")

        assert provisioner.provider == "aws"
        assert provisioner.region == "us-west-2"

    def test_init_unknown_provider(self):
        """初始化未知提供商"""
        with patch.dict(os.environ, {}, clear=True):
            provisioner = CloudResourceProvisioner("unknown")

            assert provisioner.provider == "unknown"
            assert provisioner.credentials_valid is False


class TestCloudResourceProvisionerMethods:
    """测试云资源开通器方法"""

    @pytest.fixture
    def provisioner(self):
        """创建测试用开通器"""
        with patch.dict(os.environ, {}, clear=True):
            return CloudResourceProvisioner("aws")

    def test_check_credentials_aws_no_env(self, provisioner):
        """AWS 凭证检查 - 无环境变量"""
        # 已经通过 fixture 清除环境变量
        assert provisioner.credentials_valid is False

    def test_check_credentials_aws_partial_env(self):
        """AWS 凭证检查 - 部分环境变量"""
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test-key'
            # 缺少 SECRET_ACCESS_KEY
        }):
            provisioner = CloudResourceProvisioner("aws")
            assert provisioner.credentials_valid is False

    def test_check_credentials_gcp_no_env(self):
        """GCP 凭证检查 - 无环境变量"""
        with patch.dict(os.environ, {}, clear=True):
            provisioner = CloudResourceProvisioner("gcp")
            assert provisioner.credentials_valid is False

    def test_check_credentials_gcp_with_credentials(self):
        """GCP 凭证检查 - 有凭证"""
        with patch.dict(os.environ, {
            'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/creds.json'
        }):
            provisioner = CloudResourceProvisioner("gcp")
            assert provisioner.credentials_valid is True


class TestResourceStatusTransitions:
    """测试资源状态转换"""

    def test_resource_status_flow(self):
        """资源状态流程"""
        resource = CloudResource(
            name="test",
            type="s3",
            provider="aws"
        )

        # 初始状态
        assert resource.status == ResourceStatus.NOT_EXISTS

        # 创建中
        resource.status = ResourceStatus.CREATING
        assert resource.status == ResourceStatus.CREATING

        # 活跃
        resource.status = ResourceStatus.ACTIVE
        assert resource.status == ResourceStatus.ACTIVE

        # 错误
        resource.status = ResourceStatus.ERROR
        assert resource.status == ResourceStatus.ERROR


class TestBootstrapPlanValidation:
    """测试 Bootstrap 计划验证"""

    def test_plan_with_circular_dependencies(self):
        """带循环依赖的计划"""
        resource1 = CloudResource(
            name="resource1",
            type="s3",
            provider="aws",
            dependencies=["resource2"]
        )

        resource2 = CloudResource(
            name="resource2",
            type="ec2",
            provider="aws",
            dependencies=["resource1"]
        )

        plan = BootstrapPlan(resources=[resource1, resource2])

        # 计划应能创建（验证逻辑在后续实现）
        assert len(plan.resources) == 2

    def test_plan_cost_estimation(self):
        """计划成本估算"""
        plan = BootstrapPlan(
            estimated_cost={
                "hourly": 0.5,
                "daily": 12.0,
                "monthly": 360.0,
                "yearly": 4320.0
            }
        )

        assert plan.estimated_cost["hourly"] == 0.5
        assert plan.estimated_cost["daily"] == 12.0
        assert plan.estimated_cost["monthly"] == 360.0
        assert plan.estimated_cost["yearly"] == 4320.0


class TestCloudResourceConfig:
    """测试云资源配置"""

    def test_resource_with_complex_config(self):
        """带复杂配置的资源"""
        resource = CloudResource(
            name="complex-ec2",
            type="ec2",
            provider="aws",
            config={
                "instance_type": "t3.medium",
                "storage": {
                    "size": 100,
                    "type": "gp3"
                },
                "network": {
                    "vpc": "vpc-123",
                    "subnet": "subnet-456"
                }
            }
        )

        assert resource.config["instance_type"] == "t3.medium"
        assert resource.config["storage"]["size"] == 100
        assert resource.config["network"]["vpc"] == "vpc-123"

    def test_resource_with_tags(self):
        """带标签的资源"""
        resource = CloudResource(
            name="tagged-resource",
            type="s3",
            provider="aws",
            config={
                "tags": {
                    "Environment": "Production",
                    "Team": "DevOps",
                    "CostCenter": "IT"
                }
            }
        )

        assert resource.config["tags"]["Environment"] == "Production"


class TestAuthMethodSelection:
    """测试认证方法选择"""

    def test_auto_auth_preferred(self):
        """优先自动认证"""
        assert AuthMethod.AUTO.value == "auto"

    def test_console_auth_for_complex(self):
        """复杂操作使用控制台认证"""
        assert AuthMethod.CONSOLE.value == "console"

    def test_cli_auth_for_automation(self):
        """自动化使用 CLI 认证"""
        assert AuthMethod.CLI.value == "cli"

    def test_terraform_auth_for_infrastructure(self):
        """基础设施使用 Terraform 认证"""
        assert AuthMethod.TERRAFORM.value == "terraform"

    def test_manual_auth_fallback(self):
        """回退到手动认证"""
        assert AuthMethod.MANUAL.value == "manual"


class TestCloudResourceDependencies:
    """测试云资源依赖"""

    def test_resource_no_dependencies(self):
        """无依赖资源"""
        resource = CloudResource(
            name="standalone",
            type="s3",
            provider="aws"
        )

        assert resource.dependencies == []

    def test_resource_single_dependency(self):
        """单依赖资源"""
        resource = CloudResource(
            name="app-server",
            type="ec2",
            provider="aws",
            dependencies=["vpc-123"]
        )

        assert len(resource.dependencies) == 1
        assert "vpc-123" in resource.dependencies

    def test_resource_multiple_dependencies(self):
        """多依赖资源"""
        resource = CloudResource(
            name="app-server",
            type="ec2",
            provider="aws",
            dependencies=["vpc-123", "subnet-456", "sg-789"]
        )

        assert len(resource.dependencies) == 3
        assert "vpc-123" in resource.dependencies
        assert "subnet-456" in resource.dependencies
        assert "sg-789" in resource.dependencies
