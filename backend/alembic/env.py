from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from database import Base, DATABASE_URL
from models.ml_model import MLModel


# Alembic configuration
config = context.config


# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Register SQLAlchemy models
target_metadata = Base.metadata


# Configure PostgreSQL connection
config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL.render_as_string(
        hide_password=False
    ).replace("%", "%%"),
)


def run_migrations_offline():
    """
    Run migrations without an active database connection.
    """

    context.configure(
        url=DATABASE_URL.render_as_string(
            hide_password=False
        ),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """
    Run migrations using an active database connection.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section, {}
        ),
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
