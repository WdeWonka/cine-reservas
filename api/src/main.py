from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Cine Reservas API",
    description="Módulo interno de gestión de reservas de asientos",
    version="0.1.0",
)

# Ajustar en producción a los orígenes reales del frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Los routers (auth, funciones, reservas, reporte) se registran aquí
# conforme se vayan implementando:
# from src.routers import auth, functions, reservations, reports
# app.include_router(auth.router)
# app.include_router(functions.router)
# app.include_router(reservations.router)
# app.include_router(reports.router)
