from pydantic import BaseModel, Field
from typing import Literal

class PokemonCreate(BaseModel):
    name: str
    type: Literal[
        "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
        "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
        "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy",
    ]
    level: int = Field(default = 1, ge = 1, le = 100)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

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
