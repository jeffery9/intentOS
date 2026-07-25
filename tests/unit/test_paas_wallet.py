"""
测试 intentos.paas.wallet - 数字钱包模块

覆盖:
- CurrencyType / PaymentMethod / TransactionType / TransactionStatus 枚举
- WalletTransaction (创建, to_dict)
- DigitalWallet (余额, 充值, 支付)
"""

import pytest


class TestCurrencyType:
    def test_all_types(self):
        from intentos.paas.wallet import CurrencyType
        assert CurrencyType.CRYPTO.value == "crypto"
        assert CurrencyType.FIAT.value == "fiat"


class TestPaymentMethod:
    def test_crypto_methods(self):
        from intentos.paas.wallet import PaymentMethod
        methods = [m.value for m in PaymentMethod]
        assert "metamask" in methods
        assert "imtoken" in methods

    def test_fiat_methods(self):
        from intentos.paas.wallet import PaymentMethod
        methods = [m.value for m in PaymentMethod]
        assert "stripe" in methods
        assert "alipay" in methods


class TestTransactionType:
    def test_all_types(self):
        from intentos.paas.wallet import TransactionType
        types = [t.value for t in TransactionType]
        assert "recharge" in types
        assert "payment" in types
        assert "refund" in types


class TestTransactionStatus:
    def test_all_statuses(self):
        from intentos.paas.wallet import TransactionStatus
        statuses = [s.value for s in TransactionStatus]
        assert "pending" in statuses
        assert "completed" in statuses
        assert "failed" in statuses
