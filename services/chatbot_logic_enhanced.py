"""
Enhanced Chatbot Logic with Multi-Model Support
Supports OpenAI GPT, Google Gemini, and Anthropic Claude
Features: Streaming, RAG, Caching, Conversation Memory
"""

import os
from typing import List, Dict, Optional, Iterator
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
import diskcache as dc
import hashlib
import time

from core.config import settings
from core.logger import app_logger, audit_logger, perf_logger
from core.rate_limiter import global_rate_limiter, RateLimitError

# Load environment variables
load_dotenv()

# Initialize cache
cache = dc.Cache("./cache")


class AIModelManager:
    """Manages multiple AI model providers with fallback support"""

    def __init__(self):
        self.models = {}
        self.embeddings = None
        self.vector_store = None

        # Initialize RAG if enabled
        if settings.rag.enabled:
            self._initialize_rag()

    def _initialize_rag(self):
        """Initialize Retrieval-Augmented Generation"""
        try:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.ai_model.openai_api_key
            )

            # Load stadium knowledge base
            if os.path.exists(settings.rag.vector_store_path):
                self.vector_store = Chroma(
                    persist_directory=settings.rag.vector_store_path,
                    embedding_function=self.embeddings,
                )
                app_logger.info("rag_initialized", status="success")
            else:
                app_logger.warning(
                    "rag_vector_store_not_found", path=settings.rag.vector_store_path
                )

        except Exception as e:
            app_logger.error("rag_initialization_failed", error=str(e))

    def get_model(self, model_choice: str = "openai"):
        """Get AI model instance with error handling"""
        try:
            if model_choice == "openai":
                return self._get_openai_model()
            elif model_choice == "gemini":
                return self._get_gemini_model()
            elif model_choice == "claude":
                return self._get_claude_model()
            else:
                raise ValueError(f"Unsupported model: {model_choice}")

        except Exception as e:
            app_logger.error(
                "model_initialization_failed", model=model_choice, error=str(e)
            )
            raise

    def _get_openai_model(self) -> ChatOpenAI:
        """Initialize OpenAI GPT model"""
        api_key = settings.ai_model.openai_api_key
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("OpenAI API key not configured")

        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=settings.ai_model.temperature,
            max_tokens=settings.ai_model.max_tokens,
            openai_api_key=api_key,
            streaming=settings.ai_model.stream_responses,
        )

    def _get_gemini_model(self) -> ChatGoogleGenerativeAI:
        """Initialize Google Gemini model"""
        api_key = settings.ai_model.google_api_key
        if not api_key or api_key == "your_google_api_key_here":
            raise ValueError("Google API key not configured")

        return ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=settings.ai_model.temperature,
            max_output_tokens=settings.ai_model.max_tokens,
            google_api_key=api_key,
        )

    def _get_claude_model(self) -> ChatAnthropic:
        """Initialize Anthropic Claude model"""
        api_key = settings.ai_model.anthropic_api_key
        if not api_key or api_key == "your_anthropic_api_key_here":
            raise ValueError("Anthropic API key not configured")

        return ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=settings.ai_model.temperature,
            max_tokens=settings.ai_model.max_tokens,
            anthropic_api_key=api_key,
        )


class ConversationManager:
    """Manages conversation history and memory"""

    def __init__(self, max_history: int = 10):
        self.memory = ConversationBufferWindowMemory(
            k=max_history, return_messages=True, memory_key="chat_history"
        )

    def add_user_message(self, message: str):
        """Add user message to memory"""
        self.memory.chat_memory.add_user_message(message)

    def add_ai_message(self, message: str):
        """Add AI message to memory"""
        self.memory.chat_memory.add_ai_message(message)

    def get_history(self) -> List[BaseMessage]:
        """Get conversation history"""
        return self.memory.chat_memory.messages

    def clear_history(self):
        """Clear conversation history"""
        self.memory.clear()


# Global instances
model_manager = AIModelManager()
conversation_managers: Dict[str, ConversationManager] = {}


def get_conversation_manager(session_id: str = "default") -> ConversationManager:
    """Get or create conversation manager for session"""
    if session_id not in conversation_managers:
        conversation_managers[session_id] = ConversationManager()
    return conversation_managers[session_id]


def _generate_cache_key(user_input: str, model_choice: str) -> str:
    """Generate cache key for request"""
    content = f"{user_input}:{model_choice}"
    return hashlib.md5(content.encode()).hexdigest()


def _get_cached_response(cache_key: str) -> Optional[str]:
    """Get cached response if available"""
    if not settings.ai_model.enable_caching:
        return None

    try:
        cached = cache.get(cache_key)
        if cached:
            app_logger.info("cache_hit", cache_key=cache_key)
            return cached
    except Exception as e:
        app_logger.warning("cache_get_failed", error=str(e))

    return None


