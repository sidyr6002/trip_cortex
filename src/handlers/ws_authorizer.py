"""WebSocket Lambda authorizer — validates Clerk JWT on $connect."""

import asyncio
from typing import Any

from core.auth import get_auth_provider
from core.errors import AuthenticationError


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    # AuthProvider methods are async to support future providers with async HTTP clients.
    # ClerkAuthProvider's underlying SDK calls are synchronous, so asyncio.run() bridges
    # the gap in this sync Lambda handler. Overhead is negligible (~1ms).
    try:
        query_params = event.get("queryStringParameters") or {}
        token = query_params["token"]
        auth_provider = get_auth_provider()
        auth_user = asyncio.run(auth_provider.verify_token(token))
        return _allow_policy(event["methodArn"], auth_user.employee_id)
    except (KeyError, AuthenticationError):
        return _deny_policy(event["methodArn"])


def _allow_policy(method_arn: str, employee_id: str) -> dict[str, Any]:
    return {
        "principalId": employee_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": "Allow", "Resource": method_arn}],
        },
        "context": {"employeeId": employee_id},
    }


def _deny_policy(method_arn: str) -> dict[str, Any]:
    return {
        "principalId": "unauthorized",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{"Action": "execute-api:Invoke", "Effect": "Deny", "Resource": method_arn}],
        },
    }
