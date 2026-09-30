import os
import secrets

from fastapi import Header, HTTPException, status


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Require the configured internal API token when one is set.

    Leaving BACKEND_API_TOKEN unset keeps local development friction-free. Set it
    in every deployed environment and send it only from the Next.js server proxy.
    """
    expected_token = os.getenv("BACKEND_API_TOKEN")
    if not expected_token:
        return

    if not x_api_key or not secrets.compare_digest(x_api_key, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
