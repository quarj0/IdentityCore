from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from app.settings import PUBLIC_AI_TOKEN_FINGERPRINT, Settings


@pytest.mark.parametrize("mode", ["mock", "hybrid", "real"])
def test_ai_service_rejects_published_token_on_independent_startup(mode):
    digest = Mock()
    digest.hexdigest.return_value = PUBLIC_AI_TOKEN_FINGERPRINT
    with patch("app.settings.hashlib.sha256", return_value=digest):
        with pytest.raises(ValidationError) as raised:
            Settings(
                AI_SERVICE_MODE=mode, AI_SERVICE_SHARED_TOKEN="fixture-private-value"
            )
    assert "formerly published" in str(raised.value)
    assert "fixture-private-value" not in str(raised.value)


def test_ai_service_accepts_replacement_token():
    assert (
        Settings(AI_SERVICE_SHARED_TOKEN="replacement-fixture-token").shared_token
        == "replacement-fixture-token"
    )
