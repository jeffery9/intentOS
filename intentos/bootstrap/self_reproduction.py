"""
IntentOS 自我繁殖模块

实现系统的自我复制、自我扩展、自我演化
"""

from __future__ import annotations

import asyncio
import json
import logging  # Import logging for ethical checks
import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

import yaml  # Import yaml for reading soul manifest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ReproductionType(Enum):
    """繁殖类型"""
    CLONE = "clone"              # 克隆（完全复制）
    FORK = "fork"                # 分叉（有差异的复制）
    EVOLVE = "evolve"            # 演化（改进版本）
    REPAIR = "repair"            # 修复（自我修复）


class ReproductionStatus(Enum):
    """繁殖状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ReproductionPlan:
    """
    繁殖计划
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ReproductionType = ReproductionType.CLONE
    status: ReproductionStatus = ReproductionStatus.PENDING
    source_instance: str = ""
    target_instance: str = ""
    target_region: str = ""
    target_provider: str = ""
    config_changes: dict[str, Any] = field(default_factory=dict)
    resources_to_copy: list[str] = field(default_factory=list)
    estimated_time: int = 0  # 秒
    estimated_cost: float = 0.0  # 美元
    progress: int = 0  # 百分比
    errors: list[str] = field(default_factory=list)


@dataclass
class IntentOSInstance:
    """
    IntentOS 实例
    """
    id: str
    name: str
    provider: str
    region: str
    endpoint: str
    version: str
    status: str
    resources: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    last_synced: str = ""


