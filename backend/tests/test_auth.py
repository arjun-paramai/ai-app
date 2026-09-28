from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.auth import current_user, token
from app.config import settings
from app.main import app


def test_valid_and_tampered_token():
    uid = uuid4()
    assert current_user(token(str(uid))) == uid
    with pytest.raises(HTTPException) as exc:
        current_user(token(str(uid)) + "tampered")
    assert exc.value.status_code == 401


def test_expired_token_rejected():
    encoded = jwt.encode({"sub": str(uuid4()), "exp": datetime.now(timezone.utc)-timedelta(seconds=1),
                          "iss": "clausecompass", "aud": "clausecompass-web"}, settings.jwt_secret, algorithm="HS256")
    with pytest.raises(HTTPException):
        current_user(encoded)


def test_auth_and_csrf_boundary():
    with TestClient(app) as client:
        assert client.get("/documents").status_code == 401
        assert client.post("/auth/logout").status_code == 403
        assert client.post("/auth/logout", headers={"X-Requested-With": "ClauseCompass"}).status_code == 204
