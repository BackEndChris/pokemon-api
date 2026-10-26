# Pokémon API

A backend portfolio project built with FastAPI and PostgreSQL.

The API allows users to register, log in, create Pokémon-style creatures, automatically calculate stats and moves, upload images, and manage only the Pokémon they own.

## Features

- User registration and login
- Password hashing with bcrypt
- JWT authentication
- Pokémon CRUD operations
- Ownership-based authorization
- Automatic stat calculation
- Automatic move assignment
- Image uploads
- PostgreSQL database
- Alembic database migrations
- Swagger/OpenAPI documentation

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- Alembic
- JWT
- bcrypt

## Project Structure

```text
Pokemon API/
├── alembic/
│   └── versions/
├── uploads/
├── auth.py
├── auth_routes.py
├── database.py
├── main.py
├── moves.py
├── pokemon_routes.py
├── routes.py
├── schemas.py
├── stats.py
├── requirements.txt
├── alembic.ini
├── .gitignore
└── README.md
```

## Pokemon stats

All 18 types are supported: Normal, Fire, Water, Electric, Grass, Ice,
Fighting, Poison, Ground, Flying, Psychic, Bug, Rock, Ghost, Dragon,
Dark, Steel, and Fairy. Type names are case-sensitive.

Each type has a custom six-stat archetype totaling 360 base points:
HP, attack, defense, special attack, special defense, and speed.
These are simplified rules for this project, rather than official species stats.

On creation, each stat independently receives a random integer from -4 to +4:

```text
hp = type base + variation + level * 3
other stats = type base + variation + level * 2
```

The resulting stats are stored in PostgreSQL. Reading or renaming a Pokemon
does not reroll them. Level increases add the corresponding growth,
preserving its original variation. Levels cannot be lowered.
A Pokemon's type cannot be changed;
PUT requests must still include its current type.

## Learning moves

Each of the 18 types has eight moves defined in `moves.py` (144 moves total):

| Move | Available from | Chance per gained level |
| --- | --- | --- |
| Starter | Level 1 | Guaranteed |
| Additional move | Level 5 | 20% |
| Second move | Level 10 | 20% |
| Additional move | Level 15 | 15% |
| Third move | Level 25 | 10% |
| Additional move | Level 35 | 10% |
| Additional move | Level 50 | 8% |
| Additional move | Level 65 | 5% |

These learning levels and probabilities are custom rules for this project.
A missed move gets another independent chance on the next gained level.
Eligible moves roll independently, so multiple moves can be learned together.
There is no learned-move limit, and a move cannot be learned twice.
Pokemon learn only moves of their own type: Water Pokemon cannot learn Fire
or Electric moves. Both the learning pool and database lookup enforce this.

Creating a Pokemon at a higher level processes learning from level 1 through
that level. Updating from level 10 to 15 processes all five gained levels.
Reading a Pokemon or editing its name at the same level never rerolls moves.
Levels cannot be lowered, which prevents replaying earlier learning chances.

Move records live in `moves`; learned moves are saved in `pokemon_moves`.
`GET /pokemon/{pokemon_id}` returns a `moves` list containing names and powers.
Creation, update, and list responses retain their existing stat-only shape.
Move powers are stored for future use; no battle mechanics are implemented.

## Database migrations

Apply migrations before starting the updated API:

```powershell
python -m alembic upgrade head
```

The special-stats migration adds `special_attack` and `special_defense`.
For existing Pokemon, it fills these using the type base plus `level * 2`,
without randomness, and preserves the four existing stats.

The following move-catalogue migration seeds all 54 moves, preserving existing
move records and learned assignments. Existing Pokemon receive any missing
starter move, without rerolling their past levels. Their next level increase
begins rolling for eligible, unlearned moves.

The next migration adds five more moves per type (90 additional records),
bringing the catalogue to 144. It preserves existing Pokemon and learned moves;
the new moves become eligible on future level gains without rerolling past levels.

The test database needs the same migrations. To explicitly select `.env.test`:

```powershell
python -c "from dotenv import load_dotenv; load_dotenv('.env.test', override=True); from alembic.config import Config; from alembic import command; command.upgrade(Config('alembic.ini'), 'head')"
python -m pytest -q
```
