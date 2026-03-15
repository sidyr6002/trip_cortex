"""Nova Act workflow configuration and factory helpers."""

import fnmatch
from urllib.parse import urlparse

from nova_act import GuardrailDecision, GuardrailInputState

ALLOWED_DOMAINS = ["localhost", "*.dportal.workers.dev"]


def portal_url_guardrail(state: GuardrailInputState) -> GuardrailDecision:
    hostname = urlparse(state.browser_url).hostname
    if not hostname:
        return GuardrailDecision.BLOCK
    if any(fnmatch.fnmatch(hostname, p) for p in ALLOWED_DOMAINS):
        return GuardrailDecision.PASS
    return GuardrailDecision.BLOCK


def nova_act_kwargs(portal_url: str, headless: bool = True) -> dict:
    """Return NovaAct constructor kwargs for the dummy portal."""
    import shutil

    kwargs: dict = {
        "starting_page": portal_url,
        "headless": headless,
        "tty": False,
        "state_guardrail": portal_url_guardrail,
    }
    # Use system Chrome locally; ACR container only has Playwright Chromium
    if shutil.which("google-chrome") or shutil.which("google-chrome-stable"):
        kwargs["chrome_channel"] = "chrome"
    return kwargs


def workflow_kwargs(workflow_definition_name: str) -> dict:
    """Return Workflow context manager kwargs for IAM auth."""
    import os

    boto_kwargs: dict = {"region_name": "us-east-1"}
    profile = os.environ.get("AWS_PROFILE")
    if profile:
        boto_kwargs["profile_name"] = profile
    return {
        "workflow_definition_name": workflow_definition_name,
        "model_id": "nova-act-latest",
        "boto_session_kwargs": boto_kwargs,
    }
