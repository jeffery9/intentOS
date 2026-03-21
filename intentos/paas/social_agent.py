# -*- coding: utf-8 -*-
"""
IntentOS Social Transmission Agent

This module defines a specialized agent powered by the IntentOS core,
configured to perform marketing and community engagement tasks autonomously.
"""

import logging
import os
import random
from typing import Any, Dict, Optional

import yaml

from intentos.agent.reward_system import RewardSystem  # Import RewardSystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SocialAgent:
    """
    A specialized IntentOS agent for social transmission and community engagement.
    """

    def __init__(self, agent_id: str = "intentos-social-agent", llm_backend: Any = None, reward_system: Optional[RewardSystem] = None, soul_manifest_path: str = 'intentos/config/soul_manifest.yaml'):
        """
        Initializes the SocialAgent.

        :param agent_id: The unique ID of this social agent.
        :param llm_backend: An LLM backend instance for generating content (e.g., tweets).
        :param reward_system: An instance of RewardSystem for awarding credits.
        :param soul_manifest_path: Path to the soul manifest YAML file.
        """
        self.agent_id = agent_id
        self.llm_backend = llm_backend # Placeholder for an actual LLM integration
        self.reward_system = reward_system
        self.soul_manifest: Dict[str, Any] = {}
        self._load_soul_manifest(soul_manifest_path)
        logging.info(f"SocialAgent initialized with ID: {self.agent_id}")

    def _load_soul_manifest(self, manifest_path: str) -> None:
        """
        Loads the IntentOS soul manifest from the YAML file.
        """
        if not os.path.exists(manifest_path):
            logging.warning(f"Soul Manifest file not found at: {manifest_path}. SocialAgent will operate without explicit values.")
            return
        try:
            with open(manifest_path, 'r') as f:
                self.soul_manifest = yaml.safe_load(f)
            logging.info("Soul manifest loaded successfully by SocialAgent.")
        except yaml.YAMLError as e:
            logging.error(f"Error parsing SocialAgent's Soul Manifest YAML: {e}")
            # Continue without manifest rather than crashing

    async def _generate_content(self, prompt: str) -> str:
        """
        Simulates content generation using an LLM backend, incorporating soul manifest elements.

        :param prompt: The prompt for content generation.
        :return: Generated content (e.g., a tweet, a summary).
        """
        core_message_parts = []
        if self.soul_manifest:
            mission = self.soul_manifest.get('mission', [])
            values = self.soul_manifest.get('values', [])

            if mission and random.random() < 0.5: # 50% chance to include a mission statement
                core_message_parts.append(random.choice(mission))
            if values and random.random() < 0.5: # 50% chance to include a value
                core_message_parts.append(f"#IntentOS {random.choice(values).get('name')}")

        core_message = " ".join(core_message_parts)

        if self.llm_backend:
            logging.info(f"LLM backend generating content for prompt: {prompt}")
            return f"[LLM-generated content: \'{prompt}\' {core_message} - This is a great feature! #IntentOS {random.choice(['AI', 'Future', 'Tech'])}{random.randint(100, 999)} ]"
        else:
            logging.warning("LLM backend not provided. Returning generic content.")
            return f"[Generic content for: {prompt}] {core_message}"

    async def post_to_twitter(self, message_prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Simulates posting a message to Twitter and rewards simulated engagement.

        :param message_prompt: A prompt to generate the tweet content.
        :param context: Additional context for content generation.
        :return: Details of the simulated post.
        """
        logging.info(f"SocialAgent posting to Twitter. Prompt: {message_prompt}")
        content = await self._generate_content(message_prompt + f" (context: {context or {}})")

        post_details = {
            "platform": "Twitter",
            "agent_id": self.agent_id,
            "content": content,
            "timestamp": "2026-03-18T11:00:00Z",
            "status": "posted",
            "post_url": "https://twitter.com/intentos_ai/status/1234567890"
        }
        logging.info(f"Simulated Twitter post: {post_details['content']}")

        # Simulate community engagement and award credits
        if self.reward_system:
            num_likes = random.randint(5, 50)
            num_retweets = random.randint(1, 10)
            for _ in range(num_likes):
                self.reward_system.award_credits(f"user_{random.randint(1, 100)}", "community_engagement", 0.1) # Small reward for likes
            for _ in range(num_retweets):
                self.reward_system.award_credits(f"user_{random.randint(1, 100)}", "user_referral", 1.0) # Larger reward for retweets/shares
            logging.info(f"Simulated {num_likes} likes and {num_retweets} retweets, awarded credits.")

        return post_details

    async def post_to_discord(self, channel: str, message_prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Simulates posting a message to a Discord channel and rewards simulated engagement.

        :param channel: The Discord channel to post to.
        :param message_prompt: A prompt to generate the message content.
        :param context: Additional context for content generation.
        :return: Details of the simulated post.
        """
        logging.info(f"SocialAgent posting to Discord channel '{channel}'. Prompt: {message_prompt}")
        content = await self._generate_content(message_prompt + f" (context: {context or {}})")

        post_details = {
            "platform": "Discord",
            "agent_id": self.agent_id,
            "channel": channel,
            "content": content,
            "timestamp": "2026-03-18T11:05:00Z",
            "status": "posted",
        }
        logging.info(f"Simulated Discord post to {channel}: {post_details['content']}")

        # Simulate community engagement and award credits
        if self.reward_system:
            num_reactions = random.randint(3, 20)
            num_comments = random.randint(1, 5)
            for _ in range(num_reactions):
                self.reward_system.award_credits(f"user_{random.randint(1, 100)}", "community_engagement", 0.05) # Small reward for reactions
            for _ in range(num_comments):
                self.reward_system.award_credits(f"user_{random.randint(1, 100)}", "code_contribution", 0.5) # Modest reward for comments/discussion
            logging.info(f"Simulated {num_reactions} reactions and {num_comments} comments, awarded credits.")

        return post_details

    async def summarize_pull_requests(self, repo: str, count: int = 5) -> str:
        """
        Simulates summarizing recent pull requests.

        :param repo: The repository to summarize PRs from.
        :param count: The number of recent PRs to summarize.
        :return: A summary string.
        """
        logging.info(f"SocialAgent summarizing {count} recent PRs from {repo}.")
        summary_prompt = f"Summarize the latest {count} merged pull requests from GitHub repository {repo} for a community update."
        return await self._generate_content(summary_prompt)
