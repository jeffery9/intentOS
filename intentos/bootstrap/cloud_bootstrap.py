"""
IntentOS 云资源 Self-Bootstrap 模块

实现云资源的自动开通和人类引导授权
"""

from __future__ import annotations
import logging

import asyncio
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ResourceStatus(Enum):
    """资源状态"""
    NOT_EXISTS = "not_exists"
    CREATING = "creating"
    ACTIVE = "active"
    ERROR = "error"
    NEEDS_AUTH = "needs_auth"


class AuthMethod(Enum):
    """认证方式"""
    AUTO = "auto"              # 自动开通（有凭证）
    CONSOLE = "console"        # 引导控制台操作
    CLI = "cli"                # 引导 CLI 命令
    TERRAFORM = "terraform"    # 引导 Terraform
    MANUAL = "manual"          # 手动操作


@dataclass
class CloudResource:
    """云资源定义"""
    name: str
    type: str
    provider: str
    status: ResourceStatus = ResourceStatus.NOT_EXISTS
    id: Optional[str] = None
    endpoint: Optional[str] = None
    config: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    auto_create: bool = True
    human_guide: Optional[dict[str, str]] = None


@dataclass
class BootstrapPlan:
    """Bootstrap 计划"""
    resources: list[CloudResource] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    estimated_cost: dict[str, float] = field(default_factory=dict)
    requires_human_action: bool = False


