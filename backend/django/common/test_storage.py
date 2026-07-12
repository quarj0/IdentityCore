from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from common.crypto import (
    decrypt_object_bytes,
    encrypt_object_bytes,
    is_encrypted_object_payload,
)
from common.storage import (
    build_signed_download_url,
    build_signed_upload_url,
    build_public_asset_url,
    determine_storage_provider,
    get_object_bytes,
    get_object_storage_temp_bucket_name,
    move_object,
    put_object_bytes,
)


class StorageHelpersTests(TestCase):
    @override_settings(
        UPLOAD_URL_BASE="http://localhost:9000/mock-upload",
        MEDIA_DOWNLOAD_URL_BASE="http://localhost:9000/mock-download",
        MEDIA_DOWNLOAD_URL_EXPIRES_SECONDS=300,
    )
    def test_fallback_signed_urls_use_placeholder_bases(self):
        upload_url = build_signed_upload_url(
            storage_key="uploads/documents/upl_01TEST",
            mime_type="image/jpeg",
        )
        download_url = build_signed_download_url(
            storage_key="uploads/documents/upl_01TEST",
            filename="front.jpg",
        )

        self.assertIn("mock-upload/uploads/documents/upl_01TEST", upload_url)
        self.assertIn("content_type=image%2Fjpeg", upload_url)
        self.assertIn("mock-download/uploads/documents/upl_01TEST", download_url)
        self.assertIn("filename=front.jpg", download_url)

    @override_settings(
        PUBLIC_ASSET_URL_BASE="https://assets.example.com/public",
    )
    def test_public_asset_urls_use_public_base(self):
        self.assertEqual(
            build_public_asset_url("organizations/org_01TEST/logo.png"),
            "https://assets.example.com/public/organizations/org_01TEST/logo.png",
        )

    @override_settings(
        OBJECT_STORAGE_MEDIA_BUCKET="identitycore-media",
        OBJECT_STORAGE_TEMP_BUCKET="",
    )
    def test_temp_bucket_falls_back_to_media_bucket(self):
        self.assertEqual(get_object_storage_temp_bucket_name(), "identitycore-media")

    @override_settings(
        OBJECT_STORAGE_PROVIDER="cloudflare_r2",
        OBJECT_STORAGE_BUCKET="identitycore-media",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        OBJECT_STORAGE_REGION="auto",
        OBJECT_STORAGE_SIGNATURE_VERSION="s3v4",
        OBJECT_STORAGE_PRESIGNED_UPLOAD_EXPIRES_SECONDS=600,
        MEDIA_DOWNLOAD_URL_EXPIRES_SECONDS=300,
    )
    @patch("common.storage.boto3.client")
    def test_s3_compatible_storage_generates_presigned_urls(
        self, mock_client_factory
    ):
        mock_client = Mock()
        mock_client.generate_presigned_url.side_effect = [
            "https://r2.example/upload",
            "https://r2.example/download",
        ]
        mock_client_factory.return_value = mock_client

        upload_url = build_signed_upload_url(
            storage_key="uploads/documents/upl_01TEST",
            mime_type="image/jpeg",
            bucket_name="identitycore-temp",
        )
        download_url = build_signed_download_url(
            storage_key="uploads/documents/upl_01TEST",
            filename="front.jpg",
            bucket_name="identitycore-media",
        )

        self.assertEqual(upload_url, "https://r2.example/upload")
        self.assertEqual(download_url, "https://r2.example/download")
        self.assertEqual(mock_client.generate_presigned_url.call_count, 2)
        self.assertEqual(
            mock_client.generate_presigned_url.call_args_list[0].kwargs["Params"][
                "ServerSideEncryption"
            ],
            "AES256",
        )

    @override_settings(
        OBJECT_STORAGE_PROVIDER="cloudflare_r2",
        OBJECT_STORAGE_BUCKET="identitycore-media",
        OBJECT_STORAGE_TEMP_BUCKET="identitycore-temp",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        OBJECT_STORAGE_REGION="auto",
        OBJECT_STORAGE_SIGNATURE_VERSION="s3v4",
        OBJECT_STORAGE_PRESIGNED_UPLOAD_EXPIRES_SECONDS=600,
    )
    @patch("common.storage.boto3.client")
    def test_signed_upload_url_uses_temp_bucket_when_configured(
        self, mock_client_factory
    ):
        mock_client = Mock()
        mock_client.generate_presigned_url.return_value = "https://r2.example/upload"
        mock_client_factory.return_value = mock_client

        upload_url = build_signed_upload_url(
            storage_key="uploads/documents/upl_02TEST",
            mime_type="image/png",
            bucket_name="identitycore-temp",
        )

        self.assertEqual(upload_url, "https://r2.example/upload")
        self.assertEqual(mock_client.generate_presigned_url.call_count, 1)
        self.assertEqual(
            mock_client.generate_presigned_url.call_args.kwargs["Params"]["Bucket"],
            "identitycore-temp",
        )

    @override_settings(
        OBJECT_STORAGE_PROVIDER="cloudflare_r2",
        OBJECT_STORAGE_BUCKET="identitycore-media",
        OBJECT_STORAGE_TEMP_BUCKET="identitycore-temp",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        OBJECT_STORAGE_REGION="auto",
        OBJECT_STORAGE_SIGNATURE_VERSION="s3v4",
    )
    @patch("common.storage.boto3.client")
    def test_move_object_moves_and_deletes_source(self, mock_client_factory):
        mock_client = Mock()
        mock_client.copy_object.return_value = {}
        mock_client.delete_object.return_value = {}
        mock_client_factory.return_value = mock_client

        move_object(
            source_bucket="identitycore-temp",
            source_key="uploads/documents/upl_03TEST",
            destination_bucket="identitycore-media",
        )

        mock_client.copy_object.assert_called_once_with(
            CopySource={
                "Bucket": "identitycore-temp",
                "Key": "uploads/documents/upl_03TEST",
            },
            Bucket="identitycore-media",
            Key="uploads/documents/upl_03TEST",
            ServerSideEncryption="AES256",
        )
        mock_client.delete_object.assert_called_once_with(
            Bucket="identitycore-temp",
            Key="uploads/documents/upl_03TEST",
        )

    @override_settings(
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        OBJECT_STORAGE_SERVER_SIDE_ENCRYPTION="AES256",
    )
    @patch("common.storage.boto3.client")
    def test_put_object_bytes_can_encrypt_payloads(self, mock_client_factory):
        mock_client = Mock()
        mock_client_factory.return_value = mock_client

        put_object_bytes(
            bucket_name="identitycore-evidence",
            key="organizations/org_1/reports/report.json",
            content=b'{"status":"verified"}',
            content_type="application/json",
            encrypt=True,
            encryption_purpose="evidence.reports",
        )

        body = mock_client.put_object.call_args.kwargs["Body"]
        self.assertTrue(is_encrypted_object_payload(body))
        decrypted, content_type = decrypt_object_bytes(
            payload=body,
            purpose="evidence.reports",
        )
        self.assertEqual(decrypted, b'{"status":"verified"}')
        self.assertEqual(content_type, "application/json")

    @override_settings(
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
    )
    @patch("common.storage.boto3.client")
    def test_get_object_bytes_can_decrypt_encrypted_payloads(self, mock_client_factory):
        encrypted_payload = encrypt_object_bytes(
            content=b"pdf-bytes",
            content_type="application/pdf",
            purpose="evidence.reports",
        )
        mock_client = Mock()
        mock_client.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=encrypted_payload)),
            "ContentType": "application/vnd.identitycore.encrypted+json",
        }
        mock_client_factory.return_value = mock_client

        content, content_type = get_object_bytes(
            bucket_name="identitycore-evidence",
            key="organizations/org_1/reports/report.pdf",
            decrypt=True,
            encryption_purpose="evidence.reports",
        )

        self.assertEqual(content, b"pdf-bytes")
        self.assertEqual(content_type, "application/pdf")
