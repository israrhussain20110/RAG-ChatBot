# RAG Bot: A Retrieval-Augmented Generation Agent

This project is a complete Retrieval-Augmented Generation (RAG) bot built with a modern tech stack. It features a FastAPI backend, a React frontend, and a modular architecture that allows for configurable AI models and extensible agent capabilities.

## Features

- **Dual Chat Modes**: Switch between a simple RAG mode for direct document-based answers and a powerful Agent mode with tool-using capabilities.
- **Knowledge Ingestion**: Upload documents (.pdf, .docx, .txt) to a persistent vector store, making them available to the bot as a knowledge base.
- **Configurable LLMs**: Easily switch between different language model providers (OpenAI, Google Gemini, DeepSeek) via a simple configuration file.
- **Conversational Memory**: The agent remembers previous turns in the conversation for a natural, follow-up dialogue.
- **Tool-Using Agent**: The agent can use tools to augment its knowledge, including a web search tool and a tool to search the local knowledge base.
- **Human Handoff**: A mechanism for the bot to flag a conversation for human intervention, and for the user to request a human agent.
- **Streaming Responses**: The bot's responses are streamed to the UI token-by-token for a real-time, responsive user experience.
- **Containerized**: The entire application is containerized with Docker, allowing for easy setup and deployment.
- **Testing & CI**: The project includes a testing suite with `pytest` and a GitHub Actions workflow for continuous integration.

## Tech Stack

- **Backend**: FastAPI, Python, LangChain
- **Frontend**: React, Tailwind CSS
- **Vector Store**: ChromaDB
- **Containerization**: Docker, Docker Compose
- **Testing**: Pytest
- **CI/CD**: GitHub Actions

## Project Structure

/RAG_BOT
├── .github/workflows/ci.yml   # CI/CD pipeline
├── backend/                   # FastAPI application
│   ├── app/                   # Core application logic
│   ├── tests/                 # Backend tests
│   └── Dockerfile             # Backend Dockerfile
├── frontend/                  # React application
│   ├── src/                   # Frontend source code
│   └── Dockerfile             # Frontend Dockerfile
├── vectorstore/               # Persistent vector store data
├── .env                       # Environment variables
├── docker-compose.yml         # Docker Compose configuration
├── README.md                  # This file
└── requirements.txt           # Python dependencies

## Prerequisites

- Python 3.10+
- Node.js and npm
- Docker and Docker Compose

## Configuration

Before running the application, you need to configure your API keys and select an LLM provider.

1. Rename the `.env.example` file to `.env` (or create a new `.env` file).
2. Edit the `.env` file:

    ```ini
    LLM_PROVIDER="openai" # Options    langchain-community>=0.0.21: "openai", "gemini", "deepseek"

    # Add your API keys here
    OPENAI_API_KEY="your_openai_api_key_here"
    GOOGLE_API_KEY="your_google_api_key_here"
    DEEPSEEK_API_KEY="your_deepseek_api_key_here"
    ```

## Running the Project

You can run the project in two ways: using Docker (recommended for ease of use) or by running the frontend and backend separately for local development.

### With Docker (Recommended)

From the project root directory, run:

```sh
docker-compose up --build
```

- The frontend will be available at `http://localhost:3000`.
- The backend API will be available at `http://localhost:8000`.

### Local Development

**1. Run the Backend:**

```sh
# From the project root

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
cd backend
uvicorn app.main:app --reload
```

**2. Run the Frontend:**

In a separate terminal:

```sh
# From the project root

cd frontend

# Install dependencies
npm install

# Run the development server
npm start
```

## API Endpoints

The main API endpoints are served by the FastAPI backend:

- `POST /api/v1/upload`: Upload a document for ingestion.
- `POST /api/v1/chat/rag/stream`: Start a streaming chat session in RAG mode.
- `POST /api/v1/chat/agent/stream`: Start a streaming chat session in Agent mode.

## Running Tests

To run the backend tests, execute the following command from the project root directory:

```sh
pytest
```
