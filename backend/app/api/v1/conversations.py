"""
Conversation API endpoints.
"""

from typing import Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate, ConversationResponse, ConversationDetailResponse,
    MessageCreate, MessageResponse, ChatRequest, ChatResponse
)
from app.services import conversation_service, trip_service
from app.agents.orchestrator import get_orchestrator
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Create a new conversation."""
    conversation = await conversation_service.create_conversation(
        db, current_user.id, data
    )
    return ConversationResponse.model_validate(conversation)


@router.get("", response_model=list[ConversationResponse])
async def get_conversations(
    trip_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationResponse]:
    """Get user's conversations."""
    conversations = await conversation_service.get_user_conversations(
        db, current_user.id, trip_id
    )
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetailResponse:
    """Get conversation with messages."""
    conversation = await conversation_service.get_conversation(db, conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation",
        )

    return ConversationDetailResponse.model_validate(conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageResponse]:
    """Get messages from a conversation."""
    conversation = await conversation_service.get_conversation(db, conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation",
        )

    messages = await conversation_service.get_conversation_messages(
        db, conversation_id, limit, offset
    )
    return [MessageResponse.model_validate(m) for m in messages]


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Add a user message to a conversation."""
    conversation = await conversation_service.get_conversation(db, conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation",
        )

    message = await conversation_service.add_message(
        db, conversation_id, "user", data.content
    )
    return MessageResponse.model_validate(message)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a conversation."""
    conversation = await conversation_service.get_conversation(db, conversation_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this conversation",
        )

    await conversation_service.delete_conversation(db, conversation)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Send a message and get AI response.

    This is the main chat endpoint that routes messages through the orchestrator.
    """
    # Get or create conversation
    if data.conversation_id:
        conversation = await conversation_service.get_conversation(db, data.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )
    else:
        # Create new conversation
        conv_data = ConversationCreate(trip_id=data.trip_id)
        conversation = await conversation_service.create_conversation(
            db, current_user.id, conv_data
        )

    # Add user message
    user_message = await conversation_service.add_message(
        db, conversation.id, "user", data.message
    )

    # Get trip data if available
    trip_data = None
    if data.trip_id or conversation.trip_id:
        trip_id = data.trip_id or conversation.trip_id
        trip = await trip_service.get_trip(db, trip_id)
        if trip and trip.user_id == current_user.id:
            trip_data = {
                "destination": trip.destination,
                "start_date": str(trip.start_date) if trip.start_date else None,
                "end_date": str(trip.end_date) if trip.end_date else None,
                "travelers_count": trip.travelers_count,
                "budget": float(trip.budget) if trip.budget else None,
            }

    # Get conversation history
    messages = await conversation_service.get_conversation_messages(
        db, conversation.id, limit=20
    )
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages[:-1]  # Exclude the message we just added
    ]

    # Process through orchestrator
    orchestrator = get_orchestrator()
    agent_response = await orchestrator.process(
        message=data.message,
        user_id=str(current_user.id),
        trip_id=str(conversation.trip_id) if conversation.trip_id else None,
        trip_data=trip_data,
        conversation_history=conversation_history
    )

    # Save assistant response
    assistant_message = await conversation_service.add_message(
        db,
        conversation.id,
        "assistant",
        agent_response.message,
        agent_type=agent_response.agent_type,
        metadata={
            "data": agent_response.data,
            "suggestions": agent_response.suggestions,
            "actions": agent_response.actions
        }
    )

    logger.info(
        "chat_completed",
        user_id=current_user.id,
        conversation_id=conversation.id,
        agent_type=agent_response.agent_type
    )

    return ChatResponse(
        message=MessageResponse.model_validate(assistant_message),
        conversation_id=conversation.id,
        agent_type=agent_response.agent_type,
        data=agent_response.data,
        suggestions=agent_response.suggestions,
        actions=agent_response.actions
    )


@router.post("/chat/stream")
async def chat_stream(
    data: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Send a message and get streaming AI response using Server-Sent Events.

    This endpoint streams the AI response in real-time for better UX.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Get or create conversation
            conversation = None
            if data.conversation_id:
                conversation = await conversation_service.get_conversation(db, data.conversation_id)
                if not conversation:
                    yield f"data: {json.dumps({'error': 'Conversation not found'})}\n\n"
                    return
                if conversation.user_id != current_user.id:
                    yield f"data: {json.dumps({'error': 'Not authorized'})}\n\n"
                    return
            else:
                # Create new conversation
                conv_data = ConversationCreate(trip_id=data.trip_id)
                conversation = await conversation_service.create_conversation(
                    db, current_user.id, conv_data
                )

            # Send conversation ID
            yield f"data: {json.dumps({'type': 'conversation_id', 'data': conversation.id})}\n\n"

            # Add user message
            user_message = await conversation_service.add_message(
                db, conversation.id, "user", data.message
            )

            # Get trip data if available
            trip_data = None
            if data.trip_id or conversation.trip_id:
                trip_id = data.trip_id or conversation.trip_id
                trip = await trip_service.get_trip(db, trip_id)
                if trip and trip.user_id == current_user.id:
                    trip_data = {
                        "destination": trip.destination,
                        "start_date": str(trip.start_date) if trip.start_date else None,
                        "end_date": str(trip.end_date) if trip.end_date else None,
                        "travelers_count": trip.travelers_count,
                        "budget": float(trip.budget) if trip.budget else None,
                    }

            # Get conversation history
            messages = await conversation_service.get_conversation_messages(
                db, conversation.id, limit=20
            )
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in messages[:-1]  # Exclude the message we just added
            ]

            # Process through orchestrator
            orchestrator = get_orchestrator()
            agent_response = await orchestrator.process(
                message=data.message,
                user_id=str(current_user.id),
                trip_id=str(conversation.trip_id) if conversation.trip_id else None,
                trip_data=trip_data,
                conversation_history=conversation_history
            )

            # Stream the response message in chunks
            message_content = agent_response.message
            chunk_size = 20  # Characters per chunk

            for i in range(0, len(message_content), chunk_size):
                chunk = message_content[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Send metadata
            yield f"data: {json.dumps({'type': 'metadata', 'agent_type': agent_response.agent_type, 'suggestions': agent_response.suggestions, 'actions': agent_response.actions})}\n\n"

            # Save assistant response
            assistant_message = await conversation_service.add_message(
                db,
                conversation.id,
                "assistant",
                agent_response.message,
                agent_type=agent_response.agent_type,
                metadata={
                    "data": agent_response.data,
                    "suggestions": agent_response.suggestions,
                    "actions": agent_response.actions
                }
            )

            # Send completion with message ID
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.id})}\n\n"

            logger.info(
                "chat_stream_completed",
                user_id=current_user.id,
                conversation_id=conversation.id,
                agent_type=agent_response.agent_type
            )

        except Exception as e:
            logger.error("chat_stream_error", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
