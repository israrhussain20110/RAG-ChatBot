import asyncio
import os
import re
import uuid
import logging
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import spacy
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from ..schemas.chat import ChatRequest
from ..services.ingestion import get_vector_store
from ..services.grammar_rules import ENGLISH_GRAMMAR_GUIDELINES
from starlette.responses import Response

# =========================================================
# Load environment variables
# =========================================================
load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)
DEBUG_STREAM_LOGS = os.getenv("DEBUG_STREAM_LOGS", "false").lower() == "true"

# =========================================================
# --- LLM Configuration ---
# =========================================================
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
    elif provider == "deepseek":
        return ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            temperature=0,
        )
    else:
        return ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)

llm = get_llm()

# --- spaCy NLP Model ---
# IMPORTANT: Ensure spaCy and the 'en_core_web_sm' model are installed.
# pip install spacy
# python -m spacy download en_core_web_sm
nlp = spacy.load('en_core_web_sm')

# =========================================================
# --- Cleaning Helpers ---
# =========================================================
def clean_context(text: str) -> str:
    """Remove all 'data:' artifacts and collapse spaces from document context."""
    return re.sub(r'(?i)([:\s]*data[:\s]*)+', ' ', text or '').strip()


def normalize_text(text: str) -> str:
    """Completely remove all 'data:' artifacts and fix punctuation/spacing."""
    if not text:
        return ""

    normalized = str(text)

    # Remove stacked or stray 'data:' labels
    normalized = re.sub(r'(?i)(data\s*:\s*)+', '', normalized)

    # Fix punctuation spacing
    normalized = re.sub(r'([a-z])([A-Z])', r'\1 \2', normalized)
    normalized = re.sub(r'\s+([.,!?:;])', r'\1', normalized)
    normalized = re.sub(r'([.,!?:;])(?=\S)', r'\1 ', normalized)
    normalized = re.sub(r'\s{2,}', ' ', normalized)
    normalized = normalized.replace(" .", ".").replace(" ,", ",").strip()

    # Capitalize if necessary
    if normalized and not normalized[0].isupper():
        normalized = normalized[0].upper() + normalized[1:]

    return normalized


# =========================================================
# --- RAG Setup ---
# =========================================================
retriever = get_vector_store().as_retriever()
DEFAULT_RAG_PROMPT = f"{ENGLISH_GRAMMAR_GUIDELINES}\n\nAnswer the question based on the following context:\n\n{{context}}\n\nQuestion: {{question}}"
rag_prompt = PromptTemplate.from_template(DEFAULT_RAG_PROMPT)
prompt_llm_chain = rag_prompt | llm | StrOutputParser()

@router.get("/api/v1/chat/rag/prompt")
async def get_rag_prompt():
    """
    Returns the default RAG prompt.
    """
    return {"prompt": DEFAULT_RAG_PROMPT}


# =========================================================
# --- CORS Preflight ---
# =========================================================
@router.options("/api/v1/chat/rag/stream")
async def chat_rag_options():
    """Handle CORS preflight request."""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Accept",
            "Access-Control-Max-Age": "600",
        },
    )


# =========================================================
# --- Mock Current User ---
# =========================================================
async def get_current_user():
    return {"username": "testuser"}


# =========================================================
# --- RAG Streaming Endpoint ---
# =========================================================
@router.post("/api/v1/chat/rag/stream")
async def chat_rag_stream(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Stream LLM responses with RAG retrieval.
    SSE-compatible: each message line starts with 'data:' prefix.
    """
    conversation_id = req.conversation_id or str(uuid.uuid4())
    cleaned_message = normalize_text(req.message)

    # Use the provided prompt or the default one
    if req.rag_prompt:
        current_rag_prompt = PromptTemplate.from_template(req.rag_prompt)
        current_prompt_llm_chain = current_rag_prompt | llm | StrOutputParser()
    else:
        current_prompt_llm_chain = prompt_llm_chain


    async def event_generator():
        try:
            # --- Step 1: Send conversation ID first ---
            yield f"event: conversation_id\ndata: {conversation_id}\n\n"

            # --- Step 2: Retrieve documents ---
            docs = retriever._get_relevant_documents(cleaned_message, run_manager=None)
            if not docs:
                yield "data: I'm sorry, but I couldn't find any relevant information in the documents.\n\n"
                return

            # --- Step 3: Clean and combine context ---
            context = clean_context("\n\n".join([doc.page_content for doc in docs]))

            # --- Step 4: Stream LLM output ---
            buffer = ""
            stream = getattr(current_prompt_llm_chain, "astream", None)

            if callable(stream):
                async for chunk in current_prompt_llm_chain.astream({"context": context, "question": cleaned_message}):
                    raw_text = str(chunk or "")

                    if DEBUG_STREAM_LOGS:
                        logger.info(f"[RAW CHUNK]: {raw_text}")

                    if not raw_text:
                        continue

                    buffer += raw_text
                    # Send when a sentence likely ends
                    if any(buffer.rstrip().endswith(p) for p in [".", "!", "?", ":", ";"]):
                        yield f"data: {normalize_text(buffer)}\n\n"
                        buffer = ""
                        await asyncio.sleep(0.01)
            else:
                # --- Fallback: synchronous LLM ---
                result = current_prompt_llm_chain.invoke({"context": context, "question": cleaned_message})
                cleaned = normalize_text(result)
                if DEBUG_STREAM_LOGS:
                    logger.info(f"[SYNC OUTPUT RAW]: {result}")
                    logger.info(f"[SYNC OUTPUT CLEANED]: {cleaned}")
                yield f"data: {cleaned}\n\n"

            # --- Step 5: Send any remaining text ---
            if buffer:
                yield f"data: {normalize_text(buffer)}\n\n"

        except Exception as e:
            logger.error(f"Error in stream: {e}", exc_info=True)
            yield f"data: Error: {str(e)}\n\n"

    return EventSourceResponse(event_generator())
