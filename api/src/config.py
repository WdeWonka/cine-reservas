from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 1433
    db_name: str = "CineReservas"
    db_user: str = "sa"
    db_password: str = ""

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
        env_file = ".env"


settings = Settings()
