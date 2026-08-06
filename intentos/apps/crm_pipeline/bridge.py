# -*- coding: utf-8 -*-
"""
CRM Event Bridge Broker
"""
from __future__ import annotations

from typing import Any, Callable


class CRMBridge:
    _lead_listeners: list[Callable[[str, dict[str, Any]], None]] = []
    _quote_listeners: list[Callable[[str, dict[str, Any]], None]] = []
    _refund_listeners: list[Callable[[str, dict[str, Any]], None]] = []

    @classmethod
    def register_lead_listener(cls, callback: Callable[[str, dict[str, Any]], None]) -> None:
        cls._lead_listeners.append(callback)

    @classmethod
    def register_quote_listener(cls, callback: Callable[[str, dict[str, Any]], None]) -> None:
        cls._quote_listeners.append(callback)

    @classmethod
    def register_refund_listener(cls, callback: Callable[[str, dict[str, Any]], None]) -> None:
        cls._refund_listeners.append(callback)

    @classmethod
    def notify_lead_analyzed(cls, customer_id: str, analysis_data: dict[str, Any]) -> None:
        for cb in cls._lead_listeners:
            cb(customer_id, analysis_data)

    @classmethod
    def notify_quote_generated(cls, customer_id: str, quote_data: dict[str, Any]) -> None:
        for cb in cls._quote_listeners:
            cb(customer_id, quote_data)

    @classmethod
    def notify_refund_requested(cls, customer_id: str, refund_data: dict[str, Any]) -> None:
        for cb in cls._refund_listeners:
            cb(customer_id, refund_data)
