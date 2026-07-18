"""
Crea la base de datos CineReservas si todavía no existe.
Se conecta primero a 'master' (la BD de sistema que sí existe siempre en
SQL Server), porque no se puede conectar directamente a una BD que aún
no fue creada.
"""
import time

import pyodbc

from src.config import settings


def _master_connection_string() -> str:
    driver = "ODBC Driver 18 for SQL Server"
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={settings.db_host},{settings.db_port};"
        f"DATABASE=master;"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"TrustServerCertificate=yes;"
    )


def ensure_database_exists(retries: int = 10, delay_seconds: int = 3) -> None:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            conn = pyodbc.connect(_master_connection_string(), autocommit=True)
            cursor = conn.cursor()
            cursor.execute(
                f"IF DB_ID('{settings.db_name}') IS NULL "
                f"CREATE DATABASE [{settings.db_name}]"
            )
            conn.close()
            print(f"Base de datos '{settings.db_name}' verificada/creada correctamente.")
            return
        except Exception as exc:  # noqa: BLE001 - reintentamos ante cualquier fallo de conexión
            last_error = exc
            print(f"Intento {attempt}/{retries} fallido al conectar a SQL Server: {exc}")
            time.sleep(delay_seconds)

    raise RuntimeError(
        f"No se pudo crear/verificar la base de datos tras {retries} intentos."
    ) from last_error


if __name__ == "__main__":
    ensure_database_exists()
