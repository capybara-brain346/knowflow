import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import io
from fastapi import UploadFile, HTTPException
from src.services.document_service import DocumentService
from src.models.database import Document, DocumentStatus, User
from src.core.exceptions import ExternalServiceException


@pytest.fixture
def document_service(
    db_session, mock_llm, mock_embeddings, mock_neo4j_driver, test_user
):
    with (
        patch(
            "src.services.document_service.ChatGoogleGenerativeAI",
            return_value=mock_llm,
        ),
        patch(
            "src.services.document_service.GoogleGenerativeAIEmbeddings",
            return_value=mock_embeddings,
        ),
        patch(
            "src.services.document_service.GraphDatabase.driver",
            return_value=mock_neo4j_driver,
        ),
        patch("src.services.document_service.PGVector") as mock_pgvector,
        patch("src.services.document_service.S3Service") as mock_s3,
    ):
        mock_pgvector.return_value = MagicMock()
        mock_s3.return_value = MagicMock()
        service = DocumentService(db_session, test_user)
        return service


@pytest.fixture
def sample_pdf_file():
    return UploadFile(
        filename="test.pdf",
        file=io.BytesIO(b"PDF content"),
        content_type="application/pdf",
    )


@pytest.fixture
def sample_docx_file():
    return UploadFile(
        filename="test.docx",
        file=io.BytesIO(b"DOCX content"),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@pytest.mark.asyncio
async def test_upload_documents_success(document_service, sample_pdf_file):
    result = await document_service.upload_documents([sample_pdf_file])

    assert len(result) == 1
    assert result[0]["title"] == "test.pdf"
    assert result[0]["status"] == "success"

    # Verify document was created in database
    doc = (
        document_service.db.query(Document).filter(Document.title == "test.pdf").first()
    )
    assert doc is not None
    assert doc.status == DocumentStatus.PROCESSING


@pytest.mark.asyncio
async def test_upload_documents_unsupported_type(document_service):
    unsupported_file = UploadFile(
        filename="test.xyz", file=io.BytesIO(b"content"), content_type="application/xyz"
    )

    with pytest.raises(HTTPException) as exc_info:
        await document_service.upload_documents([unsupported_file])
    assert exc_info.value.status_code == 400
    assert "Unsupported file type" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_upload_documents_storage_error(document_service, sample_pdf_file):
    # Mock storage service to raise an error
    document_service.storage_service.upload_file.side_effect = Exception(
        "Storage error"
    )

    result = await document_service.upload_documents([sample_pdf_file])
    assert result[0]["status"] == "failed"
    assert "Failed to upload document" in result[0]["message"]

    # Verify document status was updated to FAILED
    doc = (
        document_service.db.query(Document).filter(Document.title == "test.pdf").first()
    )
    assert doc.status == DocumentStatus.FAILED


@pytest.mark.asyncio
async def test_index_document_success(document_service, test_document):
    # Mock successful document processing
    document_service.storage_service.get_file.return_value = b"Document content"
    document_service.text_splitter.split_text.return_value = ["chunk1", "chunk2"]
    document_service.embeddings.embed_documents.return_value = [
        [0.1] * 768,
        [0.2] * 768,
    ]

    result = await document_service.index_document(test_document.doc_id)

    assert result["doc_id"] == test_document.doc_id
    assert result["status"] == "INDEXED"
    assert result["chunks_count"] == 2

    # Verify document was updated in database
    doc = (
        document_service.db.query(Document)
        .filter(Document.doc_id == test_document.doc_id)
        .first()
    )
    assert doc.status == DocumentStatus.INDEXED


@pytest.mark.asyncio
async def test_index_document_already_indexed(document_service, test_document):
    test_document.status = DocumentStatus.INDEXED
    document_service.db.commit()

    result = await document_service.index_document(test_document.doc_id)
    assert result["message"] == "Document already indexed"


@pytest.mark.asyncio
async def test_index_document_not_found(document_service):
    with pytest.raises(HTTPException) as exc_info:
        await document_service.index_document("nonexistent")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_index_document_unauthorized(document_service, test_document):
    # Change document user_id
    test_document.user_id = 999
    document_service.db.commit()

    with pytest.raises(HTTPException) as exc_info:
        await document_service.index_document(test_document.doc_id)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_index_document_processing_error(document_service, test_document):
    document_service.storage_service.get_file.side_effect = Exception(
        "Processing error"
    )

    with pytest.raises(HTTPException) as exc_info:
        await document_service.index_document(test_document.doc_id)
    assert exc_info.value.status_code == 500

    # Verify document status was updated to FAILED
    doc = (
        document_service.db.query(Document)
        .filter(Document.doc_id == test_document.doc_id)
        .first()
    )
    assert doc.status == DocumentStatus.FAILED


@pytest.mark.asyncio
async def test_list_documents(document_service, test_document):
    documents = await document_service.list_documents()
    assert len(documents) == 1
    assert documents[0].doc_id == test_document.doc_id


@pytest.mark.asyncio
async def test_list_documents_with_status(document_service, test_document):
    documents = await document_service.list_documents(document_status="PENDING")
    assert len(documents) == 1
    assert all(doc.status == DocumentStatus.PENDING for doc in documents)


@pytest.mark.asyncio
async def test_list_documents_invalid_status(document_service):
    with pytest.raises(HTTPException) as exc_info:
        await document_service.list_documents(document_status="INVALID")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_document(document_service, test_document):
    doc = await document_service.get_document(test_document.doc_id)
    assert doc.doc_id == test_document.doc_id


@pytest.mark.asyncio
async def test_get_document_not_found(document_service):
    with pytest.raises(HTTPException) as exc_info:
        await document_service.get_document("nonexistent")
    assert exc_info.value.status_code == 404


def test_get_document_loader(document_service):
    # Test PDF loader
    loader = document_service._get_document_loader("test.pdf", "application/pdf")
    assert "PyMuPDFLoader" in str(type(loader))

    # Test DOCX loader
    loader = document_service._get_document_loader(
        "test.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert "Docx2txtLoader" in str(type(loader))

    # Test CSV loader
    loader = document_service._get_document_loader("test.csv", "text/csv")
    assert "CSVLoader" in str(type(loader))

    # Test TXT loader
    loader = document_service._get_document_loader("test.txt", "text/plain")
    assert "TextLoader" in str(type(loader))

    # Test fallback loader
    loader = document_service._get_document_loader("test.other", "application/other")
    assert "UnstructuredFileLoader" in str(type(loader))