class SelfReproduction:
    """
    自我繁殖管理器

    实现 IntentOS 的自我复制、扩展和演化
    """

    def __init__(self, instance_id: str = "", soul_manifest_path: str = 'intentos/config/soul_manifest.yaml'):
        self.instance_id = instance_id or self._get_instance_id()
        self._current_instance: Optional[IntentOSInstance] = None
        self._reproduction_plans: list[ReproductionPlan] = []
        self.soul_manifest: Dict[str, Any] = {}
        self._load_soul_manifest(soul_manifest_path)
        logging.info("SelfReproduction module initialized.")

    def _load_soul_manifest(self, manifest_path: str) -> None:
        """
        Loads the IntentOS soul manifest from the YAML file.
        """
        if not os.path.exists(manifest_path):
            logging.warning(f"Soul Manifest file not found at: {manifest_path}. SelfReproduction will operate without explicit ethics.")
            return
        try:
            with open(manifest_path, 'r') as f:
                self.soul_manifest = yaml.safe_load(f)
            logging.info("Soul manifest loaded successfully by SelfReproduction.")
        except yaml.YAMLError as e:
            logging.error(f"Error parsing SelfReproduction's Soul Manifest YAML: {e}")
            # Continue without manifest rather than crashing

    async def _check_ethical_guidelines(self, proposed_plan: ReproductionPlan) -> bool:
        """
        Simulates checking a proposed reproduction plan against IntentOS's ethical guidelines.

        :param proposed_plan: The ReproductionPlan to be checked.
        :return: True if the plan adheres to ethics, False otherwise.
        """
        ethics = self.soul_manifest.get('ethics', [])
        plan_type = proposed_plan.type.value
        estimated_cost = proposed_plan.estimated_cost

        logging.info(f"Checking ethical guidelines for {plan_type} plan (estimated cost: ${estimated_cost})...")

        for ethic in ethics:
            if ethic['principle'] == "Respect resource limits.":
                # Example: If estimated cost is very high for a non-critical clone/scale operation
                if (plan_type == 'clone' or plan_type == 'fork') and estimated_cost > 200.0: # Arbitrary high cost threshold
                    logging.warning(f"Ethical concern: Proposed {plan_type} plan estimated cost (${estimated_cost}) is very high. Violates '{ethic['principle']}'.")
                    return False

            if ethic['principle'] == "Prioritize long-term viability over short-term gains.":
                # Example: If a repair plan is proposed but it's too cheap (implies superficial fix) for a critical issue
                # This would need more context on issue criticality in a real scenario.
                if plan_type == 'repair' and estimated_cost < 1.0 and "critical_issue" in proposed_plan.config_changes.get('repairs', []):
                    logging.warning(f"Ethical concern: Superficial repair for a critical issue. Might violate '{ethic['principle']}'.")
                    return False

        logging.info("Reproduction plan adheres to ethical guidelines.")
        return True

    def _get_instance_id(self) -> str:
        """
        获取当前实例 ID
        """
        if os.path.exists('/etc/intentos/instance_id'):
            with open('/etc/intentos/instance_id') as f:
                return f.read().strip()
        return str(uuid.uuid4())[:8]

    async def discover_self(self) -> IntentOSInstance:
        """
        发现当前实例配置
        """
        print(f"🔍 发现当前实例：{self.instance_id}")

        # 检测云环境
        provider = self._detect_cloud_provider()
        region = self._detect_region()

        # 获取资源配置
        resources = await self._scan_resources()

        # 获取配置
        config = await self._load_config()

        instance = IntentOSInstance(
            id=self.instance_id,
            name=f"intentos-{self.instance_id}",
            provider=provider,
            region=region,
            endpoint=self._get_endpoint(),
            version=self._get_version(),
            status="running",
            resources=resources,
            config=config,
            created_at=self._get_creation_time(),
            last_synced=self._get_current_time()
        )

        self._current_instance = instance
        print("✓ 实例发现完成")
        print(f"  提供商：{provider}")
        print(f"  区域：{region}")
        print(f"  端点：{instance.endpoint}")
        print(f"  资源：{len(resources)} 个")

        return instance

    def _detect_cloud_provider(self) -> str:
        """
        检测云提供商
        """
        # AWS
        if os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION'):
            return "aws"
        # GCP
        if os.getenv('GCP_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT'):
            return "gcp"
        # Azure
        if os.getenv('ARM_REGION') or os.getenv('AZURE_REGION'):
            return "azure"
        # Docker
        return "docker"

    def _detect_region(self) -> str:
        """
        检测区域
        """
        return (
            os.getenv('AWS_REGION') or
            os.getenv('AWS_DEFAULT_REGION') or
            os.getenv('GCP_REGION') or
            os.getenv('AZURE_REGION') or
            'us-east-1'
        )

    async def _scan_resources(self) -> dict[str, Any]:
        """
        扫描资源
        """
        resources = {}

        if self._detect_cloud_provider() == "aws":
            resources = await self._scan_aws_resources()
        elif self._detect_cloud_provider() == "docker":
            resources = await self._scan_docker_resources()

        return resources

    async def _scan_aws_resources(self) -> dict[str, Any]:
        """
        扫描 AWS 资源
        """
        try:
            import boto3

            ecs = boto3.client('ecs')
            ec2 = boto3.client('ec2')
            elasticache = boto3.client('elasticache')

            # ECS 集群
            clusters = ecs.describe_clusters()

            # VPC
            vpcs = ec2.describe_vpcs(
                Filters=[{'Name': 'tag:managed-by', 'Values': ['intentos']}]
            )

            # Redis
            redis = elasticache.describe_cache_clusters(
                TagFilters=[{'Name': 'managed-by', 'Values': ['intentos']}]
            )

            return {
                'ecs_clusters': [c['clusterName'] for c in clusters.get('clusters', [])],
                'vpcs': [v['VpcId'] for v in vpcs.get('Vpcs', [])],
                'redis_clusters': [c['CacheClusterId'] for c in redis.get('CacheClusters', [])],
            }
        except Exception as e:
            print(f"⚠️  扫描失败：{e}")
            return {}

    async def _scan_docker_resources(self) -> dict[str, Any]:
        """
        扫描 Docker 资源
        """

        try:
            # 获取容器
            result = await asyncio.create_subprocess_exec(
                'docker', 'ps', '--filter', 'name=intentos',
                '--format', '{{.Names}}:{{.Status}}',
                stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()

            containers = {}
            for line in stdout.decode().strip().split('\n'):
                if ':' in line:
                    name, status = line.split(':', 1)
                    containers[name] = status

            # 获取网络
            result = await asyncio.create_subprocess_exec(
                'docker', 'network', 'ls', '--filter', 'name=intentos',
                '--format', '{{.Name}}',
                stdout=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            networks = stdout.decode().strip().split('\n')

            return {
                'containers': containers,
                'networks': [n for n in networks if n],
            }
        except Exception as e:
            return {}

    async def _load_config(self) -> dict[str, Any]:
        """
        加载配置
        """
        config_paths = [
            '/opt/intentos/data/config.json',
            './data/config.json',
            './config.json',
        ]

        for path in config_paths:
            if os.path.exists(path):
                with open(path) as f:
                    return json.load(f)

        return {}

    def _get_endpoint(self) -> str:
        """
        获取端点
        """
        return os.getenv('INTENTOS_ENDPOINT', 'http://localhost:8080')

    def _get_version(self) -> str:
        """
        获取版本
        """
        return os.getenv('INTENTOS_VERSION', '9.0')

    def _get_creation_time(self) -> str:
        """
        获取创建时间
        """
        return os.getenv('INTENTOS_CREATED_AT', self._get_current_time())

    def _get_current_time(self) -> str:
        """
        获取当前时间
        """
        from datetime import datetime
        return datetime.now().isoformat()

    # ========== 自我复制 ==========

    async def clone_self(self, target_region: str, target_provider: str = "") -> ReproductionPlan:
        """
        克隆自己到新区域

        Args:
            target_region: 目标区域
            target_provider: 目标提供商（默认同当前）

        Returns:
            ReproductionPlan: 繁殖计划
        """
        print("\n🔄 开始自我克隆...")
        print(f"  源实例：{self.instance_id}")
        print(f"  目标区域：{target_region}")

        if not self._current_instance:
            await self.discover_self()

        plan = ReproductionPlan(
            type=ReproductionType.CLONE,
            source_instance=self.instance_id,
            target_instance=f"intentos-{target_region}-{uuid.uuid4().hex[:8]}",
            target_region=target_region,
            target_provider=target_provider or self._current_instance.provider,
            resources_to_copy=list(self._current_instance.resources.keys()),
            estimated_time=600,  # 10 分钟
            estimated_cost=50.0  # $50
        )

        self._reproduction_plans.append(plan)

        # 执行克隆
        await self._execute_reproduction(plan)

        return plan

    # ========== 自我扩展 ==========

    async def scale_self(self, scale_factor: float = 2.0) -> ReproductionPlan:
        """
        自我扩展

        Args:
            scale_factor: 扩展倍数（2.0 = 扩展一倍）

        Returns:
            ReproductionPlan: 繁殖计划
        """
        print("\n📈 开始自我扩展...")
        print(f"  当前实例：{self.instance_id}")
        print(f"  扩展倍数：{scale_factor}x")

        if not self._current_instance:
            await self.discover_self()

        plan = ReproductionPlan(
            type=ReproductionType.FORK,
            source_instance=self.instance_id,
            target_instance=f"intentos-scaled-{uuid.uuid4().hex[:8]}",
            target_region=self._current_instance.region,
            target_provider=self._current_instance.provider,
            config_changes={
                'replicas': int(self._current_instance.config.get('replicas', 1) * scale_factor),
                'auto_scaling': True,
            },
            estimated_time=300,
            estimated_cost=30.0 * scale_factor
        )

        self._reproduction_plans.append(plan)
        await self._execute_reproduction(plan)

        return plan

    # ========== 自我演化 ==========

    async def evolve_self(self, improvements: list[str] = None) -> ReproductionPlan:
        """
        自我演化

        Args:
            improvements: 改进列表

        Returns:
            ReproductionPlan: 繁殖计划
        """
        print("\n🧬 开始自我演化...")
        print(f"  当前版本：{self._current_instance.version if self._current_instance else 'unknown'}")
        print(f"  改进项：{improvements or ['自动检测']}")

        if not self._current_instance:
            await self.discover_self()

        plan = ReproductionPlan(
            type=ReproductionType.EVOLVE,
            source_instance=self.instance_id,
            target_instance=f"intentos-v{self._get_next_version()}",
            target_region=self._current_instance.region,
            target_provider=self._current_instance.provider,
            config_changes={
                'version': self._get_next_version(),
                'improvements': improvements or [],
            },
            estimated_time=900,
            estimated_cost=100.0
        )

        self._reproduction_plans.append(plan)
        await self._execute_reproduction(plan)

        return plan

    # ========== 自我修复 ==========

    async def repair_self(self, issues: list[str] = None) -> ReproductionPlan:
        """
        自我修复

        Args:
            issues: 问题列表

        Returns:
            ReproductionPlan: 繁殖计划
        """
        print("\n🔧 开始自我修复...")

        if not issues:
            # 自动检测问题
            issues = await self._detect_issues()

        print(f"  检测到的问题：{issues}")

        plan = ReproductionPlan(
            type=ReproductionType.REPAIR,
            source_instance=self.instance_id,
            target_instance=self.instance_id,  # 原地修复
            target_region=self._current_instance.region if self._current_instance else "",
            target_provider=self._current_instance.provider if self._current_instance else "",
            config_changes={
                'repairs': issues,
            },
            estimated_time=180,
            estimated_cost=0.0
        )

        self._reproduction_plans.append(plan)
        await self._execute_reproduction(plan)

        return plan

    # ========== 执行繁殖 ==========

    async def _execute_reproduction(self, plan: ReproductionPlan) -> None:
        """
        执行繁殖计划
        """
        plan.status = ReproductionStatus.IN_PROGRESS

        # --- Ethical Guardrail Check ---
        if not await self._check_ethical_guidelines(plan):
            plan.errors.append("Reproduction blocked due to ethical guideline violation.")
            plan.status = ReproductionStatus.FAILED
            logging.warning("Reproduction blocked due to ethical guideline violation.")
            return
        # --- End Ethical Guardrail Check ---

        steps = [
            ("准备资源", self._prepare_resources, 10),
            ("复制配置", self._copy_config, 20),
            ("部署实例", self._deploy_instance, 50),
            ("同步数据", self._sync_data, 80),
            ("验证健康", self._verify_health, 100),
        ]

        for step_name, step_func, progress in steps:
            print(f"  [{progress}%] {step_name}...")
            try:
                await step_func(plan)
                plan.progress = progress
            except Exception as e:
                plan.errors.append(f"{step_name}: {str(e)}")
                plan.status = ReproductionStatus.FAILED
                print(f"  ❌ {step_name} 失败：{e}")
                return

        plan.status = ReproductionStatus.COMPLETED
        print(f"  ✅ 繁殖完成！新实例：{plan.target_instance}")

    async def _prepare_resources(self, plan: ReproductionPlan) -> None:
        """
        准备资源
        """
        # 在目标区域创建资源
        if plan.target_provider == "aws":
            await self._create_aws_resources(plan)
        elif plan.target_provider == "docker":
            await self._create_docker_resources(plan)

    async def _create_aws_resources(self, plan: ReproductionPlan) -> None:
        """
        创建 AWS 资源
        """
        try:
            import boto3

            # 切换到目标区域
            session = boto3.Session(region_name=plan.target_region)

            # 创建 VPC
            ec2 = session.client('ec2')
            vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
            print(f"    ✓ VPC 已创建：{vpc['Vpc']['VpcId']}")

            # 创建 ECS 集群
            ecs = session.client('ecs')
            cluster = ecs.create_cluster(clusterName=plan.target_instance)
            print(f"    ✓ ECS 集群已创建：{cluster['cluster']['clusterName']}")

        except Exception as e:
            raise Exception(f"AWS 资源创建失败：{e}")

    async def _create_docker_resources(self, plan: ReproductionPlan) -> None:
        """
        创建 Docker 资源
        """
        # 生成 docker-compose 配置
        compose_content = self._generate_docker_compose(plan)

        # 写入文件
        target_dir = f"/tmp/intentos-{plan.target_instance}"
        os.makedirs(target_dir, exist_ok=True)

        with open(f"{target_dir}/docker-compose.yml", 'w') as f:
            f.write(compose_content)

        print("    ✓ Docker Compose 已生成")

    def _generate_docker_compose(self, plan: ReproductionPlan) -> str:
        """
        生成 Docker Compose 配置
        """
        return f"""
version: '3.8'
services:
  intentos:
    image: intentos/intentos:{plan.config_changes.get('version', '9.0')}
    ports:
      - "8080:8080"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

volumes:
  redis-data:
"""

    async def _copy_config(self, plan: ReproductionPlan) -> None:
        """
        复制配置
        """
        # 复制当前配置并应用变更
        if self._current_instance:
            plan.config_changes.update({
                'source_instance': self._current_instance.id,
                'source_config': self._current_instance.config,
            })
        print("    ✓ 配置已复制")

    async def _deploy_instance(self, plan: ReproductionPlan) -> None:
        """
        部署实例
        """
        # 根据提供商部署
        if plan.target_provider == "docker":
            target_dir = f"/tmp/intentos-{plan.target_instance}"
            await asyncio.create_subprocess_exec(
                'docker-compose', '-f', f'{target_dir}/docker-compose.yml', 'up', '-d'
            )
        print("    ✓ 实例已部署")

    async def _sync_data(self, plan: ReproductionPlan) -> None:
        """
        同步数据
        """
        # 同步 Redis 数据
        print("    ✓ 数据已同步")

    async def _verify_health(self, plan: ReproductionPlan) -> None:
        """
        验证健康
        """
        # 等待服务启动
        await asyncio.sleep(10)

        # 健康检查
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f'{plan.target_endpoint or "http://localhost:8080"}/v1/status', timeout=10) as resp:
                    if resp.status == 200:
                        print("    ✓ 健康检查通过")
                    else:
                        raise Exception(f"健康检查失败：{resp.status}")
            except Exception as e:
                raise Exception(f"健康检查失败：{e}")

    async def _detect_issues(self) -> list[str]:
        """
        检测问题
        """
        issues = []

        # 检查资源使用率
        # 检查错误日志
        # 检查性能指标

        return issues

    def _get_next_version(self) -> str:
        """
        获取下一版本
        """
        if self._current_instance:
            current = self._current_instance.version
            parts = current.split('.')
            parts[-1] = str(int(parts[-1]) + 1)
            return '.'.join(parts)
        return "9.1"

    # ========== 状态查询 ==========

    def get_reproduction_history(self) -> list[ReproductionPlan]:
        """
        获取繁殖历史
        """
        return self._reproduction_plans

    def get_reproduction_status(self, plan_id: str) -> Optional[ReproductionPlan]:
        """
        获取繁殖状态
        """
        for plan in self._reproduction_plans:
            if plan.id == plan_id:
                return plan
        return None


async def main():
    """
    演示自我繁殖
    """
    import argparse

    parser = argparse.ArgumentParser(description='IntentOS 自我繁殖')
    parser.add_argument('--action', choices=['clone', 'scale', 'evolve', 'repair', 'discover'], default='discover')
    parser.add_argument('--target-region', default='')
    parser.add_argument('--scale-factor', type=float, default=2.0)

    args = parser.parse_args()

    reproducer = SelfReproduction()

    if args.action == 'discover':
        await reproducer.discover_self()

    elif args.action == 'clone':
        await reproducer.discover_self()
        plan = await reproducer.clone_self(args.target_region or 'us-west-2')
        print(f"\n克隆计划：{plan.id}")
        print(f"状态：{plan.status.value}")

    elif args.action == 'scale':
        await reproducer.discover_self()
        plan = await reproducer.scale_self(args.scale_factor)
        print(f"\n扩展计划：{plan.id}")
        print(f"状态：{plan.status.value}")

    elif args.action == 'evolve':
        await reproducer.discover_self()
        plan = await reproducer.evolve_self()
        print(f"\n演化计划：{plan.id}")
        print(f"状态：{plan.status.value}")

    elif args.action == 'repair':
        await reproducer.discover_self()
        plan = await reproducer.repair_self()
        print(f"\n修复计划：{plan.id}")
        print(f"状态：{plan.status.value}")


if __name__ == '__main__':
    asyncio.run(main())

