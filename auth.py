from datetime import datetime, timedelta, timezone
import re

from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text

from config import SECRET_KEY
from database import engine

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer(auto_error=False)


def unauthorized():
    return HTTPException(401, "Invalid or expired authentication credentials", headers={"WWW-Authenticate": "Bearer"})


def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"require_exp": True, "require_sub": True})
        subject = payload.get("sub")
        if not isinstance(subject, str) or not re.fullmatch(r"[1-9][0-9]{0,9}", subject):
            raise unauthorized()
        user_id = int(subject)
        if user_id > 2147483647:
            raise unauthorized()
        return user_id
    except (JWTError, ValueError, TypeError):
        raise unauthorized() from None


def get_current_user_id(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()
    user_id = decode_access_token(credentials.credentials)
    with engine.connect() as connection:
        exists = connection.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id}).scalar_one_or_none()
    if exists is None:
        raise unauthorized()
    return user_id
