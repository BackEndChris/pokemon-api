from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from database import engine
from schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from auth import create_access_token


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()


@router.post("/register", response_model=UserResponse)
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

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )

    return dict(row._mapping)

@router.post("/login", response_model=TokenResponse)
def login_user(user: UserLogin):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT *
                FROM users
                WHERE username = :username
            """),
            {
                "username": user.username
            }
        )

        row = result.fetchone()

    if row is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not pwd_context.verify(
        user.password,
        row._mapping["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    access_token = create_access_token(row._mapping["id"])

    return {
        "access_token": access_token,
        "token_type": "bearer"
        }
    