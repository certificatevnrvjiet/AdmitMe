from __future__ import annotations

from io import BytesIO

try:
    import boto3
    from botocore.exceptions import ClientError
except Exception:  # pragma: no cover - runtime dependency gate
    boto3 = None
    ClientError = Exception

from .base import StorageProvider


class S3StorageProvider(StorageProvider):
    name = "s3"

    def __init__(self, bucket: str | None = None, region: str | None = None, endpoint_url: str | None = None):
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url
        self._client = None

        if boto3 and self.bucket:
            self._client = boto3.client("s3", region_name=self.region, endpoint_url=self.endpoint_url)

    def _ensure_client(self):
        if not self.bucket:
            raise RuntimeError("S3_BUCKET is required for S3 storage")
        if boto3 is None:
            raise RuntimeError("boto3 is not installed. Install it before using S3 storage.")
        if not self._client:
            self._client = boto3.client("s3", region_name=self.region, endpoint_url=self.endpoint_url)
        return self._client

    def save(self, key: str, content: bytes, content_type: str | None = None) -> str:
        client = self._ensure_client()
        kwargs = {
            "Bucket": self.bucket,
            "Key": key,
            "Body": content,
        }
        if content_type:
            kwargs["ContentType"] = content_type
        client.put_object(**kwargs)
        return key

    def get_bytes(self, key: str) -> bytes | None:
        client = self._ensure_client()
        try:
            response = client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except ClientError as exc:
            code = (exc.response or {}).get("Error", {}).get("Code")
            if code in {"NoSuchKey", "404", "NotFound"}:
                return None
            raise

    def get_stream(self, key: str):
        payload = self.get_bytes(key)
        if payload is None:
            return None
        return BytesIO(payload)

    def delete(self, key: str) -> bool:
        client = self._ensure_client()
        try:
            client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def exists(self, key: str) -> bool:
        client = self._ensure_client()
        try:
            client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def signed_url(self, key: str, expires_in_seconds: int = 3600) -> str | None:
        client = self._ensure_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in_seconds,
        )
