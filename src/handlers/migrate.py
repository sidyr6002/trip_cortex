from core.services.migration import run_migrations


def handler(event, context):  # type: ignore[no-untyped-def]
    return run_migrations()
