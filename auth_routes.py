from fastapi import APIRouter, HTTPException, Depends, Request
import logging
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from database import engine
from schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from auth import create_access_token
from rate_limits import registration_limit, login_source_limit, login_account_limit


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=True)
DUMMY_HASH = pwd_context.hash("dummy-password-for-timing")
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserResponse, dependencies=[Depends(registration_limit)])
def register_user(user: UserCreate):
    password_hash = pwd_context.hash(user.password)

    try:
        with engine.begin() as connection:
            result = connection.execute(
                text("""
                    INSERT INTO users (username, email, password_hash)
                    VALUES (:username, :email, :password_hash)
                    RETURNING id, username, email
                """),
                {
                    "username": user.username,
                    "email": user.email,
                    "password_hash": password_hash
                }
            )

            row = result.fetchone()

    except IntegrityError as error:
        if getattr(error.orig, "pgcode", None) != "23505":
            raise
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )

    return dict(row._mapping)

@router.post("/login", response_model=TokenResponse, dependencies=[Depends(login_source_limit)])
def login_user(user: UserLogin, request: Request):
    login_account_limit(request, user.username)
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT *
                FROM users
                WHERE lower(username) = lower(:username)
            """),
            {
                "username": user.username
            }
        )

        row = result.fetchone()

    stored_hash = row._mapping["password_hash"] if row is not None else DUMMY_HASH
    try:
        matches = pwd_context.verify(user.password, stored_hash)
    except (ValueError, TypeError):
        logger.error("Invalid stored password hash encountered")
        matches = False
    if row is None or not matches:
        raise HTTPException(status_code=401, detail="Invalid username or password", headers={"WWW-Authenticate": "Bearer"})

    access_token = create_access_token(row._mapping["id"])

    return {
        "access_token": access_token,
        "token_type": "bearer"
        }
    