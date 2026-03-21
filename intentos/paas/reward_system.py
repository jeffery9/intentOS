# -*- coding: utf-8 -*-
"""
IntentOS Incentive & Reward System

This module manages a simplified, off-chain ledger for awarding credits
to users and agents for valuable contributions to the IntentOS ecosystem.
These credits can eventually be used to pay for IntentOS services.
"""

import logging
from typing import Dict, Any, List, Optional

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

    def get_contribution_types(self) -> Dict[str, float]:
        """
        Returns a dictionary of all recognized contribution types and their base credit awards.
        """
        return self.contribution_types
