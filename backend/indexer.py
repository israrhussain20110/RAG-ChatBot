
import os
import uuid
from app.services import ingestion

# The directory containing the documents to be indexed.
# Assumes this script is run from the 'backend' directory.
DOCS_DIR = "../3.0.0"

def index_directory(directory: str):
    """
    Indexes all the .txt, .pdf, and .docx files in a directory.
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            if filename.endswith((".pdf", ".docx", ".txt")):
                with open(file_path, "rb") as f:
                    content = f.read()
                    doc_id = str(uuid.uuid4())
                    print(f"Indexing {filename}...")
                    ingestion.ingest_document(doc_id, filename, content)
            else:
                print(f"Skipping unsupported file type: {filename}")

if __name__ == "__main__":
    index_directory(DOCS_DIR)
