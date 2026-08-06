# -*- coding: utf-8 -*-
"""
CRM Pipeline Application Model

AI-driven pipeline with L4 Security Gate human-in-the-loop fallback.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

logger: logging.Logger = logging.getLogger(__name__)


class CRMPipelineApp:
    """
    CRM Pipeline Application Model

    Exposes lead scoring, quote generation, refund requests, and handoff utilities.
    """

    def __init__(self) -> None:
        self.app_id: str = "crm_pipeline"
        self.name: str = "CRM 运作流水线"
        self.version: str = "1.0.0"

        # State stores
        self.leads: dict[str, dict[str, Any]] = {}
        self.quotes: dict[str, dict[str, Any]] = {}
        self.refunds: dict[str, dict[str, Any]] = {}
        self.message_logs: dict[str, list[str]] = {}

    def lead_analyzer(self, customer_id: str, message: str) -> dict[str, Any]:
        """
        Analyzes incoming client messages, scores leads, and checks sentiment.
        """
        # Save message log
        if customer_id not in self.message_logs:
            self.message_logs[customer_id] = []
        self.message_logs[customer_id].append(message)

        # Basic sentiment heuristic for demonstration
        angry_keywords = ["生气", "太差", "退钱", "投诉", "垃圾", "愤怒", "生气了", "垃圾服务"]
        is_angry = any(kw in message for kw in angry_keywords)
        anger_score = 0.9 if is_angry else 0.1
        sentiment = "ANGRY" if is_angry else "NORMAL"

        # Simple lead scoring (0 - 100)
        score = 30
        if "买" in message or "购买" in message or "合作" in message:
            score += 40
        if "定价" in message or "报价" in message or "折扣" in message:
            score += 20

        result = {
            "customer_id": customer_id,
            "score": score,
            "sentiment": sentiment,
            "anger_score": anger_score,
            "message": message
        }
        self.leads[customer_id] = result
        return result

    def quote_generator(self, customer_id: str, amount: float, discount: float) -> dict[str, Any]:
        """
        Prepares a discount quote. High discount (>20%) requires manual approval.
        """
        final_price = amount * (1.0 - (discount / 100.0))
        quote_id = f"Q-{uuid.uuid4().hex[:8].upper()}"

        requires_approval = discount > 20.0

        result = {
            "quote_id": quote_id,
            "customer_id": customer_id,
            "original_amount": amount,
            "discount": discount,
            "final_price": final_price,
            "requires_approval": requires_approval
        }
        self.quotes[quote_id] = result
        return result

    def refund_handler(self, customer_id: str, amount: float) -> dict[str, Any]:
        """
        Requests a customer refund. All refunds require manual approval.
        """
        refund_id = f"RF-{uuid.uuid4().hex[:8].upper()}"

        # All refunds trigger L4 gate (human in the loop fallback)
        requires_approval = True

        result = {
            "refund_id": refund_id,
            "customer_id": customer_id,
            "amount": amount,
            "status": "PENDING_APPROVAL" if requires_approval else "APPROVED",
            "requires_approval": requires_approval
        }
        self.refunds[refund_id] = result
        return result

    def generate_handoff_summary(self, customer_id: str, reason: str, action_details: str) -> str:
        """
        Generates an interactive structural ASCII summary for a human representative.
        """
        lead_info = self.leads.get(customer_id, {})
        sentiment = lead_info.get("sentiment", "UNKNOWN")
        anger_val = lead_info.get("anger_score", 0.0)
        logs = self.message_logs.get(customer_id, [])
        log_str = " | ".join(logs[-3:]) if logs else "No messages logged"

        summary = f"""=========================================
CRM HANDOFF SUMMARY (L4 Security Gate Trigger)
=========================================
Client ID   : {customer_id}
Emotion     : {sentiment} (Anger: {anger_val:.2f})
Reason      : {reason}
Action      : {action_details}
Context     : {log_str}
-----------------------------------------
Decision Required: Approve / Deny Action
========================================="""
        return summary
