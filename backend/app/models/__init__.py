"""
Database models package.

All models are imported here to ensure they are registered with SQLAlchemy
before Alembic migrations are generated.
"""

from app.models.user import User
from app.models.trip import (
    Trip,
    TripAccommodation,
    TripRestaurant,
    TripTransportation,
    TripActivity,
    TripExpense,
    TripStatus,
)
from app.models.conversation import Conversation, Message
from app.models.agent_state import AgentState, AgentInteraction

__all__ = [
    "User",
    "Trip",
    "TripAccommodation",
    "TripRestaurant",
    "TripTransportation",
    "TripActivity",
    "TripExpense",
    "TripStatus",
    "Conversation",
    "Message",
    "AgentState",
    "AgentInteraction",
]
