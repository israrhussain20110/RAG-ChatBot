from pydantic import BaseModel

class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    rag_prompt: str | None = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
