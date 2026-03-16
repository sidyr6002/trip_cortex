"""Re-orientation and retry-with-wait recovery helpers for Nova Act workflows."""


import structlog

log = structlog.get_logger()


def reorient(nova: object, original_goal: str, search_url: str) -> bool:
    """Navigate back to the search URL and re-attempt the original goal.

    Must be called inside an active NovaAct context manager.
    Returns True if recovery succeeded, False otherwise.
    """
    try:
        nova.act(f"Navigate to {search_url}", max_steps=10)  # type: ignore[attr-defined]
        nova.act(original_goal, max_steps=20)  # type: ignore[attr-defined]
        log.info("nova_act_reorient_success", search_url=search_url)
        return True
    except Exception as exc:
        log.warning("nova_act_reorient_failed", error=str(exc))
        return False


def should_retry(elapsed_ms: float, wait_seconds: float, budget_ms: float = 300_000) -> bool:
    """Return True if there is enough budget remaining to wait and retry.

    Requires at least 60 s of headroom after the wait to be worth retrying.
    """
    return elapsed_ms + (wait_seconds * 1_000) + 60_000 < budget_ms
