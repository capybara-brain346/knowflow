import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from typing import BinaryIO, Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from src.core.config import settings


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.max_workers = 5  # Limit concurrent uploads

    def _get_user_path(self, user_id: int) -> str:
        return f"users/{user_id}"

    def upload_file(
        self,
        user_id: int,
        file_path: str,
        file_data: bytes,
        content_type: Optional[str] = None,
    ) -> str:
        try:
            full_path = f"{self._get_user_path(user_id)}/{file_path.lstrip('/')}"
            extra_args = {"ContentType": content_type} if content_type else {}

            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=full_path, Body=file_data, **extra_args
            )
            return full_path
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}",
            )

    def upload_files_batch(
        self,
        user_id: int,
        files: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for file in files:
                future = executor.submit(
                    self.upload_file,
                    user_id=user_id,
                    file_path=file["file_path"],
                    file_data=file["file_data"],
                    content_type=file.get("content_type"),
                )
                futures.append((file, future))

            for file, future in futures:
                try:
                    result = future.result()
                    results.append(
                        {
                            "file_path": file["file_path"],
                            "status": "success",
                            "full_path": result,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "file_path": file["file_path"],
                            "status": "failed",
                            "error": str(e),
                        }
                    )

        return results

    def get_file(
        self, user_id: int, file_path: str, requesting_user_id: Optional[int] = None
    ) -> bytes:
        try:
            if requesting_user_id is not None:
                if file_path.startswith("documents/"):
                    doc_id = file_path.split("/")[1].split(".")[0]
                    self.auth_service.verify_document_access_through_chunks(
                        requesting_user_id, doc_id
                    )
                else:
                    if user_id != requesting_user_id:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied to this file",
                        )

            full_path = f"{self._get_user_path(user_id)}/{file_path.lstrip('/')}"
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=full_path)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download file: {str(e)}",
            )

    def list_user_files(
        self, user_id: int, prefix: str = "", requesting_user_id: int = None
    ) -> List[Dict[str, Any]]:
        if requesting_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this user's files",
            )
        try:
            full_prefix = f"{self._get_user_path(user_id)}/{prefix.lstrip('/')}"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=full_prefix
            )

            files = []
            if "Contents" in response:
                base_path_length = len(self._get_user_path(user_id)) + 1
                for obj in response["Contents"]:
                    relative_path = obj["Key"][base_path_length:]
                    if relative_path:
                        files.append(
                            {
                                "path": relative_path,
                                "size": obj["Size"],
                                "last_modified": obj["LastModified"].isoformat(),
                            }
                        )
            return files
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list files: {str(e)}",
            )
