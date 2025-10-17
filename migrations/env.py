# -*- coding: utf-8 -*-
"""Alembic environment configuration for Flask-Migrate."""

from __future__ import with_statement

import logging
from logging.config import fileConfig

from alembic import context
from flask import current_app

# Interpret the config file for Python logging.
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# Get the metadata from the current Flask application.
target_metadata = current_app.extensions["migrate"].db.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    connectable = current_app.extensions["migrate"].db.engine

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


def run_migrations() -> None:
    """Determine which migration strategy to execute."""

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


run_migrations()
