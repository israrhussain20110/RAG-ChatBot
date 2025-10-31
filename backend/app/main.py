from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import chat, upload
import uvicorn

app = FastAPI(
    title="RAG Bot API",
    description="API for the RAG Bot, powered by FastAPI and LangChain.",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # Allow both localhost host variants used by browsers/devtools.
    # If you're still debugging CORS failures, set this to ["*"] temporarily.
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Length"],
    max_age=600,  # Cache preflight requests for 10 minutes
)


app.include_router(chat.router, tags=["Chat"])
app.include_router(upload.router, tags=["File Management"])

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)