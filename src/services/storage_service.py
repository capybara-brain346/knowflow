import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from typing import BinaryIO, Optional, Dict, Any

from src.core.config import settings
from src.services.auth_service import AuthService


class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    def _get_user_prefixed_key(self, user_id: int, file_key: str) -> str:
        user_prefix = f"user_{user_id}/"
        clean_file_key = file_key.lstrip("/")
        return f"{user_prefix}{clean_file_key}"

    def upload_file(
        self,
        user_id: int,
        file_key: str,
        file_obj: BinaryIO,
        content_type: Optional[str] = None,
    ) -> str:
        s3_key = self._get_user_prefixed_key(user_id, file_key)
        return self.upload_file_obj(s3_key, file_obj, content_type)

    def upload_file_obj(
        self,
        file_key: str,
        file_obj: BinaryIO,
        content_type: Optional[str] = None,
    ) -> str:
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.s3_client.upload_fileobj(
                file_obj, self.bucket_name, file_key, ExtraArgs=extra_args
            )
            return file_key
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}",
            )

    def download_file(self, file_key: str) -> BinaryIO:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            return response["Body"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download file: {str(e)}",
            )

    def get_user_file(self, user_id: int, file_key: str) -> BinaryIO:
        s3_key = self._get_user_prefixed_key(user_id, file_key)
        return self.download_file(s3_key)

    def delete_file(self, user_id: int, file_key: str) -> None:
        s3_key = self._get_user_prefixed_key(user_id, file_key)
        self._delete_file_obj(s3_key)

    def _delete_file_obj(self, file_key: str) -> None:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}",
            )

    def list_files(self, user_id: Optional[int] = None, prefix: str = "") -> list:
        try:
            if user_id is not None:
                prefix = self._get_user_prefixed_key(user_id, prefix)

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )

            files = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    key = obj["Key"]
                    if user_id is not None:
                        user_prefix = f"user_{user_id}/"
                        key = (
                            key[len(user_prefix) :]
                            if key.startswith(user_prefix)
                            else key
                        )

                    if key:
                        files.append(
                            {
                                "key": key,
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

    def get_file_metadata(self, file_key: str) -> Dict[str, Any]:
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return {
                "ContentType": response.get("ContentType"),
                "ContentLength": response.get("ContentLength"),
                "LastModified": response.get("LastModified"),
                "Metadata": response.get("Metadata", {}),
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get file metadata: {str(e)}",
            )
