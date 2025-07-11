import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from typing import BinaryIO, Optional, Dict, Any, List

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

    def get_file(self, user_id: int, file_path: str) -> bytes:
        try:
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

    def list_user_files(self, user_id: int, prefix: str = "") -> List[Dict[str, Any]]:
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
