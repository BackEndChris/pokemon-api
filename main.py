from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes import router as root_router
from auth_routes import router as auth_router
from pokemon_routes import router as pokemon_router

app = FastAPI()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(root_router)
app.include_router(auth_router)
app.include_router(pokemon_router)