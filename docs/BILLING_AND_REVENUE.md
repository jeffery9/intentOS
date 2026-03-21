# IntentOS 计费与商业化规范 (v2.1 融合版)

> **Gas 驱动结算 · 自动收益分配 · 平台自进化储备**

---

## 一、 经济原力：Gas 价值模型

在 IntentOS 中，所有的计费均基于 **Gas** 这一统一资源单位。

### 1.1 Gas 消耗维度
- **推理 Gas**: LLM Token 消耗。
- **逻辑 Gas**: 语义操作码（Opcode）执行步数。
- **IO Gas**: 物理能力（如调用 API、执行 Shell）的频率。

### 1.2 自动结算流程
1. **进程运行**: 每个内核进程（PID）在执行过程中向所属租户账户扣除 Gas。
2. **实例汇总**: `AppMarketplace` 通过监控 App 实例的 `active_pids`，定期汇总总消耗。
3. **商业转化**: 消耗的 Gas 按照市场定价（`Gas Price`）转化为法币或信用额度。

---

## 二、 计费模式详解

### 2.1 按量计费
```yaml
# pricing/rules.yaml
pricing:
  model: "pay_per_use"
  currency: "USD"
  dimensions:
    - name: "gas"
      unit: "1000_gas"
      rate: 0.02
```

### 2.2 订阅制
```yaml
pricing:
  model: "subscription"
  plans:
    pro:
      price: 9.99
      billing_cycle: "monthly"
      included_quota:
        total_gas_limit: 500000
```

---

## 三、 收益分配机制

| 参与者 | 分成比例 (默认) | 描述 |
| :--- | :--- | :--- |
| **开发者** | 80% | 奖励高质量、高效率的语义程序编写。 |
| **平台留存** | 15% | 注入 `platform_reserve`，用于物理节点扩容。 |
| **能力贡献者** | 5% | 奖励物理 IO 驱动（如高性能 GPU 节点）的提供方。 |

---

## 四、 平台自我成长回路

PaaS 层通过 `platform_reserve` 实现系统的自我增殖：
1. **收益累积**: 每笔交易的 15% 进入储备金。
2. **负载预警**: `PaaSAutoScaler` 检测到集群平均负载 > 70%。
3. **物理增殖**: 储备金自动支付云服务费用，启动新的 `RuntimeAgent` 节点并加入分布式网络。

---

**文档版本**: 2.1 (融合版)  
**最后更新**: 2026-03-21  
**状态**: **v2.1 生产级标准**
