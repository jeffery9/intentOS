# -*- coding: utf-8 -*-
"""
IntentOS Incentive & Reward System

This module manages a simplified, off-chain ledger for awarding credits
to users and agents for valuable contributions to the IntentOS ecosystem.
These credits can eventually be used to pay for IntentOS services.
"""

import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RewardSystem:
    """
    Manages the distribution and tracking of credits/tokens within IntentOS.
    """

    def __init__(self, initial_contribution_types: Optional[Dict[str, float]] = None):
        self.ledger: Dict[str, float] = {}
        self.contribution_types: Dict[str, float] = initial_contribution_types or {
            "code_contribution": 10.0, # Credits per contribution
            "doc_contribution": 5.0,
            "skill_development": 20.0,
            "user_referral": 15.0, # Credits per successful referral
            "bug_report": 2.0,
            "community_moderation": 7.0,
            "tutorial_creation": 12.0,
            "feature_suggestion": 3.0,
        }
        logging.info("RewardSystem initialized.")

    def award_credits(self, entity_id: str, contribution_type: str, quantity: float = 1.0) -> float:
        """
        Awards credits to an entity for a specific contribution type.

        :param entity_id: The ID of the entity (user, agent) to reward.
        :param contribution_type: The type of contribution (e.g., 'code_contribution').
        :param quantity: The multiplier for the base credit value (e.g., number of referrals).
        :return: The new credit balance of the entity.
        :raises ValueError: If the contribution type is not recognized.
        """
        if contribution_type not in self.contribution_types:
            logging.error(f"Unknown contribution type: {contribution_type}")
            raise ValueError(f"Unknown contribution type: {contribution_type}")

        base_credits = self.contribution_types[contribution_type]
        credits_to_award = base_credits * quantity

        self.ledger[entity_id] = self.ledger.get(entity_id, 0.0) + credits_to_award
        logging.info(f"Awarded {credits_to_award} credits to {entity_id} for {contribution_type}. New balance: {self.ledger[entity_id]}")
        return self.ledger[entity_id]

    def get_balance(self, entity_id: str) -> float:
        """
        Retrieves the credit balance for a given entity.

        :param entity_id: The ID of the entity.
        :return: The current credit balance.
        """
        return self.ledger.get(entity_id, 0.0)

    def spend_credits(self, entity_id: str, amount: float) -> float:
        """
        Simulates spending credits by an entity.

        :param entity_id: The ID of the entity.
        :param amount: The amount of credits to spend.
        :return: The new credit balance of the entity.
        :raises ValueError: If the entity does not have sufficient credits.
        """
        if self.ledger.get(entity_id, 0.0) < amount:
            logging.error(f"Entity {entity_id} has insufficient credits to spend {amount}.")
            raise ValueError(f"Insufficient credits for {entity_id}")

        self.ledger[entity_id] -= amount
        logging.info(f"Entity {entity_id} spent {amount} credits. New balance: {self.ledger[entity_id]}")
        return self.ledger[entity_id]

    def process_gas_settlement(
        self,
        user_id: str,
        app_id: str,
        developer_id: str,
        gas_used: int,
        gas_price: float = 0.001 # 每 Gas 对应的信用额度
    ) -> dict[str, float]:
        """
        Gas 结算逻辑 (Economic Pipeline)

        第一性原理：OS 产生的每一单位物理消耗（Gas）都应在经济层面被补偿。
        """
        total_cost = gas_used * gas_price

        # 1. 扣除用户信用额度
        try:
            self.spend_credits(user_id, total_cost)
        except ValueError:
            # 如果额度不足，此处仅记录日志，实际生产应在 OS 层拦截
            logging.error(f"User {user_id} has insufficient credits to pay for gas: {total_cost}")

        # 2. 分成计算
        developer_share = total_cost * 0.8  # 80% 归开发者
        platform_share = total_cost * 0.2   # 20% 留存平台用于成长

        # 3. 分发收益
        self.ledger[developer_id] = self.ledger.get(developer_id, 0.0) + developer_share
        self.ledger["platform_reserve"] = self.ledger.get("platform_reserve", 0.0) + platform_share

        logging.info(f"Gas Settlement: App {app_id} used {gas_used} gas. User {user_id} paid {total_cost:.4f}. Developer {developer_id} earned {developer_share:.4f}.")

        return {
            "total_cost": total_cost,
            "developer_earned": developer_share,
            "platform_retained": platform_share
        }

    def get_platform_reserve(self) -> float:
        """获取平台留存资金，用于 OS 自动扩容/研发"""
        return self.ledger.get("platform_reserve", 0.0)
