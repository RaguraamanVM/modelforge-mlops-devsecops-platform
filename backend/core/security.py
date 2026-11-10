import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def require_api_key(api_key: str | None = Security(api_key_header)):
    expected_key = os.getenv("MODELFORGE_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


admin_key_header = APIKeyHeader(
    name="X-Admin-Key",
    auto_error=False,
)


def require_admin_key(admin_key: str | None = Security(admin_key_header)):
    expected_key = os.getenv("MODELFORGE_ADMIN_KEY")
    regular_key = os.getenv("MODELFORGE_API_KEY")

    if not expected_key or expected_key == regular_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrator authentication is not securely configured",
        )

    if not admin_key or not secrets.compare_digest(admin_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing administrator key",
        )
