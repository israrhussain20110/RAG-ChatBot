from pydantic import BaseModel

class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    user_id: str

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
