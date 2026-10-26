from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from error_handlers import install_error_handlers
from request_limits import RequestSizeLimit

from routes import router as root_router
from auth_routes import router as auth_router
from pokemon_routes import router as pokemon_router

app = FastAPI()
install_error_handlers(app)
app.add_middleware(RequestSizeLimit)

app.mount("/uploads", StaticFiles(directory="uploads", check_dir=False), name="uploads")

app.include_router(root_router)
app.include_router(auth_router)
app.include_router(pokemon_router)
