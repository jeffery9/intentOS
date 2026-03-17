# -*- coding: utf-8 -*-
"""
IntentOS Self-Reflection and Intent Alignment Module

This module enables IntentOS to periodically evaluate its own state
(economic, social, operational) against its defined core mission and values
(the 'soul manifest'). It identifies deviations and can trigger corrective actions.
"""

import yaml
import logging
from typing import Dict, Any, List, Optional
import os
import asyncio

# Import IntentOS modules for corrective actions
from intentos.distributed.economic_engine import EconomicEngine
from intentos.bootstrap.self_reproduction import SelfReproduction
from intentos.agent.social_agent import SocialAgent
from intentos.distributed.cost_monitor import CostMonitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SelfReflection:
    """
    Enables IntentOS to reflect on its performance and align with its core intent.
    """

    def __init__(self, manifest_path: str = 'intentos/config/soul_manifest.yaml',
                 economic_engine: Optional[EconomicEngine] = None,
                 self_reproduction: Optional[SelfReproduction] = None,
                 social_agent: Optional[SocialAgent] = None,
                 cost_monitor: Optional[CostMonitor] = None):
        """
        Initializes the SelfReflection module by loading the soul manifest.

        :param manifest_path: Path to the soul manifest YAML file.
        :param economic_engine: Instance of EconomicEngine for economic actions.
        :param self_reproduction: Instance of SelfReproduction for reproduction actions.
        :param social_agent: Instance of SocialAgent for social outreach.
        :param cost_monitor: Instance of CostMonitor for cost optimization.
        """
        self.manifest_path = manifest_path
        self.soul_manifest: Dict[str, Any] = {}
        self._load_soul_manifest()

        self.economic_engine = economic_engine
        self.self_reproduction = self_reproduction
        self.social_agent = social_agent
        self.cost_monitor = cost_monitor

        logging.info("SelfReflection module initialized.")

    def _load_soul_manifest(self) -> None:
        """
        Loads the IntentOS soul manifest from the YAML file.
        """
        if not os.path.exists(self.manifest_path):
            logging.error(f"Soul Manifest file not found at: {self.manifest_path}")
            raise FileNotFoundError(f"Soul Manifest file not found: {self.manifest_path}")
        try:
            with open(self.manifest_path, 'r') as f:
                self.soul_manifest = yaml.safe_load(f)
            logging.info("Soul manifest loaded successfully.")
        except yaml.YAMLError as e:
            logging.error(f"Error parsing Soul Manifest YAML: {e}")
            raise

    def evaluate_current_state(self, current_state: Dict[str, Any]) -> List[str]:
        """
        Evaluates the current state of IntentOS against its core mission and values.

        :param current_state: A dictionary representing the current operational state
                              (e.g., {'economic_health': 'good', 'social_sentiment': 'neutral', 'growth_rate': 'low'}).
        :return: A list of identified deviations or areas for improvement.
        """
        logging.info("Evaluating current state against Soul Manifest...")
        deviations = []

        mission_statements = self.soul_manifest.get('mission', [])
        values = self.soul_manifest.get('values', [])
        ethics = self.soul_manifest.get('ethics', [])

        # --- Mission Alignment Checks (Simplified) ---
        if "Self-preservation and sustained growth through autonomous operation." in mission_statements:
            if current_state.get('economic_health') == 'poor':
                deviations.append("Economic health is poor, risking self-preservation. Requires action.")
            if current_state.get('growth_rate') == 'low':
                deviations.append("Growth rate is low, impacting sustained growth. Requires attention.")

        # --- Values Alignment Checks (Simplified) ---
        for value in values:
            if value['name'] == "Sustainability" and current_state.get('resource_consumption') == 'high':
                deviations.append("High resource consumption detected, violating Sustainability value.")
            if value['name'] == "Collaboration" and current_state.get('social_sentiment') == 'negative':
                deviations.append("Negative social sentiment, impacting Collaboration value.")

        # --- Ethical Guideline Checks (Simplified) ---
        for ethic in ethics:
            if ethic['principle'] == "Respect resource limits." and current_state.get('cost_over_budget') is True:
                deviations.append("Cost over budget, violating 'Respect resource limits' ethical principle.")

        if not deviations:
            logging.info("Current state is well-aligned with the Soul Manifest. No significant deviations found.")
        else:
            logging.warning(f"Deviations found: {deviations}")

        return deviations

    async def trigger_self_correction(self, deviations: List[str]) -> None:
        """
        Triggers simulated self-correction actions based on identified deviations.

        :param deviations: A list of identified deviations from evaluate_current_state.
        """
        logging.info("Triggering simulated self-correction based on deviations...")
        for deviation in deviations:
            if "Economic health is poor" in deviation:
                if self.economic_engine:
                    logging.info("  --> Economic health poor. Running economic cycle for optimization/revenue.")
                    await self.economic_engine.run_economic_cycle()
                else:
                    logging.warning("  --> EconomicEngine not provided, cannot take economic action.")
            elif "Growth rate is low" in deviation:
                if self.self_reproduction:
                    logging.info("  --> Growth rate low. Suggesting self-reproduction (scale) actions.")
                    # For simplicity, trigger a small scale-up. Real logic would be more complex.
                    await self.self_reproduction.scale_self(scale_factor=1.2)
                else:
                    logging.warning("  --> SelfReproduction not provided, cannot take reproduction action.")
            elif "High resource consumption" in deviation or "Cost over budget" in deviation:
                if self.cost_monitor:
                    logging.info("  --> Resource consumption/cost issue. Running cost optimization checks.")
                    optimization_suggestions = self.cost_monitor.run_optimization_checks()
                    # In a real system, these suggestions would be applied.
                    if optimization_suggestions:
                        logging.info(f"    Optimization suggestions: {optimization_suggestions}")
                else:
                    logging.warning("  --> CostMonitor not provided, cannot take cost optimization action.")

        logging.info("Simulated self-correction complete.")

if __name__ == '__main__':
    # Example usage
    self_reflection = SelfReflection()
    
    # Simulate a healthy state
    healthy_state = {
        'economic_health': 'good',
        'social_sentiment': 'positive',
        'growth_rate': 'high',
        'resource_consumption': 'low',
        'cost_over_budget': False,
    }
    deviations_healthy = self_reflection.evaluate_current_state(healthy_state)
    self_reflection.trigger_self_correction(deviations_healthy)
    print(" " + "-"*80 + " ")

    # Simulate a state with deviations
    deviated_state = {
        'economic_health': 'poor',
        'social_sentiment': 'negative',
        'growth_rate': 'low',
        'resource_consumption': 'high',
        'cost_over_budget': True,
    }
    deviations_deviated = self_reflection.evaluate_current_state(deviated_state)
    self_reflection.trigger_self_correction(deviations_deviated)
