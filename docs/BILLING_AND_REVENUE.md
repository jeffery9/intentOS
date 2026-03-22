# AI Native App 计费与收益分成

> **按量计费 · 自动分成 · 透明账单**

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**状态**: Release Candidate

---

## 一、概述

### 1.1 计费模式

IntentOS 支持多种计费模式，适应不同应用场景：

| 模式 | 适用场景 | 计费单位 | 示例 |
|------|---------|---------|------|
| **按量计费** | 临时使用 | CPU 秒/Token/次 | $0.10/分钟 |
| **订阅制** | 高频使用 | 月/年 | $9.99/月 |
| **配额制** | 中等频率 | 配额包 | $49.99/500 次 |
| **免费 + 增值** | 获客 | 免费额度 + 付费 | 免费 10 次/月 |
| **阶梯定价** | 大量使用 | 用量阶梯 | 1-100 次$0.1, 101+ 次$0.08 |

### 1.2 收益分成

```
用户支付 $100
    ↓
┌─────────────────────────────────────┐
│           收益分配                   │
├─────────────────────────────────────┤
│  开发者：$80 (80%)                  │
│  平台：$15 (15%)                    │
│  推荐者：$5 (5%)                    │
└─────────────────────────────────────┘
```

### 1.3 计费流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 用户使用 App                                                  │
│    "分析销售数据"                                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 计量系统记录用量                                              │
│    - CPU 时间：90 秒                                             │
│    - Token 使用：2500                                           │
│    - 执行时长：1.5 分钟                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 计费引擎计算费用                                              │
│    - 执行时长：1.5 × $0.10 = $0.15                              │
│    - Token 使用：2.5 × $0.02 = $0.05                            │
│    - 总计：$0.20                                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. 从用户钱包扣费                                                │
│    - 用户余额：$100.00 → $99.80                                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. 收益分成                                                      │
│    - 开发者：$0.16 (80%)                                        │
│    - 平台：$0.03 (15%)                                          │
│    - 推荐者：$0.01 (5%)                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、计费模式详解

### 2.1 按量计费 (Pay-per-Use)

最常用的计费模式，按实际使用量计费。

```yaml
# pricing/rules.yaml
pricing:
  model: "pay_per_use"
  currency: "USD"
  
  # 计费维度
  dimensions:
    - name: "execution_time"
      unit: "minute"
      rate: 0.10
      
    - name: "llm_tokens"
      unit: "1000_tokens"
      rate: 0.02
      
    - name: "api_calls"
      unit: "call"
      rate: 0.01

  # 最低收费
  minimum_charge: 0.01
  
  # 免费额度
  free_quota:
    execution_time: 1  # 1 分钟免费
    requests: 1        # 首次免费
```

**适用场景**:
- 临时使用
- 使用频率不稳定
- 尝试新应用

**优点**:
- 灵活，用多少付多少
- 无预付压力

**缺点**:
- 单价相对较高
- 费用不可预测

---

### 2.2 订阅制 (Subscription)

按月或年付费，享受无限或配额内免费使用。

```yaml
pricing:
  model: "subscription"
  currency: "USD"
  
  plans:
    free:
      price: 0
      billing_cycle: "monthly"
      included_quota:
        cpu_seconds: 600
        tokens: 10000
        api_calls: 10
      overage_rates:
        cpu_second: 0.002
        token_1k: 0.03
        api_call: 0.02
      features:
        - "基础功能"
        - "社区支持"

    pro:
      price: 9.99
      billing_cycle: "monthly"
      included_quota:
        cpu_seconds: 36000
        tokens: 500000
        api_calls: 1000
      overage_rates:
        cpu_second: 0.001
        token_1k: 0.02
        api_call: 0.01
      features:
        - "全部功能"
        - "优先支持"
        - "API 访问"

    enterprise:
      price: 99.99
      billing_cycle: "monthly"
      included_quota:
        cpu_seconds: 360000
        tokens: 5000000
        api_calls: 10000
      overage_rates:
        cpu_second: 0.0005
        token_1k: 0.01
        api_call: 0.005
      features:
        - "全部功能"
        - "专属支持"
        - "SLA 保障"
        - "定制开发"
```

**适用场景**:
- 高频使用
- 费用可预测
- 需要稳定服务

**优点**:
- 单价更低
- 费用可预测
- 享受更多功能

**缺点**:
- 需要预付
- 不用也收费

---

### 2.3 配额制 (Quota)

购买配额包，在有效期内使用。

```yaml
pricing:
  model: "quota"
  currency: "USD"
  
  packages:
    starter:
      price: 9.99
      quota:
        requests: 100
      validity_days: 30
      
    standard:
      price: 39.99
      quota:
        requests: 500
      validity_days: 90
      
    professional:
      price: 149.99
      quota:
        requests: 2000
      validity_days: 365
```

**适用场景**:
- 中等频率使用
- 希望批量购买优惠

