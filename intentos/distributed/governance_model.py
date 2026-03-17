# -*- coding: utf-8 -*-
"""
IntentOS Governance Model

This module simulates a basic proposal and voting system, allowing credit holders
to create and vote on proposals, thus laying the groundwork for a Decentralized
Autonomous Organization (DAO) for IntentOS.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random # Import random for simulating initial voters

from intentos.agent.reward_system import RewardSystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Proposal:
    """
    Represents a governance proposal.
    """
    def __init__(self, proposer_id: str, title: str, description: str, vote_duration_days: int = 7):
        self.id = str(uuid.uuid4())
        self.proposer_id = proposer_id
        self.title = title
        self.description = description
        self.created_at = datetime.now()
        self.ends_at = self.created_at + timedelta(days=vote_duration_days)
        self.votes_for: float = 0.0
        self.votes_against: float = 0.0
        self.voters: Dict[str, bool] = {} # Records if a user has voted to prevent double voting
        self.status: str = "open" # "open", "closed", "passed", "failed"

    def is_active(self) -> bool:
        return self.status == "open" and datetime.now() < self.ends_at

    def close_vote(self):
        self.status = "closed"
        if self.votes_for > self.votes_against:
            self.status = "passed"
        else:
            self.status = "failed"
        logging.info(f"Proposal '{self.title}' ({self.id}) closed. Status: {self.status}")


class GovernanceModel:
    """
    Manages proposals and voting for IntentOS.
    """

    def __init__(self, reward_system: RewardSystem):
        """
        Initializes the GovernanceModel.

        :param reward_system: An instance of RewardSystem for checking credit balances.
        """
        self.reward_system = reward_system
        self.proposals: Dict[str, Proposal] = {}
        logging.info("GovernanceModel initialized.")

    def create_proposal(self, proposer_id: str, title: str, description: str, vote_duration_days: int = 7) -> Proposal:
        """
        Creates a new governance proposal.

        :param proposer_id: The ID of the entity proposing.
        :param title: The title of the proposal.
        :param description: The detailed description of the proposal.
        :param vote_duration_days: How many days the voting period will last.
        :return: The created Proposal object.
        """
        logging.info(f"Entity '{proposer_id}' creating new proposal: '{title}'")
        proposal = Proposal(proposer_id, title, description, vote_duration_days)
        self.proposals[proposal.id] = proposal
        logging.info(f"Proposal '{proposal.title}' created with ID: {proposal.id}")

        # Simulate initial voter participation and rewards
        num_initial_voters = random.randint(2, 5)
        logging.info(f"Simulating {num_initial_voters} initial voters for proposal '{proposal.title}'.")
        for i in range(num_initial_voters):
            voter_id = f"sim_voter_{random.randint(100, 999)}"
            # Award some credits for community engagement to these simulated voters
            self.reward_system.award_credits(voter_id, "community_engagement", random.uniform(1.0, 5.0))
            # Make them vote randomly
            self.vote_on_proposal(voter_id, proposal.id, random.choice([True, False]))

        return proposal

    def vote_on_proposal(self, voter_id: str, proposal_id: str, vote: bool) -> bool:
        """
        Allows an entity to vote on an active proposal.

        Voting power is weighted by the voter's credit balance.

        :param voter_id: The ID of the entity casting the vote.
        :param proposal_id: The ID of the proposal to vote on.
        :param vote: True for 'for', False for 'against'.
        :return: True if the vote was successful, False otherwise.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal or not proposal.is_active():
            logging.warning(f"Cannot vote on proposal {proposal_id}: not found or not active.")
            return False
        if voter_id in proposal.voters:
            logging.warning(f"Entity {voter_id} has already voted on proposal {proposal_id}.")
            return False
        
        voting_power = self.reward_system.get_balance(voter_id) # Voting power == credit balance
        if voting_power <= 0:
            logging.warning(f"Entity {voter_id} has no voting power (0 credits).")
            return False

        if vote:
            proposal.votes_for += voting_power
            logging.info(f"Entity {voter_id} voted FOR proposal '{proposal.title}' with {voting_power} power.")
        else:
            proposal.votes_against += voting_power
            logging.info(f"Entity {voter_id} voted AGAINST proposal '{proposal.title}' with {voting_power} power.")
        
        proposal.voters[voter_id] = True
        return True

    def get_proposal_status(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current status of a proposal.

        :param proposal_id: The ID of the proposal.
        :return: A dictionary with proposal details, or None if not found.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            return None

        # Close the vote if duration has passed
        if proposal.is_active() and datetime.now() >= proposal.ends_at:
            proposal.close_vote()
            
        return {
            "id": proposal.id,
            "title": proposal.title,
            "proposer_id": proposal.proposer_id,
            "description": proposal.description,
            "status": proposal.status,
            "votes_for": proposal.votes_for,
            "votes_against": proposal.votes_against,
            "total_votes": proposal.votes_for + proposal.votes_against,
            "ends_at": proposal.ends_at.isoformat(),
            "is_active": proposal.is_active(),
        }

    def get_all_proposals(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all proposals and their statuses.

        :return: A list of dictionaries, each representing a proposal's status.
        """
        all_proposals = []
        for proposal_id in list(self.proposals.keys()): # Iterate over a copy to allow modification if closing votes
            status = self.get_proposal_status(proposal_id)
            if status:
                all_proposals.append(status)
        return all_proposals
