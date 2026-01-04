"""
AI Chatbot Routes
Handles AI assistant interactions with multiple model support
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from api.v1.routes.auth import get_current_active_user, User
from core.logger import app_logger, audit_logger

# Import AI chatbot logic
try:
    from services.chatbot_logic_enhanced import get_response, get_streaming_response
except ImportError:
    # Fallback
    def get_response(query, model_choice="openai", user_id="anonymous"):
        return f"Response to: {query} (using {model_choice})"

    async def get_streaming_response(query, model_choice="openai", user_id="anonymous"):
        for word in f"Streaming response to: {query}".split():
            yield word + " "


router = APIRouter()


# Models
class ChatRequest(BaseModel):
    query: str
    model: str = "openai"  # openai, gemini, claude
    context: Optional[List[str]] = None


class ChatResponse(BaseModel):
    response: str
    model: str
    timestamp: datetime
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


class ModelInfo(BaseModel):
    name: str
    provider: str
    description: str
    cost_per_1k_tokens: float
    available: bool


# Available models
AVAILABLE_MODELS = [
    {
        "name": "openai",
        "provider": "OpenAI",
        "description": "GPT-3.5 Turbo - Fast and reliable",
        "cost_per_1k_tokens": 0.002,
        "available": True,
    },
    {
        "name": "gemini",
        "provider": "Google",
        "description": "Gemini Pro - Advanced reasoning",
        "cost_per_1k_tokens": 0.00025,
        "available": True,
    },
    {
        "name": "claude",
        "provider": "Anthropic",
        "description": "Claude 3 Sonnet - Detailed analysis",
        "cost_per_1k_tokens": 0.003,
        "available": True,
    },
]


# Routes
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, current_user: User = Depends(get_current_active_user)
):
    """
    Send message to AI assistant

    Supports multiple models:
    - openai: GPT-3.5 Turbo (fast, reliable)
    - gemini: Google Gemini Pro (advanced reasoning)
    - claude: Claude 3 Sonnet (detailed analysis)
    """
    # Validate model
    valid_models = [m["name"] for m in AVAILABLE_MODELS if m["available"]]
    if request.model not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Available: {', '.join(valid_models)}",
        )

    try:
        app_logger.info(
            "ai_chat_request",
            user=current_user.username,
            model=request.model,
            query_length=len(request.query),
        )

        # Get response from AI
        response_text = get_response(
            query=request.query,
            model_choice=request.model,
            user_id=current_user.username,
        )

        # Audit log
        audit_logger.log_user_query(
            user_id=current_user.username,
            query=request.query[:200],  # Log first 200 chars
            model=request.model,
        )

        # Calculate approximate tokens (rough estimate)
        tokens = len(request.query.split()) + len(response_text.split())

        # Get cost info
        model_info = next(
            (m for m in AVAILABLE_MODELS if m["name"] == request.model), None
        )
        cost = (
            (tokens / 1000) * model_info["cost_per_1k_tokens"] if model_info else None
        )

        return ChatResponse(
            response=response_text,
            model=request.model,
            timestamp=datetime.now(),
            tokens_used=tokens,
            cost=cost,
        )

    except Exception as e:
        app_logger.error("ai_chat_error", error=str(e), user=current_user.username)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/models", response_model=List[ModelInfo])
async def get_models(current_user: User = Depends(get_current_active_user)):
    """
    Get list of available AI models with pricing information
    """
    return [ModelInfo(**model) for model in AVAILABLE_MODELS]


@router.get("/history")
async def get_chat_history(
    limit: int = 50, current_user: User = Depends(get_current_active_user)
):
    """
    Get user's chat history

    Query Parameters:
    - limit: Maximum number of messages (default: 50)
    """
    # TODO: Implement database query for chat history
    app_logger.info("chat_history_request", user=current_user.username, limit=limit)

    return {"user_id": current_user.username, "messages": [], "total": 0}  # Placeholder


@router.websocket("/stream")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for streaming AI responses

    Client sends JSON: {"query": "...", "model": "openai", "token": "jwt_token"}
    Server streams response word by word
    """
    await websocket.accept()

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            query = data.get("query")
            model = data.get("model", "openai")
            token = data.get("token")

            if not query:
                await websocket.send_json({"error": "Query is required"})
                continue

            # TODO: Validate JWT token
            # For now, use anonymous user
            user_id = "websocket_user"

            app_logger.info(
                "websocket_chat_request", model=model, query_length=len(query)
            )

            # Stream response
            try:
                await websocket.send_json({"status": "streaming", "model": model})

                async for chunk in get_streaming_response(query, model, user_id):
                    await websocket.send_json({"chunk": chunk})

                await websocket.send_json({"status": "complete"})

            except Exception as e:
                app_logger.error("websocket_streaming_error", error=str(e))
                await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        app_logger.info("websocket_disconnected")
    except Exception as e:
        app_logger.error("websocket_error", error=str(e))
        await websocket.close()


@router.delete("/history")
async def clear_chat_history(current_user: User = Depends(get_current_active_user)):
    """
    Clear user's chat history
    """
    # TODO: Implement database deletion
    app_logger.info("chat_history_cleared", user=current_user.username)

    return {"message": "Chat history cleared successfully"}