---

### 2.4 阶梯定价 (Tiered Pricing)

用量越大，单价越低。

```yaml
pricing:
  model: "tiered"
  currency: "USD"
  
  tiers:
    - range: "1-100"
      rate: 0.10
      description: "基础档"
      
    - range: "101-1000"
      rate: 0.08
      description: "标准档"
      
    - range: "1001-10000"
      rate: 0.05
      description: "专业档"
      
    - range: "10001+"
      rate: 0.03
      description: "企业档"
```

**计算示例**:
```
使用 1500 次:
- 前 100 次：100 × $0.10 = $10.00
- 101-1000 次：900 × $0.08 = $72.00
- 1001-1500 次：500 × $0.05 = $25.00
- 总计：$107.00
```

---

## 三、收益分成

### 3.1 分成比例

```yaml
# 默认分成比例
revenue_share:
  developer: 0.80    # 开发者 80%
  platform: 0.15     # 平台 15%
  referrer: 0.05     # 推荐者 5%
```

### 3.2 分成计算

```python
from intentos.agent import RevenueShare

# 配置分成比例
share_config = {
    "developer": 0.80,
    "platform": 0.15,
    "referrer": 0.05,
}

# 计算分成
revenue = RevenueShare(share_config)

total_revenue = 1000  # 总收入$1000

developer_earnings = revenue.calculate_developer_share(total_revenue)
platform_earnings = revenue.calculate_platform_share(total_revenue)
referrer_earnings = revenue.calculate_referrer_share(total_revenue)

print(f"开发者收益：${developer_earnings}")  # $800
print(f"平台收益：${platform_earnings}")      # $150
print(f"推荐者收益：${referrer_earnings}")    # $50
```

### 3.3 推荐者机制

```python
# 用户通过推荐链接注册
referrer_id = "user_alice"
new_user_id = "user_bob"

# 记录推荐关系
revenue.add_referral(
    referrer_id=referrer_id,
    referred_id=new_user_id,
    referred_at=datetime.now()
)

# 新用户消费时，推荐者获得分成
# 新用户消费 $100
# 推荐者获得：$100 × 5% = $5
```

### 3.4 开发者收益提现

```python
# 查询可提现余额
developer_id = "dev_alice"
balance = revenue.get_developer_balance(developer_id)
print(f"可提现余额：${balance}")

# 申请提现
withdrawal = revenue.request_withdrawal(
    developer_id=developer_id,
    amount=balance,
    method="bank_transfer",  # bank_transfer/crypto/paypal
    account="bank_account_123"
)

# 提现处理
# T+1 到账
```

---

## 四、账单管理

### 4.1 账单生成

```python
from intentos.agent import BillingEngine

billing = BillingEngine()

# 生成月度账单
invoice = billing.generate_invoice(
    user_id="user_alice",
    period="2026-03",
    items=[
        {"description": "数据分析 App 使用", "amount": 15.50},
        {"description": "代码生成 App 使用", "amount": 8.20},
        {"description": "文档总结 App 使用", "amount": 3.00},
    ],
    subtotal=26.70,
    discount=0,
    total=26.70
)

# 发送账单
billing.send_invoice(invoice_id=invoice.id, email="alice@example.com")
```

### 4.2 账单查询

```bash
# API 查询账单
GET /v1/invoices?user_id=user_alice&period=2026-03

# 返回
{
    "invoices": [
        {
            "invoice_id": "inv_202603_alice",
            "period": "2026-03",
            "created_at": "2026-03-31T23:59:59Z",
            "status": "paid",
            "items": [
                {"description": "数据分析 App 使用", "amount": 15.50},
                {"description": "代码生成 App 使用", "amount": 8.20}
            ],
            "total": 26.70,
            "paid_at": "2026-03-31T10:00:00Z"
        }
    ]
}
```

### 4.3 用量查询

```bash
# API 查询用量
GET /v1/usage?user_id=user_alice&period=2026-03

# 返回
{
    "user_id": "user_alice",
    "period": "2026-03",
    "usage": {
        "cpu_seconds": 4500,
        "tokens": 125000,
        "api_calls": 350,
        "execution_minutes": 75
    },
    "cost_breakdown": {
        "cpu_time": 4.50,
        "tokens": 2.50,
        "api_calls": 3.50,
        "execution_time": 7.50
    },
    "total": 18.00
}
```

---

## 五、数字钱包

### 5.1 钱包管理

```python
from intentos.agent import DigitalWallet

# 创建钱包
wallet = DigitalWallet(user_id="user_alice")

# 查询余额
balance = await wallet.get_balance()
print(f"余额：${balance}")

# 充值
await wallet.recharge(
    amount=100,
    method="crypto",  # crypto/stripe/alipay/wechat
    token="USDT"
)

# 支付
payment = await wallet.pay(
    amount=0.20,
    description="数据分析 App 使用"
)

# 查询交易历史
transactions = await wallet.get_transaction_history(limit=50)
for tx in transactions:
    print(f"{tx.type}: ${tx.amount} - {tx.description}")
```

