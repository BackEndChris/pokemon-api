from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Literal

class PokemonCreate(BaseModel):
    name: str = Field(max_length=50)

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value or value.isnumeric():
                raise ValueError("Name must be nonblank and cannot consist only of numbers")
        return value
    type: Literal[
        "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
        "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
        "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy",
    ]
    level: int = Field(default = 1, ge = 1, le = 100)

def validate_password(value):
    try:
        byte_length = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        raise ValueError("Password must contain valid Unicode") from None
    if byte_length > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes")
    if "\x00" in value:
        raise ValueError("Password cannot contain null characters")
    return value


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_][a-zA-Z0-9_.-]*$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        if value.isspace():
            raise ValueError("Password cannot be blank")
        return validate_password(value)

class UserLogin(BaseModel):
    # Keep legacy short usernames/passwords usable; stricter rules apply on registration.
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=72)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        return validate_password(value)

class PokemonResponse(BaseModel):
    id: int
    name: str
    type: str
    level: int
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    owner_id: int | None = None
    image_url: str | None = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str


class MoveResponse(BaseModel):
    name: str
    power: int


class PokemonDetailResponse(PokemonResponse):
    moves: list[MoveResponse]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class ImageUploadResponse(BaseModel):
    message: str
    image_url: str


class DeletePokemonResponse(BaseModel):
    message: str
    pokemon: PokemonResponse
