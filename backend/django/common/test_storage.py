from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from common.storage import (
    build_signed_download_url,
    build_signed_upload_url,
    determine_storage_provider,
)


class StorageHelpersTests(SimpleTestCase):
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
    def test_s3_compatible_storage_generates_presigned_urls(self, mock_client_factory):
        mock_client = Mock()
        mock_client.generate_presigned_url.side_effect = [
            "https://r2.example/upload",
            "https://r2.example/download",
        ]
        mock_client_factory.return_value = mock_client

        upload_url = build_signed_upload_url(
            storage_key="uploads/documents/upl_01TEST",
            mime_type="image/jpeg",
        )
        download_url = build_signed_download_url(
            storage_key="uploads/documents/upl_01TEST",
            filename="front.jpg",
        )

        self.assertEqual(upload_url, "https://r2.example/upload")
        self.assertEqual(download_url, "https://r2.example/download")
        self.assertEqual(determine_storage_provider(), "cloudflare_r2")
        self.assertEqual(mock_client.generate_presigned_url.call_count, 2)