### 5.2 自动充值

```python
# 设置自动充值
await wallet.setup_auto_recharge(
    threshold=10,      # 余额低于$10 时触发
    amount=50,         # 充值$50
    method="crypto"
)

# 当余额低于阈值时自动充值
```

### 5.3 余额告警

```python
# 设置余额告警
await wallet.setup_balance_alert(
    threshold=20,     # 余额低于$20 时告警
    notification="email"  # email/sms/push
)
```

---

## 六、计费示例

### 6.1 数据分析 App

```yaml
# App 计费配置
app_id: "data_analyst"

pricing:
  model: "pay_per_use"
  dimensions:
    - name: "execution_time"
      unit: "minute"
      rate: 0.10
    - name: "data_volume"
      unit: "1000_rows"
      rate: 0.05

# 使用示例
# 分析 5000 行数据，耗时 3 分钟
# 费用计算:
# - 执行时长：3 × $0.10 = $0.30
# - 数据量：5 × $0.05 = $0.25
# - 总计：$0.55
```

### 6.2 代码生成 App

```yaml
app_id: "code_generator"

pricing:
  model: "pay_per_token"
  price_per_1k_tokens: 0.02

# 使用示例
# 生成 5000 tokens 代码
# 费用计算:
# - 5 × $0.02 = $0.10
```

### 6.3 智能客服 Bot

```yaml
app_id: "customer_service_bot"

pricing:
  model: "pay_per_call"
  price_per_call: 0.01
  
  # 阶梯定价
  tiers:
    - range: "1-1000"
      rate: 0.01
    - range: "1001-10000"
      rate: 0.008
    - range: "10001+"
      rate: 0.005

# 使用示例
# 1500 次对话
# 费用计算:
# - 前 1000 次：1000 × $0.01 = $10.00
# - 后 500 次：500 × $0.008 = $4.00
# - 总计：$14.00
```

---

## 七、开发者收益

### 7.1 收益仪表板

```python
# 查询开发者收益
developer_id = "dev_alice"

# 本月收益
monthly_earnings = revenue.get_developer_earnings(
    developer_id=developer_id,
    period="2026-03"
)

print(f"本月收益：${monthly_earnings['total']}")
print(f"分成明细:")
for app, earnings in monthly_earnings['by_app'].items():
    print(f"  - {app}: ${earnings}")

# 收益趋势
trend = revenue.get_earnings_trend(
    developer_id=developer_id,
    months=6
)
```

### 7.2 收益优化建议

```python
# 获取优化建议
suggestions = revenue.get_optimization_suggestions(developer_id)

for suggestion in suggestions:
    print(f"建议：{suggestion['type']}")
    print(f"  说明：{suggestion['description']}")
    print(f"  预期提升：{suggestion['expected_increase']}%")

# 示例输出:
# 建议：调整定价
#   说明：您的应用使用量稳定，建议采用订阅制提高收益
#   预期提升：30%
```

---

## 八、最佳实践

### 8.1 定价策略

```yaml
# ✅ 正确：透明定价
pricing:
  model: "pay_per_use"
  dimensions:
    - name: "execution_time"
      unit: "minute"
      rate: 0.10
  minimum_charge: 0.01
  free_quota:
    execution_time: 1  # 1 分钟免费

# ❌ 错误：隐藏费用
pricing:
  model: "custom"
  # 没有明确说明如何计费
```

### 8.2 免费额度

```yaml
# ✅ 正确：提供合理免费额度
free_quota:
  execution_time: 1      # 1 分钟免费
  requests: 10           # 10 次免费请求
  tokens: 10000          # 10K tokens 免费

# 目的：让用户试用，建立信任
```

### 8.3 账单清晰

```yaml
# ✅ 正确：详细账单
invoice:
  items:
    - description: "数据分析 App - 2026-03-15 10:30"
      amount: 0.15
      details:
        execution_time: "1.5 分钟"
        tokens: 2500
    - description: "代码生成 App - 2026-03-15 14:20"
      amount: 0.10
      details:
        tokens: 5000

# ❌ 错误：模糊账单
invoice:
  items:
    - description: "App 使用费"
      amount: 26.70
```

---

## 九、参考文档

| 文档 | 说明 |
|------|------|
| [AI Native App 概述](./AI_NATIVE_APP.md) | 核心概念、架构概览 |
| [即时生成架构](./JIT_GENERATION_ARCHITECTURE.md) | App 即时生成、身份感知 |
| [租户架构](./TENANT_ARCHITECTURE.md) | 多租户隔离、资源配置 |

---

**文档版本**: 1.0  
**创建日期**: 2026-03-21  
**最后更新**: 2026-03-21  
**状态**: Release Candidate
