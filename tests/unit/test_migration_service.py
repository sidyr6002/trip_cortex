from unittest.mock import patch

import pytest

from core.services.migration import run_migrations


@patch("core.services.migration.command")
@patch("core.services.migration._load_credentials_from_secret")
def test_run_migrations_success(mock_creds, mock_command):
    with patch.dict("os.environ", {"AURORA_SECRET_ARN": ""}):
        with patch("core.services.migration.Config"):
            result = run_migrations()
            assert result["status"] == "success"


@patch("core.services.migration.command")
def test_run_migrations_raises_on_failure(mock_command):
    mock_command.upgrade.side_effect = Exception("connection refused")
    with patch.dict("os.environ", {"AURORA_SECRET_ARN": ""}):
        with patch("core.services.migration.Config"):
            with pytest.raises(Exception, match="connection refused"):
                run_migrations()
