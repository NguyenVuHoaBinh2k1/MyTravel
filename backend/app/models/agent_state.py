"""
Agent State database model for persisting agent state across interactions.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentState(Base):
    """Model for storing agent state and context."""

    __tablename__ = "agent_states"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"), nullable=False, index=True
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Current state in the agent workflow
    current_step: Mapped[str] = mapped_column(String(100), nullable=False)

    # Collected information
    collected_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Questions asked and answered
    questions_asked: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Pending actions or follow-ups
    pending_actions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Last AI response for context
    last_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<AgentState {self.agent_type} - {self.current_step}>"


class AgentInteraction(Base):
    """Model for logging agent interactions for analytics."""

    __tablename__ = "agent_interactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"), nullable=False, index=True
    )
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Input/Output
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    agent_response: Mapped[str] = mapped_column(Text, nullable=False)

    # Metrics
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Response metadata
    response_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    suggestions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Status
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<AgentInteraction {self.agent_type} - {self.id}>"