class CloudResourceProvisioner:
    """
    云资源开通器

    支持自动开通和人类引导授权
    """

    def __init__(self, provider: str, region: str = ""):
        self.provider = provider
        self.region = region
        self.credentials_valid = False
        self._check_credentials()

    def _check_credentials(self) -> None:
        """检查云凭证"""
        if self.provider == "aws":
            self.credentials_valid = bool(
                os.getenv('AWS_ACCESS_KEY_ID') and
                os.getenv('AWS_SECRET_ACCESS_KEY')
            )
        elif self.provider == "gcp":
            self.credentials_valid = bool(
                os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            )
        elif self.provider == "azure":
            self.credentials_valid = bool(
                os.getenv('ARM_CLIENT_ID') and
                os.getenv('ARM_CLIENT_SECRET')
            )
        elif self.provider == "docker":
            self.credentials_valid = True

    async def check_resource(self, resource: CloudResource) -> ResourceStatus:
        """检查资源是否存在"""
        if self.provider == "aws":
            return await self._check_aws_resource(resource)
        elif self.provider == "gcp":
            return await self._check_gcp_resource(resource)
        elif self.provider == "docker":
            return await self._check_docker_resource(resource)
        return ResourceStatus.NOT_EXISTS

    async def _check_aws_resource(self, resource: CloudResource) -> ResourceStatus:
        """检查 AWS 资源"""
        if not self.credentials_valid:
            return ResourceStatus.NEEDS_AUTH

        try:
            import boto3

            if resource.type == "vpc":
                client = boto3.client('ec2', region_name=self.region)
                response = client.describe_vpcs(
                    Filters=[{'Name': 'tag:Name', 'Values': [resource.name]}]
                )
                if response['Vpcs']:
                    resource.id = response['Vpcs'][0]['VpcId']
                    return ResourceStatus.ACTIVE

            elif resource.type == "ecs_cluster":
                client = boto3.client('ecs', region_name=self.region)
                response = client.describe_clusters(clusters=[resource.name])
                if response['clusters']:
                    resource.id = response['clusters'][0]['clusterArn']
                    return ResourceStatus.ACTIVE

            elif resource.type == "elasticache":
                client = boto3.client('elasticache', region_name=self.region)
                response = client.describe_cache_clusters(
                    CacheClusterId=resource.name
                )
                if response['CacheClusters']:
                    resource.id = response['CacheClusters'][0]['CacheClusterId']
                    return ResourceStatus.ACTIVE

            return ResourceStatus.NOT_EXISTS

        except Exception as e:
            if "credential" in str(e).lower() or "auth" in str(e).lower():
                return ResourceStatus.NEEDS_AUTH
            return ResourceStatus.ERROR

    async def create_resource(self, resource: CloudResource) -> bool:
        """创建资源"""
        if not self.credentials_valid:
            # 需要人类介入
            return await self._guide_human_creation(resource)

        if self.provider == "aws":
            return await self._create_aws_resource(resource)
        elif self.provider == "gcp":
            return await self._create_gcp_resource(resource)
        elif self.provider == "docker":
            return await self._create_docker_resource(resource)

        return False

    async def _create_aws_resource(self, resource: CloudResource) -> bool:
        """创建 AWS 资源"""
        try:
            import boto3
            import botocore

            if resource.type == "vpc":
                client = boto3.client('ec2', region_name=self.region)
                response = client.create_vpc(
                    CidrBlock=resource.config.get('cidr', '10.0.0.0/16'),
                    TagSpecifications=[{
                        'ResourceType': 'vpc',
                        'Tags': [{'Key': 'Name', 'Value': resource.name}]
                    }]
                )
                resource.id = response['Vpc']['VpcId']
                print(f"  ✓ VPC 已创建：{resource.id}")

            elif resource.type == "ecs_cluster":
                client = boto3.client('ecs', region_name=self.region)
                response = client.create_cluster(
                    clusterName=resource.name,
                    tags=[{'key': 'managed-by', 'value': 'intentos'}]
                )
                resource.id = response['cluster']['clusterArn']
                print(f"  ✓ ECS Cluster 已创建：{resource.id}")

            elif resource.type == "elasticache":
                client = boto3.client('elasticache', region_name=self.region)
                response = client.create_cache_cluster(
                    CacheClusterId=resource.name,
                    Engine='redis',
                    CacheNodeType=resource.config.get('node_type', 'cache.t3.micro'),
                    NumCacheNodes=1,
                    Tags=[{'Key': 'managed-by', 'Value': 'intentos'}]
                )
                resource.id = response['CacheCluster']['CacheClusterId']
                print(f"  ✓ ElastiCache 已创建：{resource.id}")

            resource.status = ResourceStatus.ACTIVE
            return True

        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                print("  ⚠️  权限不足，需要人类介入")
                return await self._guide_human_creation(resource)
            raise

    async def _guide_human_creation(self, resource: CloudResource) -> bool:
        """引导人类创建资源"""
        print(f"\n{'='*60}")
        print(f"⚠️  需要人类介入：{resource.name} ({resource.type})")
        print(f"{'='*60}")

        guide = self._get_creation_guide(resource)

        print("\n📋 资源信息:")
        print(f"  名称：{resource.name}")
        print(f"  类型：{resource.type}")
        print(f"  提供商：{resource.provider}")

        print("\n📖 创建方式（选择一种）:")

        # 方式 1: 控制台
        if 'console_url' in guide:
            print("\n  【方式 1】AWS 控制台:")
            print(f"  1. 访问：{guide['console_url']}")
            print(f"  2. 点击\"创建{resource.type.replace('_', ' ').title()}\"")
            print("  3. 配置参数:")
            for param, value in guide.get('parameters', {}).items():
                print(f"     - {param}: {value}")
            print("  4. 点击\"创建\"")

        # 方式 2: CLI
        if 'cli_command' in guide:
            print("\n  【方式 2】AWS CLI:")
            print("  运行以下命令:")
            print("  ```bash")
            print(f"  {guide['cli_command']}")
            print("  ```")

        # 方式 3: Terraform
        if 'terraform_code' in guide:
            print("\n  【方式 3】Terraform:")
            print("  添加以下配置到 main.tf:")
            print("  ```hcl")
            print(f"  {guide['terraform_code']}")
            print("  ```")
            print("  然后运行：terraform apply")

        print(f"\n{'='*60}")

        # 等待确认
        while True:
            choice = input("\n请选择操作:\n  [1] 我已创建资源\n  [2] 显示指南\n  [3] 跳过此资源\n  选择：")

            if choice == '1':
                # 验证资源是否已创建
                status = await self.check_resource(resource)
                if status == ResourceStatus.ACTIVE:
                    print("  ✓ 资源验证成功！")
                    return True
                else:
                    print("  ⚠️  未找到资源，请确认创建成功")
            elif choice == '2':
                print(f"\n{guide.get('console_url', '')}")
            elif choice == '3':
                print(f"  ⚠️  跳过资源：{resource.name}")
                resource.status = ResourceStatus.NOT_EXISTS
                return False

    def _get_creation_guide(self, resource: CloudResource) -> dict[str, Any]:
        """获取创建指南"""
        guides = {
            'vpc': {
                'console_url': 'https://console.aws.amazon.com/vpc/home?#VPCs:',
                'cli_command': f'aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications "ResourceType=vpc,Tags=[{{Key=Name,Value={resource.name}}}]"',
                'terraform_code': f'''
resource "aws_vpc" "{resource.name}" {{
  cidr_block = "10.0.0.0/16"
  tags = {{
    Name = "{resource.name}"
  }}
}}''',
                'parameters': {
                    'CIDR': '10.0.0.0/16',
                    '名称': resource.name
                }
            },
            'ecs_cluster': {
                'console_url': 'https://console.aws.amazon.com/ecs/home?#/clusters',
                'cli_command': f'aws ecs create-cluster --cluster-name {resource.name}',
                'terraform_code': f'''
resource "aws_ecs_cluster" "{resource.name}" {{
  name = "{resource.name}"
}}''',
                'parameters': {
                    '集群名称': resource.name
                }
            },
            'elasticache': {
                'console_url': 'https://console.aws.amazon.com/elasticache/home?#redis:',
                'cli_command': f'aws elasticache create-cache-cluster --cache-cluster-id {resource.name} --engine redis --cache-node-type cache.t3.micro --num-cache-nodes 1',
                'terraform_code': f'''
resource "aws_elasticache_cluster" "{resource.name}" {{
  cluster_id           = "{resource.name}"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
}}''',
                'parameters': {
                    '引擎': 'Redis',
                    '节点类型': 'cache.t3.micro',
                    '节点数': '1'
                }
            }
        }

        return guides.get(resource.type, {
            'console_url': 'https://console.aws.amazon.com/',
            'cli_command': f'# 请访问 AWS 控制台创建 {resource.name}',
            'terraform_code': f'# 请手动配置 {resource.name}',
            'parameters': {}
        })


