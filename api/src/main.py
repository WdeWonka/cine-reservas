from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.exceptions import AppError
from src.routers import auth, movie_functions, movies, reservations, rooms, tickets

app = FastAPI(
    title="Cine Reservas API",
    description="Módulo interno de gestión de reservas de asientos",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(movie_functions.router)
app.include_router(movies.router)
app.include_router(reservations.router)
app.include_router(rooms.router)
app.include_router(tickets.router)

# Los siguientes routers se registran conforme se vayan implementando:
# from src.routers import reports
# app.include_router(reports.router)
