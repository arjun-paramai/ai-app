from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Cookie, HTTPException
import jwt
from pwdlib import PasswordHash

from .config import settings

passwords = PasswordHash.recommended()


def token(user_id: str) -> str:
    return jwt.encode({"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(hours=8),
                       "iss": "clausecompass", "aud": "clausecompass-web"}, settings.jwt_secret, algorithm="HS256")


def current_user(session: str | None = Cookie(default=None)) -> UUID:
    try:
        data = jwt.decode(session or "", settings.jwt_secret, algorithms=["HS256"],
                          issuer="clausecompass", audience="clausecompass-web",
                          options={"require": ["sub", "exp", "iss", "aud"]})
        return UUID(data["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(401, "Sign in to continue.")
