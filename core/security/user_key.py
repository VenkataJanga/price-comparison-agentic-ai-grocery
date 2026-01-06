from __future__ import annotations

from fastapi import Request


def get_user_key(request: Request) -> str:
    """
    DEV user key.

    Later replace this with:
    - logged-in user id
    - hashed email
    - device id
    """
    return request.headers.get("X-User-Key") or "local-dev"
