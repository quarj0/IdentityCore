from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.uploads.models import UploadStatus
from apps.uploads.services import promote_upload_to_media


class UploadPromotionRecoveryTests(SimpleTestCase):
    @patch("apps.uploads.services._move_upload_to_media_bucket")
    def test_already_promoted_upload_is_not_moved_again(self, mock_move):
        upload = Mock(status=UploadStatus.PROMOTED)

        result = promote_upload_to_media(upload=upload)

        self.assertIs(result, upload)
        mock_move.assert_not_called()
        upload.save.assert_not_called()
