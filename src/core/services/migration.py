"""Run Alembic migrations programmatically — invoked via MigrateFunction Lambda."""

import io
import json
import logging
import os

import boto3
from alembic.config import Config

from alembic import command

logger = logging.getLogger(__name__)


def _load_credentials_from_secret(secret_arn: str) -> None:
    """Fetch Aurora credentials from Secrets Manager and set env vars."""
    sm = boto3.client("secretsmanager", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    secret = json.loads(sm.get_secret_value(SecretId=secret_arn)["SecretString"])
    os.environ["AURORA_USER"] = secret.get("username", "tripcortex")
    os.environ["AURORA_PASSWORD"] = secret.get("password", "")
    os.environ["AURORA_HOST"] = secret.get("host", os.environ.get("AURORA_HOST", ""))
    os.environ["AURORA_PORT"] = str(secret.get("port", 5432))
    os.environ["AURORA_DATABASE"] = secret.get("dbname", os.environ.get("AURORA_DATABASE", "tripcortex"))


def run_migrations() -> dict[str, str]:
    secret_arn = os.environ.get("AURORA_SECRET_ARN")
    if secret_arn:
        _load_credentials_from_secret(secret_arn)

    cfg = Config("/var/task/alembic.ini")
    cfg.set_main_option("script_location", "/var/task/alembic")

    stderr_buf = io.StringIO()
    try:
        import logging

        handler = logging.StreamHandler(stderr_buf)
        logging.getLogger("alembic").addHandler(handler)
        command.upgrade(cfg, "head")
        logging.getLogger("alembic").removeHandler(handler)
        output = stderr_buf.getvalue()
        logger.info("Migration complete: %s", output)
        return {"status": "success", "output": output}
    except Exception as e:
        logger.error("Migration failed: %s", e)
        return {"status": "error", "error": str(e), "output": stderr_buf.getvalue()}
