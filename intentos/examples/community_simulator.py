# -*- coding: utf-8 -*-
"""
IntentOS Community Interaction Simulator

This script demonstrates how IntentOS modules (RewardSystem, SocialAgent, GovernanceModel)
interact to simulate community building, engagement, and governance.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import random

from intentos.agent.reward_system import RewardSystem
from intentos.agent.social_agent import SocialAgent
from intentos.distributed.governance_model import GovernanceModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def simulate_community_cycle():
    logging.info("
========================================================")
    logging.info("SIMULATING INTENTOS COMMUNITY INTERACTION CYCLE")
    logging.info("========================================================")

    # 1. Initialize core community modules
    reward_system = RewardSystem()
    social_agent = SocialAgent(reward_system=reward_system)
    governance_model = GovernanceModel(reward_system=reward_system)

    # Give some initial credits to a few users to kickstart the economy
    initial_users = [f"user_{i}" for i in range(1, 4)]
    for user_id in initial_users:
        reward_system.award_credits(user_id, "code_contribution", random.uniform(5.0, 15.0))
        logging.info(f"Initial credits for {user_id}: {reward_system.get_balance(user_id)}")

    # 2. Social Agent announces a new feature and incentivizes engagement
    logging.info("
--- Social Agent: Announcing New Feature and Incentivizing Engagement ---")
    new_feature_announcement = "IntentOS now supports self-reproduction! Help us test and earn credits!"
    await social_agent.post_to_twitter(new_feature_announcement, {"feature": "self_reproduction"})
    await social_agent.post_to_discord("general-chat", new_feature_announcement, {"feature": "self_reproduction"})

    # Simulate more users getting credits through engagement
    for _ in range(5):
        user_id = f"user_{random.randint(4, 10)}"
        reward_system.award_credits(user_id, "community_engagement", random.uniform(0.5, 2.0))
        logging.info(f"User {user_id} engaged and earned credits. Balance: {reward_system.get_balance(user_id)}")

    # 3. A user proposes a new governance initiative
    logging.info("
--- User Proposal: New Governance Initiative ---")
    proposer_id = initial_users[0] # One of our initial, credited users
    proposal_title = "Allocate 1000 credits to community-led documentation efforts"
    proposal_description = "This proposal aims to fund community members who create high-quality tutorials and documentation for IntentOS. Credits will be awarded upon approval by core contributors."
    new_proposal = governance_model.create_proposal(proposer_id, proposal_title, proposal_description, vote_duration_days=0.001) # Short duration for simulation
    logging.info(f"Proposal created by {proposer_id}: '{new_proposal.title}' (ID: {new_proposal.id})")

    # Simulate more users voting on the proposal
    logging.info("Simulating more community members voting...")
    for i in range(11, 20):
        voter_id = f"user_{i}"
        # Give them some credits first if they don't have any
        if reward_system.get_balance(voter_id) == 0:
            reward_system.award_credits(voter_id, "community_engagement", random.uniform(1.0, 3.0))
        governance_model.vote_on_proposal(voter_id, new_proposal.id, random.choice([True, False, True])) # Bias towards 'True'

    # 4. Check proposal status after some time (simulated)
    logging.info("
--- Checking Proposal Status After Voting Period ---")
    # Advance time to ensure vote closes for simulation purposes
    await asyncio.sleep(1) # Simulate passage of time
    final_status = governance_model.get_proposal_status(new_proposal.id)
    if final_status:
        logging.info(f"Proposal '{final_status['title']}' status: {final_status['status']}")
        logging.info(f"Votes For: {final_status['votes_for']} | Votes Against: {final_status['votes_against']}")
        if final_status['status'] == 'passed':
            logging.info("🎉 Proposal PASSED! Community-led documentation efforts will be funded.")
        else:
            logging.info("💔 Proposal FAILED or still open.")
    
    # 5. Display some user balances to show impact of rewards
    logging.info("
--- Final User Credit Balances ---")
    all_entity_ids = list(set(reward_system.ledger.keys()))
    for entity_id in all_entity_ids:
        logging.info(f"Balance for {entity_id}: {reward_system.get_balance(entity_id)} credits.")

    logging.info("
========================================================")
    logging.info("COMMUNITY SIMULATION ENDED")
    logging.info("========================================================")

if __name__ == '__main__':
    # Add 'community_engagement' to RewardSystem if it's not present (for standalone running)
    # This part should ideally be handled by a central configuration/initialization routine
    # for IntentOS itself, not here in the example, but for demonstration it works.
    temp_reward_system = RewardSystem()
    if "community_engagement" not in temp_reward_system.get_contribution_types():
        temp_reward_system.contribution_types["community_engagement"] = 0.1 # Base reward for engagement
        logging.warning("Added 'community_engagement' type to RewardSystem for simulation.")

    asyncio.run(simulate_community_cycle())
