from unittest.mock import Mock, patch

from botocore.exceptions import ClientError
from django.test import TestCase, override_settings

from common.storage import move_object


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
class StorageMoveRecoveryTests(TestCase):
    @patch("common.storage.boto3.client")
    def test_recovers_when_source_was_deleted_but_destination_exists(
        self, mock_client_factory
    ):
        missing_source = ClientError(
            {
                "Error": {"Code": "NoSuchKey", "Message": "missing"},
                "ResponseMetadata": {"HTTPStatusCode": 404},
            },
            "CopyObject",
        )
        mock_client = Mock()
        mock_client.copy_object.side_effect = missing_source
        mock_client.head_object.return_value = {}
        mock_client_factory.return_value = mock_client

        move_object(
            source_bucket="identitycore-temp",
            source_key="uploads/selfies/upl_RECOVER",
            destination_bucket="identitycore-media",
        )

        mock_client.head_object.assert_called_once_with(
            Bucket="identitycore-media",
            Key="uploads/selfies/upl_RECOVER",
        )
        mock_client.delete_object.assert_not_called()

    @patch("common.storage.boto3.client")
    def test_reraises_when_source_and_destination_are_both_missing(
        self, mock_client_factory
    ):
        def missing(operation):
            return ClientError(
                {
                    "Error": {"Code": "NoSuchKey", "Message": "missing"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                operation,
            )

        mock_client = Mock()
        mock_client.copy_object.side_effect = missing("CopyObject")
        mock_client.head_object.side_effect = missing("HeadObject")
        mock_client_factory.return_value = mock_client

        with self.assertRaises(ClientError):
            move_object(
                source_bucket="identitycore-temp",
                source_key="uploads/selfies/upl_MISSING",
                destination_bucket="identitycore-media",
            )
