import pytest
from unittest.mock import patch, MagicMock
from backend.app.services import ingestion

@patch('backend.app.services.ingestion.PyPDFLoader')
@patch('backend.app.services.ingestion.vector_store')
def test_ingest_pdf_document(mock_vector_store, mock_pdf_loader):
    # Arrange
    mock_loader_instance = MagicMock()
    mock_loader_instance.load.return_value = [MagicMock(page_content="This is a test document.")]
    mock_pdf_loader.return_value = mock_loader_instance
    
    doc_id = "test_doc_1"
    filename = "test.pdf"
    content = b"dummy pdf content"

    # Act
    ingestion.ingest_document(doc_id, filename, content)

    # Assert
    mock_pdf_loader.assert_called_once()
    mock_vector_store.add_documents.assert_called_once()
    
    # Check that the documents added have the correct metadata
    added_docs = mock_vector_store.add_documents.call_args[1]['documents']
    assert len(added_docs) > 0
    assert added_docs[0].metadata['doc_id'] == doc_id
    assert added_docs[0].metadata['source'] == filename
