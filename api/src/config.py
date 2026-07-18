from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
# En Docker, las env vars se inyectan directo vía docker-compose.yml
# (environment:), así que este .env resuelto por path nunca se lee dentro
# del contenedor — es intencional, no un bug. Cualquier variable nueva que
# agregue la app debe sumarse también al environment: del servicio
# correspondiente en docker-compose.yml, o quedará silenciosamente en su
# default de Python dentro de Docker aunque el .env del host la tenga distinta.


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 1433
    db_name: str = "CineReservas"
    db_user: str = "sa"
    db_password: str = ""
    # Consumida por docker-compose para setear MSSQL_SA_PASSWORD del contenedor
    # de SQL Server, no la usa la API. Se declara igual porque extra="forbid"
    # rompería al leer .env si no está mapeada a un campo del modelo.
    db_sa_password: str = ""

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # duración de la sesión del taquillero/admin

    # Tiempo del hold antes de que una reserva "Reservada" expire (S-08).
    # Valor de ejemplo para esta prueba técnica; ver pregunta 2 del análisis.
    reservation_hold_minutes: int = 10

    @property
    def sqlalchemy_database_url(self) -> str:
        driver = "ODBC Driver 18 for SQL Server"
        return (
            f"mssql+pyodbc://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?driver={driver.replace(' ', '+')}"
            f"&TrustServerCertificate=yes"
        )

    class Config:
        env_file = _ENV_FILE


settings = Settings()
