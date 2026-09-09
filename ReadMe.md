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