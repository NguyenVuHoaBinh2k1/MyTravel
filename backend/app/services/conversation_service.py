"""
Conversation service layer for business logic.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message
from app.schemas.conversation import ConversationCreate, MessageCreate
from app.core.logging import get_logger

logger = get_logger(__name__)


async def create_conversation(
    db: AsyncSession,
    user_id: int,
    data: ConversationCreate
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        user_id=user_id,
        trip_id=data.trip_id,
        title=data.title,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    logger.info("conversation_created", conversation_id=conversation.id, user_id=user_id)
    return conversation


async def get_conversation(
    db: AsyncSession,
    conversation_id: int
) -> Optional[Conversation]:
    """Get conversation by ID with messages."""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


async def get_user_conversations(
    db: AsyncSession,
    user_id: int,
    trip_id: Optional[int] = None
) -> list[Conversation]:
    """Get user's conversations."""
    query = select(Conversation).where(Conversation.user_id == user_id)

    if trip_id:
        query = query.where(Conversation.trip_id == trip_id)

    query = query.order_by(Conversation.updated_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def add_message(
    db: AsyncSession,
    conversation_id: int,
    role: str,
    content: str,
    agent_type: Optional[str] = None,
    metadata: Optional[dict] = None
) -> Message:
    """Add a message to a conversation."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        agent_type=agent_type,
        metadata=metadata,
    )
    db.add(message)

    # Update conversation timestamp
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        from datetime import datetime
        conversation.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(message)

    logger.info(
        "message_added",
        message_id=message.id,
        conversation_id=conversation_id,
        role=role
    )
    return message


async def get_conversation_messages(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 100,
    offset: int = 0
) -> list[Message]:
    """Get messages from a conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def delete_conversation(
    db: AsyncSession,
    conversation: Conversation
) -> bool:
    """Delete a conversation and all its messages."""
    await db.delete(conversation)
    await db.commit()

    logger.info("conversation_deleted", conversation_id=conversation.id)
    return True


async def search_messages(
    db: AsyncSession,
    user_id: int,
    query: str,
    limit: int = 50
) -> list[Message]:
    """Search messages across user's conversations."""
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .where(
            Conversation.user_id == user_id,
            Message.content.ilike(f"%{query}%")
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
