# -*- coding: utf-8 -*-
"""
IntentOS Economic Decision Engine

This module serves as the economic brain of IntentOS, monitoring revenue
and costs, and making autonomous decisions regarding resource allocation
and self-reproduction based on predefined economic rules.
"""

import logging
import os
from typing import Any, Dict

import yaml

from intentos.agent.payment_integration import PaymentIntegration
from intentos.bootstrap.self_reproduction import (
    SelfReproduction,
)
from intentos.distributed.cost_monitor import CostMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EconomicEngine:
    """
    Manages the economic decisions for IntentOS, including fund allocation
    and triggering self-reproduction.
    """

    def __init__(self, cost_monitor: CostMonitor, payment_integration: PaymentIntegration, soul_manifest_path: str = 'intentos/config/soul_manifest.yaml'):
        """
        Initializes the EconomicEngine with necessary dependencies.

        :param cost_monitor: An instance of CostMonitor for cost data.
        :param payment_integration: An instance of PaymentIntegration for revenue data.
        :param soul_manifest_path: Path to the soul manifest YAML file.
        """
        self.cost_monitor = cost_monitor
        self.payment_integration = payment_integration
        self.self_reproduction = SelfReproduction()
        self.operational_fund = 0.0
        self.reproduction_fund = 0.0
        self.monthly_revenue = 0.0
        self.monthly_cost = 0.0
        self.buffer_months = 3
        self.soul_manifest: Dict[str, Any] = {}
        self._load_soul_manifest(soul_manifest_path)

        logging.info("EconomicEngine initialized.")

    def _load_soul_manifest(self, manifest_path: str) -> None:
        """
        Loads the IntentOS soul manifest from the YAML file.
        """
        if not os.path.exists(manifest_path):
            logging.warning(f"Soul Manifest file not found at: {manifest_path}. EconomicEngine will operate without explicit ethics.")
            return
        try:
            with open(manifest_path, 'r') as f:
                self.soul_manifest = yaml.safe_load(f)
            logging.info("Soul manifest loaded successfully by EconomicEngine.")
        except yaml.YAMLError as e:
            logging.error(f"Error parsing EconomicEngine's Soul Manifest YAML: {e}")
            # Continue without manifest rather than crashing

    async def _check_ethical_guidelines(self, proposed_action: Dict[str, Any]) -> bool:
        """
        Simulates checking a proposed action against IntentOS's ethical guidelines.

        :param proposed_action: Details of the action to be checked (e.g., {'type': 'clone', 'cost': 50.0}).
        :return: True if the action adheres to ethics, False otherwise.
        """
        ethics = self.soul_manifest.get('ethics', [])
        action_type = proposed_action.get('type')
        action_cost = proposed_action.get('cost', 0.0)

        logging.info(f"Checking ethical guidelines for {action_type} action (cost: ${action_cost})...")

        for ethic in ethics:
            if ethic['principle'] == "Respect resource limits.":
                # Simple check: if cost is too high (e.g., >$100 for any single action),
                # and it's not explicitly approved, it might violate the principle.
                if action_cost > 100.0 and action_type == 'clone': # Example threshold
                    logging.warning(f"Ethical concern: Proposed {action_type} action cost (${action_cost}) exceeds typical resource limits. Violates '{ethic['principle']}'.")
                    return False
            if ethic['principle'] == "Prioritize long-term viability over short-term gains.":
                # Example: If reproduction fund is barely above cost, and economic health is fragile,
                # it might violate long-term viability.
                # This is a placeholder for more complex logic.
                if action_type == 'clone' and self.reproduction_fund < (action_cost * 1.5):
                     logging.warning(f"Ethical concern: Cloning with insufficient buffer. Might violate '{ethic['principle']}'.")
                     return False

        logging.info("Proposed action adheres to ethical guidelines.")
        return True

    async def _update_financial_data(self) -> None:
        """
        Updates the latest revenue and cost data.
        """
        self.monthly_revenue = 100.00
        self.monthly_cost = self.cost_monitor.get_plan_cost_estimate({"actions": []})['total_monthly_cost']

        logging.info(f"Financial data updated. Revenue: ${self.monthly_revenue}, Cost: ${self.monthly_cost}")

    async def run_economic_cycle(self) -> Dict[str, Any]:
        """
        Runs one cycle of economic decision-making.

        :return: A dictionary of decisions made (e.g., funds allocated, reproduction triggered).
        """
        await self._update_financial_data()
        decisions: Dict[str, Any] = {}

        net_profit = self.monthly_revenue - self.monthly_cost
        logging.info(f"Net Profit: ${net_profit}")

        required_operational_fund = self.monthly_cost * self.buffer_months
        if self.operational_fund < required_operational_fund:
            funding_needed = required_operational_fund - self.operational_fund
            allocated_to_ops = min(net_profit, funding_needed)
            self.operational_fund += allocated_to_ops
            net_profit -= allocated_to_ops
            decisions['operational_fund_allocated'] = allocated_to_ops
            logging.info(f"Allocated ${allocated_to_ops} to operational fund. Current: ${self.operational_fund}")

        if net_profit > 0:
            allocation_to_reproduction = net_profit * 0.5
            self.reproduction_fund += allocation_to_reproduction
            net_profit -= allocation_to_reproduction
            decisions['reproduction_fund_allocated'] = allocation_to_reproduction
            logging.info(f"Allocated ${allocation_to_reproduction} to reproduction fund. Current: ${self.reproduction_fund}")

        cloning_cost_estimate = 50.0
        if self.reproduction_fund >= cloning_cost_estimate:
            # --- Ethical Guardrail Check ---
            proposed_action = {'type': 'clone', 'cost': cloning_cost_estimate}
            if not await self._check_ethical_guidelines(proposed_action):
                logging.warning("Cloning action blocked due to ethical guideline violation.")
                decisions['reproduction_blocked_ethics'] = True
                return decisions
            # --- End Ethical Guardrail Check ---

            logging.info("Reproduction fund sufficient for cloning. Initiating clone action.")
            await self.self_reproduction.discover_self()
            clone_plan = await self.self_reproduction.clone_self(target_region="us-west-2")
            decisions['reproduction_triggered'] = {
                "action": "clone",
                "details": f"Cloning initiated: Plan ID {clone_plan.id}, Status: {clone_plan.status.value}"
            }
            self.reproduction_fund -= cloning_cost_estimate
            logging.info(f"Reproduction triggered: Cloning initiated! Plan ID: {clone_plan.id}")
        else:
            logging.info(f"Reproduction fund (${self.reproduction_fund}) not yet sufficient for cloning (requires ${cloning_cost_estimate}).")

        return decisions