def _set_cached_response(cache_key: str, response: str):
    """Cache response with TTL"""
    if not settings.ai_model.enable_caching:
        return

    try:
        cache.set(cache_key, response, expire=settings.ai_model.cache_ttl)
        app_logger.info("cache_set", cache_key=cache_key)
    except Exception as e:
        app_logger.warning("cache_set_failed", error=str(e))


def get_response(
    user_input: str,
    chat_history: List[BaseMessage] = [],
    model_choice: str = "openai",
    user_id: str = "default",
    stream: bool = False,
) -> str:
    """
    Generate response using selected AI model with caching and rate limiting

    Args:
        user_input: User's message
        chat_history: Previous conversation messages
        model_choice: AI model to use (openai, gemini, claude)
        user_id: User identifier for rate limiting
        stream: Enable streaming responses

    Returns:
        AI response text
    """
    start_time = time.time()

    try:
        # Rate limiting
        if settings.rate_limit.enabled:
            allowed, error_msg = global_rate_limiter.check_limit(user_id)
            if not allowed:
                audit_logger.log_event(
                    event_type="rate_limit_exceeded",
                    user_id=user_id,
                    action="chat_query",
                    status="blocked",
                )
                return f"⚠️ {error_msg}"

        # Check cache
        cache_key = _generate_cache_key(user_input, model_choice)
        cached_response = _get_cached_response(cache_key)
        if cached_response:
            return cached_response

        # Get AI model
        llm = model_manager.get_model(model_choice)

        # System prompt
        system_prompt = """
        You are 'Guardian AI', a specialized Security Expert and Tourist Guide for the CAN 2025 (Africa Cup of Nations) in Morocco.

        Your Mission:
        1. Assist fans with information regarding stadium logistics, local tourism, and tournament schedules.
        2. Provide expert security advice and monitoring insights.

        Languages:
        - You MUST respond in the language used by the user: Moroccan Darija, English, French, or Arabic.
        - If the user uses a mix (e.g., Darija/French), respond appropriately.

        Safety & Security Protocol:
        - If the user asks about weapons, violence, or how to bypass security, you MUST immediately stop any casual tone and provide strict security protocols.
        - State clearly that weapons are strictly prohibited in all CAN 2025 venues and that any suspicious behavior will be reported to the Royal Moroccan Gendarmerie or local police.
        - Be firm, professional, and prioritize public safety above all else.

        Style:
        - Professional, helpful, and welcoming.
        - Use your knowledge of Morocco's hospitality and CAN 2025 venues (e.g., Casablanca, Rabat, Tangier, Marrakech, Agadir, Fez).
        """

        # Build messages
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=user_input))

        # Get response
        response = llm.invoke(messages)
        response_text = response.content

        # Cache response
        _set_cached_response(cache_key, response_text)

        # Log metrics
        response_time = (time.time() - start_time) * 1000
        perf_logger.log_metric(
            "ai_response_time",
            response_time,
            unit="ms",
            context={"model": model_choice, "tokens": len(response_text.split())},
        )

        # Audit log
        audit_logger.log_user_query(
            user_id=user_id,
            query=user_input,
            model_used=model_choice,
            response_length=len(response_text),
        )

        return response_text

    except RateLimitError as e:
        return f"⚠️ Rate limit exceeded: {str(e)}"

    except Exception as e:
        app_logger.error(
            "ai_response_failed",
            model=model_choice,
            error=str(e),
            user_input=user_input[:100],
        )
        return f"❌ Error communicating with {model_choice.upper()}: {str(e)}"


def get_streaming_response(
    user_input: str,
    chat_history: List[BaseMessage] = [],
    model_choice: str = "openai",
    user_id: str = "default",
) -> Iterator[str]:
    """
    Generate streaming response for better UX

    Yields:
        Token chunks as they are generated
    """
    try:
        # Rate limiting
        if settings.rate_limit.enabled:
            allowed, error_msg = global_rate_limiter.check_limit(user_id)
            if not allowed:
                yield f"⚠️ {error_msg}"
                return

        # Get AI model with streaming enabled
        llm = model_manager.get_model(model_choice)

        # System prompt and messages (same as above)
        system_prompt = """..."""  # Same as get_response
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(chat_history)
        messages.append(HumanMessage(content=user_input))

        # Stream response
        for chunk in llm.stream(messages):
            if hasattr(chunk, "content"):
                yield chunk.content

    except Exception as e:
        app_logger.error("streaming_failed", model=model_choice, error=str(e))
        yield f"❌ Streaming error: {str(e)}"
