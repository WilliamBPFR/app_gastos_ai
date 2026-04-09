from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from config import config


class S3Service:
    def __init__(self) -> None:

        self.bucket_name = config.S3_BUCKET_NAME

        self.client = boto3.client(
            "s3",
            endpoint_url=config.S3_ENDPOINT_URL,
            aws_access_key_id=config.S3_ACCESS_KEY_ID,
            aws_secret_access_key=config.S3_ACCESS_KEY_SECRET,
            region_name=config.S3_REGION,
            use_ssl=config.S3_USE_SSL,
            config=BotoConfig(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )

    def upload_file(
        self,
        file_path: str,
        object_name: str,
        content_type: str | None = None,
    ) -> str:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.upload_file(
            Filename=file_path,
            Bucket=self.bucket_name,
            Key=object_name,
            ExtraArgs=extra_args if extra_args else None,
        )
        return object_name

    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        content_type: str | None = None,
    ) -> str:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        file_obj = BytesIO(data)

        self.client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=self.bucket_name,
            Key=object_name,
            ExtraArgs=extra_args if extra_args else None,
        )
        return object_name

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        object_name: str,
        content_type: str | None = None,
    ) -> str:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.upload_fileobj(
            Fileobj=file_obj,
            Bucket=self.bucket_name,
            Key=object_name,
            ExtraArgs=extra_args if extra_args else None,
        )
        return object_name

    def download_file(self, object_name: str, destination_path: str) -> None:
        self.client.download_file(
            Bucket=self.bucket_name,
            Key=object_name,
            Filename=destination_path,
        )

    def get_object_bytes(self, object_name: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket_name, Key=object_name)
        return response["Body"].read()

    def delete_file(self, object_name: str) -> None:
        self.client.delete_object(Bucket=self.bucket_name, Key=object_name)

    def list_files(self, prefix: str = "") -> list[dict]:
        response = self.client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix,
        )

        contents = response.get("Contents", [])
        return [
            {
                "key": item["Key"],
                "size": item["Size"],
                "last_modified": item["LastModified"],
            }
            for item in contents
        ]

    def file_exists(self, object_name: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError:
            return False

    def generate_presigned_url(
        self,
        object_name: str,
        expires_in: int = 3600,
        download: bool = False,
        download_filename: str | None = None,
    ) -> str:
        params = {
            "Bucket": self.bucket_name,
            "Key": object_name,
        }

        if download:
            filename = download_filename or object_name.split("/")[-1]
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            Params=params,
            ExpiresIn=expires_in,
        )

    def generate_presigned_upload_url(
        self,
        object_name: str,
        expires_in: int = 3600,
        content_type: str | None = None,
    ) -> str:
        params = {
            "Bucket": self.bucket_name,
            "Key": object_name,
        }

        if content_type:
            params["ContentType"] = content_type

        return self.client.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=expires_in,
        )
    
s3_service = S3Service()
