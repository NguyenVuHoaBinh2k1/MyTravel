"""
Streaming utilities for SSE (Server-Sent Events).
"""

import asyncio
import json
from typing import AsyncGenerator, Any


async def stream_response(generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    """
    Stream SSE formatted responses.

    Args:
        generator: Async generator yielding string chunks

    Yields:
        SSE formatted strings
    """
    try:
        async for chunk in generator:
            # Format as SSE
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0)  # Allow other tasks to run
    except Exception as e:
        # Send error event
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        # Send completion event
        yield f"data: {json.dumps({'done': True})}\n\n"


async def stream_agent_response(
    message_generator: AsyncGenerator[str, None],
    metadata: dict[str, Any] = None
) -> AsyncGenerator[str, None]:
    """
    Stream agent responses with metadata.

    Args:
        message_generator: Generator for message chunks
        metadata: Optional metadata to include

    Yields:
        SSE formatted agent responses
    """
    # Send initial metadata if provided
    if metadata:
        yield f"data: {json.dumps({'type': 'metadata', 'data': metadata})}\n\n"
        await asyncio.sleep(0)

    # Stream message chunks
    async for chunk in message_generator:
        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
        await asyncio.sleep(0)

    # Send completion
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
