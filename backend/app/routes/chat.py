import asyncio
import os
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# ----------------------------------------------------------------------
# NEW AGENT API (LangChain 0.2+)
# ----------------------------------------------------------------------
# 1. create_tool_calling_agent stays in langchain.agents
# 2. AgentExecutor is gone – we build an executor with .with_config()
# ----------------------------------------------------------------------
from langchain.agents import create_tool_calling_agent

# Tools (unchanged)
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.retrievers import create_retriever_tool
from langchain.tools import tool

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

from ..schemas.chat import ChatRequest
from ..services.ingestion import vector_store

# Load environment variables from .env file
load_dotenv()

router = APIRouter()

# --- In-memory stores ---
chat_histories = {}
handoff_requests = {}

# --- LLM Configuration ---
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
    elif provider == "deepseek":
        return ChatOpenAI(model="deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com", temperature=0)
    else:
        return ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)

llm = get_llm()

# --- RAG Flow ---
retriever = vector_store.as_retriever()
rag_prompt = PromptTemplate.from_template("Answer based on context:\n{context}\n\nQuestion: {question}")
rag_chain = {"context": retriever, "question": RunnablePassthrough()} | rag_prompt | llm | StrOutputParser()

# --- Agentic Flow ---
@tool
def request_human_handoff(conversation_id: str) -> str:
    """Use this tool ONLY when the user explicitly asks to speak to a human, or you cannot help."""
    handoff_requests[conversation_id] = {"status": "pending"}
    return "A human agent will be with you shortly."

retriever_tool = create_retriever_tool(retriever, "knowledge_base_search", "Search for info in uploaded docs.")
search_tool = DuckDuckGoSearchRun()
tools = [retriever_tool, search_tool, request_human_handoff]

agent_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. If the user wants to speak to a person, use the 'request_human_handoff' tool."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, agent_prompt)
agent_executor = agent.with_config(agent=agent, tools=tools, verbose=True)

# --- API Endpoints ---
async def get_current_user(): return {"username": "testuser"}

@router.post("/api/v1/chat/rag/stream")
async def chat_rag_stream(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    conversation_id = req.conversation_id or str(uuid.uuid4())
    async def event_generator():
        yield "event: conversation_id\ndata: " + conversation_id + "\n\n"
        try:
            for chunk in rag_chain.stream(req.message):
                yield "data: " + chunk.replace('\n', ' ') + "\n\n"
                await asyncio.sleep(0.01)
        except Exception as e:
            yield "data: Error: " + str(e) + "\n\n"
    return EventSourceResponse(event_generator())

@router.post("/api/v1/chat/agent/stream")
async def chat_agent_stream(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    conversation_id = req.conversation_id or str(uuid.uuid4())
    
    if conversation_id in handoff_requests:
        async def handoff_generator():
            yield "event: conversation_id\ndata: " + conversation_id + "\n\n"
            yield "event: handoff_status\ndata: pending\n\n"
            yield "data: A human agent is reviewing this conversation.\n\n"
        return EventSourceResponse(handoff_generator())

    history = chat_histories.get(conversation_id, [])
    
    async def event_generator():
        yield "event: conversation_id\ndata: " + conversation_id + "\n\n"
        full_response = ""
        try:
            async for chunk in agent_executor.astream_log({"input": req.message, "chat_history": history, "conversation_id": conversation_id}):
                if chunk['op'] == 'add' and chunk['path'] == '/logs/P/final_output/streamed_output/-_1':
                    token = chunk['value']
                    full_response += token
                    yield "data: " + token.replace('\n', ' ') + "\n\n"
            
            history.append(HumanMessage(content=req.message))
            history.append(AIMessage(content=full_response))
            chat_histories[conversation_id] = history

            if conversation_id in handoff_requests:
                yield "event: handoff_status\ndata: pending\n\n"

        except Exception as e:
            yield "data: Error: " + str(e) + "\n\n"
            
    return EventSourceResponse(event_generator())