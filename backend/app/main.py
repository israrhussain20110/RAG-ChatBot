from fastapi import FastAPI
from .routes import auth, chat, upload
import uvicorn

app = FastAPI(
    title="RAG Bot API",
    description="API for the RAG Bot, powered by FastAPI and LangChain.",
    version="0.1.0",
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(upload.router, tags=["File Management"])

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)