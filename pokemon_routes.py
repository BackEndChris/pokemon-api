from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, Request
from sqlalchemy import text
from pathlib import Path
from uuid import uuid4
import logging
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from rate_limits import upload_limit
from image_storage import verified_image, cleanup_image

from database import engine
from schemas import PokemonCreate, PokemonResponse, PokemonDetailResponse, ImageUploadResponse, DeletePokemonResponse
from stats import calculate_stats
from moves import get_moves_for_pokemon
from auth import get_current_user_id

router = APIRouter()

UPLOAD_DIR = Path("uploads")
logger = logging.getLogger(__name__)


def save_pokemon_moves(connection, pokemon_id: int, move_names):
    for move_name in move_names:
        try:
            move_id = connection.execute(
                text("""
                    SELECT moves.id FROM moves
                    JOIN pokemons ON pokemons.type = moves.type
                    WHERE moves.name = :name AND pokemons.id = :pokemon_id
                """),
                {"name": move_name, "pokemon_id": pokemon_id},
            ).scalar_one()
        except (NoResultFound, MultipleResultsFound):
            logger.error("Move catalogue is missing or inconsistent")
            raise HTTPException(503, "Move catalogue unavailable; contact the administrator") from None
        connection.execute(
            text("""
                INSERT INTO pokemon_moves (pokemon_id, move_id)
                VALUES (:pokemon_id, :move_id)
                ON CONFLICT (pokemon_id, move_id) DO NOTHING
            """),
            {"pokemon_id": pokemon_id, "move_id": move_id},
        )

@router.get("/pokemon", response_model=list[PokemonResponse])
def get_pokemon(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=100000)):
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM pokemons ORDER BY id LIMIT :limit OFFSET :offset"), {"limit": limit, "offset": offset})
        rows = result.fetchall()

    return [dict(row._mapping) for row in rows]

@router.get("/my-pokemon", response_model=list[PokemonResponse])
def get_my_pokemon(
    user_id: int = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT *
                FROM pokemons
                WHERE owner_id = :owner_id
                ORDER BY id LIMIT :limit OFFSET :offset
            """),
            {
                "owner_id": user_id, "limit": limit, "offset": offset
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
                INSERT INTO pokemons (
                    name, type, level, hp, attack, defense,
                    special_attack, special_defense, speed, owner_id
                )
                VALUES (
                    :name, :type, :level, :hp, :attack, :defense,
                    :special_attack, :special_defense, :speed, :owner_id
                )
                RETURNING *
            """),
            {
                "name": pokemon.name,
                "type": pokemon.type,
                "level": pokemon.level,
                "hp": stats["hp"],
                "attack": stats["attack"],
                "defense": stats["defense"],
                "special_attack": stats["special_attack"],
                "special_defense": stats["special_defense"],
                "speed": stats["speed"],
                "owner_id": user_id
            }
        )

        row = result.fetchone()

        pokemon_id = row._mapping["id"]

        save_pokemon_moves(connection, pokemon_id, move_names)

    return dict(row._mapping)

@router.post("/pokemon/{pokemon_id}/image", response_model=ImageUploadResponse)
def upload_pokemon_image(
    pokemon_id: int,
    request: Request,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
):
    upload_limit(request, user_id)
    image_url = None
    file_created = False
    committed = False
    try:
        with engine.begin() as connection:
            row = connection.execute(text("""
                SELECT image_url FROM pokemons
                WHERE id = :id AND owner_id = :owner_id FOR UPDATE
            """), {"id": pokemon_id, "owner_id": user_id}).fetchone()
            if row is None:
                raise HTTPException(404, "Pokemon not found or not owned by current user")
            old_image_url = row._mapping["image_url"]
            data, extension = verified_image(file)
            filename = f"{uuid4()}{extension}"
            image_url = f"/uploads/{filename}"
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            with (UPLOAD_DIR / filename).open("xb") as output:
                file_created = True
                output.write(data)
            connection.execute(text("""
                UPDATE pokemons SET image_url = :image_url WHERE id = :id
            """), {"image_url": image_url, "id": pokemon_id})
        committed = True
    except OSError as error:
        logger.error("Image storage operation failed (%s)", type(error).__name__)
        raise HTTPException(503, "Image storage temporarily unavailable") from None
    finally:
        if not committed and file_created:
            cleanup_image(image_url, UPLOAD_DIR)
    cleanup_image(old_image_url, UPLOAD_DIR)
    return {"message": "Image uploaded", "image_url": image_url}

@router.get("/pokemon/{pokemon_id}", response_model=PokemonDetailResponse)
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
                ORDER BY moves.id
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
    
    with engine.begin() as connection:
        current = connection.execute(
            text("""
                SELECT type, level FROM pokemons
                WHERE id = :pokemon_id AND owner_id = :owner_id
                FOR UPDATE
            """),
            {"pokemon_id": pokemon_id, "owner_id": user_id},
        ).fetchone()

        if current is None:
            raise HTTPException(status_code=404, detail="Pokemon not found")
        if pokemon.type != current._mapping["type"]:
            raise HTTPException(status_code=400, detail="Pokemon type cannot be changed")
        if pokemon.level < current._mapping["level"]:
            raise HTTPException(status_code=400, detail="Pokemon level cannot be lowered")

        if pokemon.level > current._mapping["level"]:
            known_moves = connection.execute(
                text("""
                    SELECT moves.name FROM moves
                    JOIN pokemon_moves ON pokemon_moves.move_id = moves.id
                    WHERE pokemon_moves.pokemon_id = :pokemon_id
                """),
                {"pokemon_id": pokemon_id},
            ).scalars().all()
            move_names = get_moves_for_pokemon(
                pokemon.type, pokemon.level,
                previous_level=current._mapping["level"], known_moves=known_moves,
            )
            save_pokemon_moves(connection, pokemon_id, move_names)

        result = connection.execute(
            text("""
                UPDATE pokemons
                SET name = :name,
                level = :level,
                hp = hp + (:level - level) * 3,
                attack = attack + (:level - level) * 2,
                defense = defense + (:level - level) * 2,
                special_attack = special_attack + (:level - level) * 2,
                special_defense = special_defense + (:level - level) * 2,
                speed = speed + (:level - level) * 2
                WHERE id = :pokemon_id
                AND owner_id = :owner_id
                RETURNING *
            """),
            {
                "name": pokemon.name,
                "level": pokemon.level,
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

    cleanup_image(row._mapping["image_url"], UPLOAD_DIR)
    return {
        "message": "Pokemon deleted",
        "pokemon": dict(row._mapping)
    }
