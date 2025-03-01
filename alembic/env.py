import os
from dotenv import load_dotenv
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.models import Base


load_dotenv()

# Alembic Config object
config = context.config

db_url = os.getenv("POSTGRES_DATABASE_URL")
if not db_url:
    raise RuntimeError("POSTGRES_DATABASE_URL not set in the environment!")


config.set_main_option("sqlalchemy.url", db_url)
target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Create an engine from the configuration
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Configure the context with the connection and the metadata
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
