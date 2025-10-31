from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
import tempfile
import re
import asyncio

# In a real app, these would be configured
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
VECTORSTORE_PATH = "./vectorstore"

# Create embedding function
_embedding_function = None
_vector_store_instance = None

def get_embedding_function():
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embedding_function

def get_vector_store():
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = Chroma(
            persist_directory=VECTORSTORE_PATH,
            embedding_function=get_embedding_function()
        )
    return _vector_store_instance

async def ingest_document(doc_id: str, filename: str, content: bytes):
    """
    Ingests a document into the vector store.
    1. Detects file type and loads document.
    2. Chunks the document.
    3. Embeds and stores the chunks in ChromaDB.
    """
    print(f"Starting ingestion for doc_id: {doc_id}, filename: {filename}")

    try:
        # Save content to a temporary file to use with loaders
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # 1. Load document based on file type
        loader = None
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(tmp_file_path)
        elif filename.endswith(".docx"):
            loader = Docx2txtLoader(tmp_file_path)
        elif filename.endswith(".txt"):
            loader = TextLoader(tmp_file_path)
        else:
            print(f"Unsupported file type: {filename}")
            os.remove(tmp_file_path)
            return

        documents = loader.load()
        print(f"Loaded {len(documents)} document(s).")

        for doc in documents:
            doc.page_content = re.sub(r'\s+', ' ', doc.page_content)

        # 2. Chunk the document
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        print(f"Split document into {len(chunks)} chunks.")



        # Add metadata to chunks
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "doc_id": doc_id,
                "source": filename,
            })
        
        # 3. Embed and store chunks
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: get_vector_store().add_documents(documents=chunks, ids=[f"{doc_id}-{i}" for i, _ in enumerate(chunks)]))
        await loop.run_in_executor(None, lambda: get_vector_store().persist())

        print(f"Successfully ingested document {doc_id} into vector store.")

    except Exception as e:
        print(f"Error during ingestion for doc_id {doc_id}: {e}")
    finally:
        # Clean up the temporary file
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
