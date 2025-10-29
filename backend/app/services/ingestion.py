from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
import os
import tempfile

# In a real app, these would be configured
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
VECTORSTORE_PATH = "./vectorstore"

# Create embedding function
embedding_function = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_NAME)

# Get ChromaDB client
# In a real app, you'd have a singleton or a dependency-injected client.
vector_store = Chroma(
    persist_directory=VECTORSTORE_PATH,
    embedding_function=embedding_function
)

def ingest_document(doc_id: str, filename: str, content: bytes):
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
        vector_store.add_documents(documents=chunks, ids=[f"{doc_id}-{i}" for i, _ in enumerate(chunks)])
        vector_store.persist()

        print(f"Successfully ingested document {doc_id} into vector store.")

    except Exception as e:
        print(f"Error during ingestion for doc_id {doc_id}: {e}")
    finally:
        # Clean up the temporary file
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
