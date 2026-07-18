from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Import de la app: settings y modelos ---
import sys
import os

sys.path.append(os.getcwd())  # asegura que "src" sea importable al correr desde api/

from src.config import settings
from src.db.session import Base
from src.models import *  # noqa: F401,F403 — importa todas las clases de modelo
                           # para que queden registradas en Base.metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Sobrescribe la URL de conexión del alembic.ini con la de settings,
# para no duplicar la configuración de conexión en dos lugares.
config.set_main_option("sqlalchemy.url", settings.sqlalchemy_database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata: necesario para que --autogenerate compare tus modelos
# contra el estado real de la base de datos.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
