# -*- coding: utf-8 -*-
"""
IntentOS Heartbeat Module

This module provides a periodic, internal signal for IntentOS, enabling it
to autonomously wake up and trigger self-maintenance and reproduction tasks.
"""

import asyncio
import logging
from typing import Dict, Any, List
import random # For simulating current state

from intentos.kernel.self_reflection import SelfReflection # Import SelfReflection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Heartbeat:
    """
    Generates a periodic heartbeat to trigger autonomous IntentOS functions.
    """

    def __init__(self, interval_seconds: int = 3600): # Default to 1 hour
        """
        Initializes the Heartbeat module.\n\n        :param interval_seconds: The duration in seconds between each heartbeat.\n        """
        self.interval_seconds = interval_seconds
        self._running = False
        self.self_reflection = SelfReflection() # Instantiate SelfReflection
        logging.info(f"Heartbeat initialized with interval: {self.interval_seconds} seconds.")

    async def start(self) -> None:
        """
        Starts the periodic heartbeat.\n        """
        if self._running:
            logging.warning("Heartbeat is already running.")
            return

        self._running = True
        logging.info("Heartbeat started.")
        while self._running:
            logging.info(f"Heartbeat: Initiating autonomous cycle... (Next beat in {self.interval_seconds} seconds)")
            await self._on_beat()
            await asyncio.sleep(self.interval_seconds)

    def stop(self) -> None:
        """
        Stops the periodic heartbeat.\n        """
        self._running = False
        logging.info("Heartbeat stopped.")

    async def _on_beat(self) -> None:
        """
        This method is called on each heartbeat.
        It triggers the main autonomous functions of IntentOS, starting with self-reflection.
        """
        logging.info("Heartbeat: Triggering self-reflection...")

        # Simulate current state (in a real system, this would gather actual metrics)
        current_state = {
            'economic_health': random.choice(['good', 'neutral', 'poor']),
            'social_sentiment': random.choice(['positive', 'neutral', 'negative']),
            'growth_rate': random.choice(['high', 'medium', 'low']),
            'resource_consumption': random.choice(['low', 'medium', 'high']),
            'cost_over_budget': random.choice([True, False]),
        }
        logging.info(f"Heartbeat: Simulated current state: {current_state}")

        deviations = self.self_reflection.evaluate_current_state(current_state)
        if deviations:
            logging.warning(f"Heartbeat: Self-reflection identified deviations: {deviations}")
            self.self_reflection.trigger_self_correction(deviations)
        else:
            logging.info("Heartbeat: No significant deviations found. State is aligned.")

if __name__ == '__main__':
    async def demo_heartbeat():
        heartbeat = Heartbeat(interval_seconds=5) # 5 seconds for demonstration
        print("Starting demo heartbeat. Press Ctrl+C to stop. ")
        try:
            await heartbeat.start()
        except asyncio.CancelledError:
            print("\nHeartbeat demo cancelled.")
        finally:
            heartbeat.stop()
