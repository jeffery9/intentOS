# -*- coding: utf-8 -*-
"""
Marketing Campaign Application Model
"""
from __future__ import annotations
import uuid
from typing import Any
from intentos.apps.crm_pipeline.bridge import CRMBridge

class MarketingPipelineApp:
    def __init__(self) -> None:
        self.app_id: str = "marketing_pipeline"
        self.name: str = "CRM 营销投放流水线"
        self.version: str = "1.0.0"

        # Campaign state: {customer_id: [campaign_records]}
        self.campaign_enrollments: dict[str, list[dict[str, Any]]] = {}

        # Auto-register event hook listeners
        CRMBridge.register_lead_listener(self.on_lead_analyzed)
        CRMBridge.register_quote_listener(self.on_quote_generated)
        CRMBridge.register_refund_listener(self.on_refund_requested)

    def enroll_campaign(self, customer_id: str, campaign_name: str, voucher_prefix: str, discount_rate: float = 0.0, credit: float = 0.0) -> dict[str, Any]:
        """Helper to create campaign enrollment and voucher code."""
        voucher = f"{voucher_prefix}-{uuid.uuid4().hex[:8].upper()}"
        record = {
            "campaign_name": campaign_name,
            "voucher_code": voucher,
            "discount_rate": discount_rate,
            "credit": credit,
            "status": "ACTIVE"
        }
        if customer_id not in self.campaign_enrollments:
            self.campaign_enrollments[customer_id] = []
        self.campaign_enrollments[customer_id].append(record)
        return record

    def on_lead_analyzed(self, customer_id: str, lead_data: dict[str, Any]) -> None:
        """Processes lead analysis. Triggers Retention or Nurture flows."""
        # Flow 1: High Anger (anger_score > 0.8)
        if lead_data.get("anger_score", 0.0) > 0.8:
            self.enroll_campaign(customer_id, "Win-Back Retention Program", "RET-COMP", discount_rate=30.0)
        # Flow 3: Warm prospects (score >= 60, not angry)
        elif lead_data.get("score", 0) >= 60:
            self.enroll_campaign(customer_id, "Lead Nurture Campaign", "NURTURE-WARM", discount_rate=15.0)

    def on_quote_generated(self, customer_id: str, quote_data: dict[str, Any]) -> None:
        """Processes quote events. Triggers VIP loyalty flow if final_price >= 1000."""
        # Flow 2: VIP loyalty (final_price >= 1000.0)
        if quote_data.get("final_price", 0.0) >= 1000.0:
            self.enroll_campaign(customer_id, "VIP Loyalty Program", "VIP-CLUB", credit=150.0)

    def on_refund_requested(self, customer_id: str, refund_data: dict[str, Any]) -> None:
        """Processes refund requests. Triggers Retention win-back immediately."""
        self.enroll_campaign(customer_id, "Win-Back Retention Program", "RET-COMP", discount_rate=30.0)
