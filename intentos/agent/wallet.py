# -*- coding: utf-8 -*-
"""
IntentOS Digital Wallet Module

数字钱包模块，负责管理用户的数字资产和支付。
支持加密货币和法币，集成主流支付网关。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


logger: logging.Logger = logging.getLogger(__name__)


class CurrencyType(Enum):
    """货币类型"""
    CRYPTO = "crypto"      # 加密货币
    FIAT = "fiat"          # 法币


class PaymentMethod(Enum):
    """支付方式"""
    META_MASK = "metamask"       # MetaMask
    IM_TOKEN = "imtoken"         # ImToken
    TOKEN_POCKET = "tokenpocket" # TokenPocket
    STRIPE = "stripe"            # Stripe
    ALIPAY = "alipay"            # 支付宝
    WECHAT = "wechat"            # 微信
    BANK_TRANSFER = "bank"       # 银行转账


class TransactionType(Enum):
    """交易类型"""
    RECHARGE = "recharge"        # 充值
    PAYMENT = "payment"          # 支付
    REFUND = "refund"            # 退款
    WITHDRAW = "withdraw"        # 提现
    TRANSFER = "transfer"        # 转账
    SUBSCRIPTION = "subscription" # 订阅扣费


class TransactionStatus(Enum):
    """交易状态"""
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


@dataclass
class Transaction:
    """交易记录"""
    id: str
    user_id: str
    type: TransactionType
    amount: float
    currency: str
    status: TransactionStatus
    timestamp: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    tx_hash: Optional[str] = None  # 区块链交易哈希
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "tx_hash": self.tx_hash,
            "metadata": self.metadata,
        }


@dataclass
class WalletBalance:
    """钱包余额"""
    user_id: str
    balances: dict[str, float] = field(default_factory=dict)  # currency -> amount
    last_updated: datetime = field(default_factory=datetime.now)

    def get_balance(self, currency: str) -> float:
        """获取指定货币余额"""
        return self.balances.get(currency, 0.0)

    def add_balance(self, currency: str, amount: float) -> None:
        """增加余额"""
        if currency not in self.balances:
            self.balances[currency] = 0.0
        self.balances[currency] += amount
        self.last_updated = datetime.now()

    def subtract_balance(self, currency: str, amount: float) -> bool:
        """减少余额"""
        if self.get_balance(currency) < amount:
            return False
        self.balances[currency] -= amount
        self.last_updated = datetime.now()
        return True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "balances": self.balances,
            "last_updated": self.last_updated.isoformat(),
        }


class DigitalWallet:
    """
    数字钱包

    管理用户的数字资产，支持多种货币和支付方式。
    """

    def __init__(self, user_id: str) -> None:
        self.user_id: str = user_id
        self.balance: WalletBalance = WalletBalance(user_id=user_id)
        self.transactions: list[Transaction] = []
        self._next_tx_id: int = 0
        logger.info(f"数字钱包初始化完成：user={user_id}")

    def _generate_tx_id(self) -> str:
        """生成交易 ID"""
        self._next_tx_id += 1
        return f"txn_{self.user_id}_{self._next_tx_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    async def get_balance(self, currency: str = "USD") -> float:
        """获取余额"""
        return self.balance.get_balance(currency)

    async def recharge(
        self,
        amount: float,
        currency: str = "USD",
        method: PaymentMethod = PaymentMethod.STRIPE,
        tx_hash: Optional[str] = None
    ) -> Transaction:
        """充值"""
        tx = Transaction(
            id=self._generate_tx_id(),
            user_id=self.user_id,
            type=TransactionType.RECHARGE,
            amount=amount,
            currency=currency,
            status=TransactionStatus.PROCESSING,
            description=f"充值 ${amount}",
            payment_method=method,
            tx_hash=tx_hash,
        )
        self.transactions.append(tx)
        logger.info(f"充值处理中：{tx.id}, amount={amount} {currency}")

        # 模拟处理
        try:
            # 在实际实现中，这里会调用支付网关 API
            await self._process_recharge(tx)

            tx.status = TransactionStatus.COMPLETED
            self.balance.add_balance(currency, amount)
            logger.info(f"充值完成：{tx.id}")
        except Exception as e:
            tx.status = TransactionStatus.FAILED
            tx.metadata["error"] = str(e)
            logger.error(f"充值失败：{tx.id}, error={e}")
            raise

        return tx

    async def pay(
        self,
        amount: float,
        currency: str = "USD",
        description: Optional[str] = None,
        auto_recharge: bool = False
    ) -> Transaction:
        """支付"""
        # 检查余额
        if self.balance.get_balance(currency) < amount:
            if auto_recharge:
                # 自动充值
                recharge_amount = amount - self.balance.get_balance(currency) + 10  # 多充$10
                await self.recharge(recharge_amount, currency)
            else:
                raise ValueError(f"余额不足：需要{amount} {currency}, 可用{self.balance.get_balance(currency)} {currency}")

        tx = Transaction(
            id=self._generate_tx_id(),
            user_id=self.user_id,
            type=TransactionType.PAYMENT,
            amount=amount,
            currency=currency,
            status=TransactionStatus.PROCESSING,
            description=description or f"支付 ${amount}",
        )
        self.transactions.append(tx)
        logger.info(f"支付处理中：{tx.id}, amount={amount} {currency}")

        try:
            tx.status = TransactionStatus.COMPLETED
            self.balance.subtract_balance(currency, amount)
            logger.info(f"支付完成：{tx.id}")
        except Exception as e:
            tx.status = TransactionStatus.FAILED
            tx.metadata["error"] = str(e)
            logger.error(f"支付失败：{tx.id}, error={e}")
            raise

        return tx

    async def withdraw(
        self,
        amount: float,
        currency: str = "USD",
        method: PaymentMethod = PaymentMethod.BANK_TRANSFER,
        destination: Optional[str] = None
    ) -> Transaction:
        """提现"""
        if self.balance.get_balance(currency) < amount:
            raise ValueError(f"余额不足：需要{amount} {currency}, 可用{self.balance.get_balance(currency)} {currency}")

        tx = Transaction(
            id=self._generate_tx_id(),
            user_id=self.user_id,
            type=TransactionType.WITHDRAW,
            amount=amount,
            currency=currency,
            status=TransactionStatus.PROCESSING,
            description=f"提现 ${amount}",
            payment_method=method,
            metadata={"destination": destination} if destination else {},
        )
        self.transactions.append(tx)
        logger.info(f"提现处理中：{tx.id}, amount={amount} {currency}")

        try:
            tx.status = TransactionStatus.COMPLETED
            self.balance.subtract_balance(currency, amount)
            logger.info(f"提现完成：{tx.id}")
        except Exception as e:
            tx.status = TransactionStatus.FAILED
            tx.metadata["error"] = str(e)
            logger.error(f"提现失败：{tx.id}, error={e}")
            raise

        return tx

    async def get_transaction_history(
        self,
        limit: int = 50,
        tx_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None
    ) -> list[Transaction]:
        """获取交易历史"""
        transactions = self.transactions

        if tx_type:
            transactions = [t for t in transactions if t.type == tx_type]
        if status:
            transactions = [t for t in transactions if t.status == status]

        # 按时间倒序
        transactions.sort(key=lambda t: t.timestamp, reverse=True)

        return transactions[:limit]

    def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        """获取单笔交易"""
        for tx in self.transactions:
            if tx.id == tx_id:
                return tx
        return None

    async def _process_recharge(self, tx: Transaction) -> None:
        """处理充值（子类可重写）"""
        # 模拟处理延迟
        import asyncio
        await asyncio.sleep(0.1)


class PaymentGateway:
    """
    支付网关

    集成主流支付提供商，处理实际的支付操作。
    """

    def __init__(self) -> None:
        self.providers: dict[str, Any] = {}
        self.api_keys: dict[str, str] = {}
        logger.info("支付网关初始化完成")

    def register_provider(
        self,
        name: str,
        provider: Any,
        api_key: Optional[str] = None
    ) -> None:
        """注册支付提供商"""
        self.providers[name] = provider
        if api_key:
            self.api_keys[name] = api_key
        logger.info(f"注册支付提供商：{name}")

    async def connect_metamask(self, rpc_url: Optional[str] = None) -> bool:
        """连接 MetaMask"""
        logger.info("连接 MetaMask...")
        # 实际实现会连接 Web3  provider
        self.providers["metamask"] = {"type": "web3", "rpc_url": rpc_url or "https://mainnet.infura.io"}
        logger.info("MetaMask 连接成功")
        return True

    async def connect_stripe(self, api_key: str) -> bool:
        """连接 Stripe"""
        logger.info("连接 Stripe...")
        # 实际实现会初始化 Stripe SDK
        self.api_keys["stripe"] = api_key
        self.providers["stripe"] = {"type": "stripe"}
        logger.info("Stripe 连接成功")
        return True

    async def connect_alipay(self, app_id: str, private_key: str) -> bool:
        """连接支付宝"""
        logger.info("连接支付宝...")
        self.providers["alipay"] = {
            "type": "alipay",
            "app_id": app_id,
            "private_key": private_key,
        }
        logger.info("支付宝连接成功")
        return True

    async def process_payment(
        self,
        wallet: DigitalWallet,
        amount: float,
        currency: str,
        method: PaymentMethod
    ) -> Transaction:
        """处理支付"""
        if method.value not in self.providers:
            raise ValueError(f"支付方式未配置：{method.value}")

        # 实际实现会调用对应支付网关的 API
        tx = await wallet.pay(amount, currency, description=f"通过{method.value}支付")
        tx.payment_method = method
        return tx

    async def process_recharge(
        self,
        wallet: DigitalWallet,
        amount: float,
        currency: str,
        method: PaymentMethod
    ) -> Transaction:
        """处理充值"""
        if method.value not in self.providers:
            raise ValueError(f"支付方式未配置：{method.value}")

        # 实际实现会调用对应支付网关的 API
        tx = await wallet.recharge(amount, currency, method)
        return tx


class SubscriptionManager:
    """
    订阅管理器

    管理用户的订阅服务和自动扣费。
    """

    def __init__(self) -> None:
        self.subscriptions: dict[str, dict[str, Any]] = {}
        logger.info("订阅管理器初始化完成")

    async def create_subscription(
        self,
        user_id: str,
        plan_id: str,
        amount: float,
        currency: str = "USD",
        billing_cycle: str = "monthly",
        auto_renew: bool = True
    ) -> dict[str, Any]:
        """创建订阅"""
        sub_id = f"sub_{user_id}_{plan_id}_{datetime.now().strftime('%Y%m%d')}"

        subscription = {
            "id": sub_id,
            "user_id": user_id,
            "plan_id": plan_id,
            "amount": amount,
            "currency": currency,
            "billing_cycle": billing_cycle,
            "auto_renew": auto_renew,
            "status": "active",
            "start_date": datetime.now(),
            "next_bill_date": self._calculate_next_bill_date(billing_cycle),
        }

        self.subscriptions[sub_id] = subscription
        logger.info(f"创建订阅：{sub_id}, plan={plan_id}, amount={amount}")

        return subscription

    async def cancel_subscription(self, sub_id: str) -> bool:
        """取消订阅"""
        if sub_id not in self.subscriptions:
            return False

        self.subscriptions[sub_id]["status"] = "cancelled"
        logger.info(f"取消订阅：{sub_id}")
        return True

    async def process_auto_charge(
        self,
        wallet: DigitalWallet,
        sub_id: str
    ) -> Optional[Transaction]:
        """处理自动扣费"""
        if sub_id not in self.subscriptions:
            return None

        sub = self.subscriptions[sub_id]
        if sub["status"] != "active":
            return None

        try:
            tx = await wallet.pay(
                amount=sub["amount"],
                currency=sub["currency"],
                description=f"订阅扣费：{sub['plan_id']}"
            )
            tx.type = TransactionType.SUBSCRIPTION
            tx.metadata["subscription_id"] = sub_id

            # 更新下次账单日期
            sub["next_bill_date"] = self._calculate_next_bill_date(sub["billing_cycle"])
            logger.info(f"自动扣费成功：{sub_id}")

            return tx
        except Exception as e:
            logger.error(f"自动扣费失败：{sub_id}, error={e}")
            return None

    def _calculate_next_bill_date(self, billing_cycle: str) -> datetime:
        """计算下次账单日期"""
        from datetime import timedelta

        now = datetime.now()

        if billing_cycle == "daily":
            return now + timedelta(days=1)
        elif billing_cycle == "weekly":
            return now + timedelta(weeks=1)
        elif billing_cycle == "monthly":
            return now.replace(month=now.month + 1) if now.month < 12 else now.replace(year=now.year + 1, month=1)
        elif billing_cycle == "yearly":
            return now.replace(year=now.year + 1)
        else:
            return now + timedelta(days=30)

    def get_user_subscriptions(self, user_id: str) -> list[dict[str, Any]]:
        """获取用户订阅"""
        return [
            sub for sub in self.subscriptions.values()
            if sub["user_id"] == user_id
        ]


# 全局支付网关实例
_global_payment_gateway: Optional[PaymentGateway] = None
_global_subscription_manager: Optional[SubscriptionManager] = None


def get_payment_gateway() -> PaymentGateway:
    """获取全局支付网关"""
    global _global_payment_gateway
    if _global_payment_gateway is None:
        _global_payment_gateway = PaymentGateway()
    return _global_payment_gateway


def get_subscription_manager() -> SubscriptionManager:
    """获取全局订阅管理器"""
    global _global_subscription_manager
    if _global_subscription_manager is None:
        _global_subscription_manager = SubscriptionManager()
    return _global_subscription_manager


def reset_payment_services() -> None:
    """重置支付服务"""
    global _global_payment_gateway, _global_subscription_manager
    _global_payment_gateway = None
    _global_subscription_manager = None
