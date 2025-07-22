import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError
from fastapi import HTTPException
from src.services.s3_service import S3Service


@pytest.fixture
def s3_service(mock_s3_client):
    with patch("src.services.s3_service.boto3.client", return_value=mock_s3_client):
        service = S3Service()
        service.s3_client = mock_s3_client
        return service


def test_get_user_path(s3_service):
    user_path = s3_service._get_user_path(123)
    assert user_path == "users/123"


def test_upload_file_success(s3_service):
    file_data = b"test content"
    file_path = "documents/test.pdf"
    content_type = "application/pdf"
    user_id = 123

    full_path = s3_service.upload_file(
        user_id=user_id,
        file_path=file_path,
        file_data=file_data,
        content_type=content_type,
    )

    s3_service.s3_client.put_object.assert_called_once_with(
        Bucket=s3_service.bucket_name,
        Key=f"users/{user_id}/{file_path}",
        Body=file_data,
        ContentType=content_type,
    )
    assert full_path == f"users/{user_id}/{file_path}"


def test_upload_file_without_content_type(s3_service):
    file_data = b"test content"
    file_path = "documents/test.txt"
    user_id = 123

    s3_service.upload_file(user_id=user_id, file_path=file_path, file_data=file_data)

    s3_service.s3_client.put_object.assert_called_once_with(
        Bucket=s3_service.bucket_name,
        Key=f"users/{user_id}/{file_path}",
        Body=file_data,
    )


def test_upload_file_error(s3_service):
    s3_service.s3_client.put_object.side_effect = ClientError(
        {"Error": {"Code": "InternalError", "Message": "S3 Error"}}, "PutObject"
    )

    with pytest.raises(HTTPException) as exc_info:
        s3_service.upload_file(123, "test.txt", b"content")
    assert exc_info.value.status_code == 500
    assert "Failed to upload file" in str(exc_info.value.detail)


def test_upload_files_batch_success(s3_service):
    files = [
        {
            "file_path": "test1.txt",
            "file_data": b"content1",
            "content_type": "text/plain",
        },
        {
            "file_path": "test2.pdf",
            "file_data": b"content2",
            "content_type": "application/pdf",
        },
    ]

    results = s3_service.upload_files_batch(123, files)

    assert len(results) == 2
    assert all(result["status"] == "success" for result in results)
    assert s3_service.s3_client.put_object.call_count == 2


def test_upload_files_batch_partial_failure(s3_service):
    def mock_upload(*args, **kwargs):
        if "test1.txt" in kwargs.get("Key", ""):
            raise ClientError(
                {"Error": {"Code": "InternalError", "Message": "S3 Error"}}, "PutObject"
            )

    s3_service.s3_client.put_object.side_effect = mock_upload

    files = [
        {"file_path": "test1.txt", "file_data": b"content1"},
        {"file_path": "test2.txt", "file_data": b"content2"},
    ]

    results = s3_service.upload_files_batch(123, files)

    assert len(results) == 2
    assert any(result["status"] == "failed" for result in results)
    assert any(result["status"] == "success" for result in results)


def test_get_file_success(s3_service):
    s3_service.s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: b"file content")
    }

    content = s3_service.get_file(123, "test.txt")
    assert content == b"file content"

    s3_service.s3_client.get_object.assert_called_once_with(
        Bucket=s3_service.bucket_name, Key="users/123/test.txt"
    )


def test_get_file_not_found(s3_service):
    s3_service.s3_client.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
    )

    with pytest.raises(HTTPException) as exc_info:
        s3_service.get_file(123, "nonexistent.txt")
    assert exc_info.value.status_code == 404
    assert "File not found" in str(exc_info.value.detail)


def test_get_file_error(s3_service):
    s3_service.s3_client.get_object.side_effect = ClientError(
        {"Error": {"Code": "InternalError", "Message": "S3 Error"}}, "GetObject"
    )

    with pytest.raises(HTTPException) as exc_info:
        s3_service.get_file(123, "test.txt")
    assert exc_info.value.status_code == 500
    assert "Failed to download file" in str(exc_info.value.detail)


def test_get_file_unauthorized_access(s3_service):
    with pytest.raises(HTTPException) as exc_info:
        s3_service.get_file(123, "test.txt", requesting_user_id=456)
    assert exc_info.value.status_code == 403
    assert "Access denied" in str(exc_info.value.detail)


def test_list_user_files_success(s3_service):
    mock_response = {
        "Contents": [
            {"Key": "users/123/file1.txt", "Size": 100, "LastModified": datetime.now()},
            {"Key": "users/123/file2.pdf", "Size": 200, "LastModified": datetime.now()},
        ]
    }
    s3_service.s3_client.list_objects_v2.return_value = mock_response

    files = s3_service.list_user_files(123, requesting_user_id=123)

    assert len(files) == 2
    assert all("path" in f and "size" in f and "last_modified" in f for f in files)
    assert any(f["path"] == "file1.txt" for f in files)
    assert any(f["path"] == "file2.pdf" for f in files)


def test_list_user_files_empty(s3_service):
    s3_service.s3_client.list_objects_v2.return_value = {}

    files = s3_service.list_user_files(123, requesting_user_id=123)
    assert len(files) == 0


def test_list_user_files_unauthorized(s3_service):
    with pytest.raises(HTTPException) as exc_info:
        s3_service.list_user_files(123, requesting_user_id=456)
    assert exc_info.value.status_code == 403
    assert "Access denied" in str(exc_info.value.detail)


def test_list_user_files_error(s3_service):
    s3_service.s3_client.list_objects_v2.side_effect = ClientError(
        {"Error": {"Code": "InternalError", "Message": "S3 Error"}}, "ListObjectsV2"
    )

    with pytest.raises(HTTPException) as exc_info:
        s3_service.list_user_files(123, requesting_user_id=123)
    assert exc_info.value.status_code == 500
    assert "Failed to list files" in str(exc_info.value.detail)
