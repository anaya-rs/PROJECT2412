"""
Analytics Module - Event-Based Analytics
Contains analytics collection and analysis logic.
"""

from .events import (
    AnalyticsEvent,
    AnalyticsCollector,
    create_session_analytics
)

__all__ = [
    "AnalyticsEvent",
    "AnalyticsCollector", 
    "create_session_analytics"
]
