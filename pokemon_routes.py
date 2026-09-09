from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy import text
from pathlib import Path
from uuid import uuid4
import shutil

from database import engine
from schemas import PokemonCreate, PokemonResponse, ImageUploadResponse, DeletePokemonResponse
from stats import calculate_stats
from moves import get_moves_for_pokemon
from auth import get_current_user_id

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.get("/pokemon", response_model=list[PokemonResponse])
def get_pokemon():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM pokemons"))
        rows = result.fetchall()

    return [dict(row._mapping) for row in rows]

@router.get("/my-pokemon", response_model=list[PokemonResponse])
def get_my_pokemon(
    user_id: int = Depends(get_current_user_id)
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT *
                FROM pokemons
                WHERE owner_id = :owner_id
            """),
            {
                "owner_id": user_id
            }
        )

        rows = result.fetchall()

    return [dict(row._mapping) for row in rows]

@router.post("/pokemon", response_model=PokemonResponse)
def create_pokemon(pokemon: PokemonCreate, user_id: int = Depends(get_current_user_id)):
    stats = calculate_stats(pokemon.type, pokemon.level)
    move_names = get_moves_for_pokemon(pokemon.type, pokemon.level)

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                INSERT INTO pokemons (name, type, level, hp, attack, defense, speed, owner_id)
                VALUES (:name, :type, :level, :hp, :attack, :defense, :speed, :owner_id)
                RETURNING *
            """),
            {
                "name": pokemon.name,
                "type": pokemon.type,
                "level": pokemon.level,
                "hp": stats["hp"],
                "attack": stats["attack"],
                "defense": stats["defense"],
                "speed": stats["speed"],
                "owner_id": user_id
            }
        )

        row = result.fetchone()

        pokemon_id = row._mapping["id"]

        for move_name in move_names:
            move_result = connection.execute(
                text("""
                    SELECT id
                    FROM moves
                    WHERE name = :move_name
                """),
                {
                "move_name": move_name
                }
            )

            move_row = move_result.fetchone()

            connection.execute(
                text("""
                    INSERT INTO pokemon_moves (pokemon_id, move_id)
                    VALUES (:pokemon_id, :move_id)
                """),
                {
                    "pokemon_id": pokemon_id,
                    "move_id": move_row._mapping["id"]
                }
            )

    return dict(row._mapping)

@router.post("/pokemon/{pokemon_id}/image", response_model=ImageUploadResponse)
def upload_pokemon_image(
    pokemon_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id)
):
    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WEBP images are allowed"
        )

    file_extension = Path(file.filename).suffix

    unique_filename = f"{uuid4()}{file_extension}"

    file_path = UPLOAD_DIR / unique_filename
    image_url = f"/uploads/{unique_filename}"

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                SELECT id
                FROM pokemons
                WHERE id = :pokemon_id
                AND owner_id = :owner_id
            """),
            {
                "pokemon_id": pokemon_id,
                "owner_id": user_id
            }
        )

        row = result.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Pokemon not found or not owned by current user"
            )

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        connection.execute(
            text("""
                UPDATE pokemons
                SET image_url = :image_url
                WHERE id = :pokemon_id
            """),
            {
                "image_url": image_url,
                "pokemon_id": pokemon_id
            }
        )

    return {
        "message": "Image uploaded",
        "image_url": image_url
    }

@router.get("/pokemon/{pokemon_id}", response_model = PokemonResponse)
def get_pokemon_by_id(pokemon_id: int):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT *
                FROM pokemons
                WHERE id = :pokemon_id
            """),
            {
                "pokemon_id": pokemon_id
            }
        )

        row = result.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Pokemon not found"
            )

        move_result = connection.execute(
            text("""
                SELECT moves.name, moves.power
                FROM moves
                JOIN pokemon_moves
                    ON moves.id = pokemon_moves.move_id
                WHERE pokemon_moves.pokemon_id = :pokemon_id
            """),
            {
                "pokemon_id": pokemon_id
            }
        )

        move_rows = move_result.fetchall()

    pokemon_data = dict(row._mapping)

    pokemon_data["moves"] = [
        dict(move._mapping)
        for move in move_rows
    ]

    return pokemon_data

@router.put("/pokemon/{pokemon_id}", response_model=PokemonResponse)
def update_pokemon(
    pokemon_id: int, pokemon: PokemonCreate, user_id: int = Depends(get_current_user_id)
    ):
    
    stats = calculate_stats(pokemon.type, pokemon.level)

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE pokemons
                SET name = :name,
                type = :type,
                level = :level,
                hp = :hp,
                attack = :attack,
                defense = :defense,
                speed = :speed
                WHERE id = :pokemon_id
                AND owner_id = :owner_id
                RETURNING *
            """),
            {
                "name": pokemon.name,
                "type": pokemon.type,
                "level": pokemon.level,
                "hp": stats["hp"],
                "attack": stats["attack"],
                "defense": stats["defense"],
                "speed": stats["speed"],
                "pokemon_id": pokemon_id,
                "owner_id": user_id
            }
        )

        row = result.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Pokemon not found"
        )

    return dict(row._mapping)

@router.delete("/pokemon/{pokemon_id}", response_model=DeletePokemonResponse)
def delete_pokemon(pokemon_id: int, user_id: int = Depends(get_current_user_id)):
    with engine.begin() as connection:
        result = connection.execute(
            text("""
                DELETE FROM pokemons
                WHERE id = :pokemon_id
                AND owner_id = :owner_id
                RETURNING *
            """),
            {
                "pokemon_id": pokemon_id,
                "owner_id": user_id
            }
        )

        row = result.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Pokemon not found or not owned by current user"
        )

    return {
        "message": "Pokemon deleted",
        "pokemon": dict(row._mapping)
    }