class CloudSelfBootstrap:
    """
    云 Self-Bootstrap 管理器（增强版）

    支持自动开通资源和引导人类授权
    """

    def __init__(self, provider: str, region: str = "", config: dict[str, Any] = None):
        self.provider = provider
        self.region = region
        self.config = config or {}
        self.provisioner = CloudResourceProvisioner(provider, region)
        self._resources: list[CloudResource] = []
        self._plan: Optional[BootstrapPlan] = None

    def define_resources(self) -> list[CloudResource]:
        """定义所需资源"""
        resources = []

        if self.provider == "aws":
            resources = [
                CloudResource(
                    name="intentos-vpc",
                    type="vpc",
                    provider="aws",
                    config={"cidr": "10.0.0.0/16"},
                    auto_create=True,
                    human_guide={
                        "description": "VPC 是隔离的云资源网络环境"
                    }
                ),
                CloudResource(
                    name="intentos-ecs-cluster",
                    type="ecs_cluster",
                    provider="aws",
                    dependencies=["intentos-vpc"],
                    auto_create=True
                ),
                CloudResource(
                    name="intentos-redis",
                    type="elasticache",
                    provider="aws",
                    config={"node_type": "cache.t3.micro"},
                    dependencies=["intentos-vpc"],
                    auto_create=True
                ),
                CloudResource(
                    name="intentos-alb",
                    type="alb",
                    provider="aws",
                    dependencies=["intentos-vpc"],
                    auto_create=True
                ),
                CloudResource(
                    name="intentos-secrets",
                    type="secretsmanager",
                    provider="aws",
                    dependencies=[],
                    auto_create=True
                ),
            ]

        elif self.provider == "docker":
            resources = [
                CloudResource(
                    name="intentos-network",
                    type="docker_network",
                    provider="docker",
                    auto_create=True
                ),
                CloudResource(
                    name="intentos-redis",
                    type="docker_container",
                    provider="docker",
                    config={"image": "redis:7-alpine"},
                    auto_create=True
                ),
            ]

        self._resources = resources
        return resources

    async def plan(self) -> BootstrapPlan:
        """创建 Bootstrap 计划"""
        print("\n📋 创建 Bootstrap 计划...")

        plan = BootstrapPlan()

        for resource in self._resources:
            print(f"\n  检查资源：{resource.name} ({resource.type})")
            status = await self.provisioner.check_resource(resource)
            resource.status = status

            if status == ResourceStatus.ACTIVE:
                print(f"    ✓ 已存在：{resource.id}")
            elif status == ResourceStatus.NEEDS_AUTH:
                print("    ⚠️  需要授权")
                plan.requires_human_action = True
            elif status == ResourceStatus.NOT_EXISTS:
                if resource.auto_create:
                    print("    → 将自动创建")
                else:
                    print("    ⚠️  需要人类创建")
                    plan.requires_human_action = True

            plan.resources.append(resource)

        # 估算成本
        plan.estimated_cost = self._estimate_cost()

        self._plan = plan
        return plan

    def _estimate_cost(self) -> dict[str, float]:
        """估算成本"""
        costs = {
            'vpc': 0.0,  # VPC 免费
            'ecs_cluster': 0.0,  # ECS 本身免费
            'elasticache': 15.0,  # cache.t3.micro ~$15/月
            'alb': 22.0,  # ALB ~$22/月
            'secretsmanager': 1.0,  # Secrets Manager ~$1/月
        }

        total = sum(costs.get(r.type, 0) for r in self._resources if r.status != ResourceStatus.ACTIVE)

        return {
            'monthly': total,
            'yearly': total * 12,
            'breakdown': costs
        }

    async def execute(self) -> bool:
        """执行 Bootstrap"""
        if not self._plan:
            await self.plan()

        print(f"\n{'='*60}")
        print("🚀 开始执行 Cloud Self-Bootstrap")
        print(f"{'='*60}")

        if self._plan.requires_human_action:
            print("\n⚠️  需要人类介入")
            print("以下资源需要您的授权或手动创建:\n")

            for resource in self._plan.resources:
                if resource.status in [ResourceStatus.NEEDS_AUTH, ResourceStatus.NOT_EXISTS]:
                    print(f"  - {resource.name} ({resource.type})")

            print("\n您可以选择:")
            print("  [1] 授权自动创建（需要云凭证）")
            print("  [2] 手动创建资源（显示指南）")
            print("  [3] 跳过所有资源（仅使用已有资源）")

            choice = input("\n请选择：")

            if choice == '1':
                # 引导配置凭证
                await self._guide_credential_setup()
            elif choice == '2':
                # 显示手动创建指南
                await self._show_manual_guides()
            elif choice == '3':
                # 跳过
                print("⚠️  将仅使用已有资源")

        # 创建资源
        created = 0
        skipped = 0
        failed = 0

        for resource in self._plan.resources:
            if resource.status == ResourceStatus.ACTIVE:
                continue

            print(f"\n  处理资源：{resource.name}...")

            try:
                success = await self.provisioner.create_resource(resource)
                if success:
                    created += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  ❌ 创建失败：{e}")
                failed += 1

        print(f"\n{'='*60}")
        print("Bootstrap 完成!")
        print(f"  创建：{created}")
        print(f"  跳过：{skipped}")
        print(f"  失败：{failed}")
        print(f"{'='*60}")

        return failed == 0

    async def _guide_credential_setup(self) -> None:
        """引导凭证配置"""
        print("\n📖 配置云凭证")

        if self.provider == "aws":
            print("""
请访问 AWS 控制台获取凭证:

1. 登录 AWS 控制台：https://console.aws.amazon.com/
2. 访问 IAM 服务：https://console.aws.amazon.com/iam/
3. 创建新用户或使用现有用户
4. 创建 Access Key
5. 设置环境变量:

   export AWS_ACCESS_KEY_ID="your_access_key"
   export AWS_SECRET_ACCESS_KEY="your_secret_key"

或者创建 ~/.aws/credentials 文件:

   [default]
   aws_access_key_id = your_access_key
   aws_secret_access_key = your_secret_key
""")

            # 等待用户配置
            input("\n配置完成后按回车继续...")

            # 重新检查凭证
            self.provisioner._check_credentials()

            if not self.provisioner.credentials_valid:
                print("⚠️  凭证配置失败，请检查")

    async def _show_manual_guides(self) -> None:
        """显示手动创建指南"""
        print("\n📖 手动创建资源指南")

        for resource in self._plan.resources:
            if resource.status != ResourceStatus.ACTIVE:
                guide = self.provisioner._get_creation_guide(resource)
                print(f"\n{'='*60}")
                print(f"资源：{resource.name} ({resource.type})")
                print(f"{'='*60}")
                print(f"控制台：{guide.get('console_url', 'N/A')}")
                print("\nCLI 命令:")
                print(f"  {guide.get('cli_command', 'N/A')}")
                print("\nTerraform:")
                print(f"  {guide.get('terraform_code', 'N/A')}")

        input("\n查看完成后按回车继续...")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='IntentOS Cloud Self-Bootstrap')
    parser.add_argument('--provider', choices=['aws', 'gcp', 'azure', 'docker'], default='docker')
    parser.add_argument('--region', default='')
    parser.add_argument('--auto', action='store_true', help='自动模式（无需交互）')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("  IntentOS Cloud Self-Bootstrap")
    print("  云资源自动开通与人类引导授权")
    print(f"{'='*60}\n")

    bootstrap = CloudSelfBootstrap(
        provider=args.provider,
        region=args.region
    )

    # 定义资源
    resources = bootstrap.define_resources()
    print(f"📦 定义了 {len(resources)} 个资源")

    # 创建计划
    plan = await bootstrap.plan()

    print("\n📊 资源状态:")
    for resource in plan.resources:
        icon = "✓" if resource.status == ResourceStatus.ACTIVE else "○"
        print(f"  {icon} {resource.name} ({resource.type}): {resource.status.value}")

    print("\n💰 预估成本:")
    print(f"  月度：${plan.estimated_cost['monthly']:.2f}")
    print(f"  年度：${plan.estimated_cost['yearly']:.2f}")

    if args.auto:
        # 自动模式
        success = await bootstrap.execute()
    else:
        # 交互模式
        choice = input("\n是否继续执行？(y/n): ")
        if choice.lower() == 'y':
            success = await bootstrap.execute()
        else:
            print("Bootstrap 已取消")
            success = False

    return 0 if success else 1


if __name__ == '__main__':
    exit(asyncio.run(main()))
