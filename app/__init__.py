# -*- coding: utf-8 -*-
"""Application factory module initializing Flask app, database, Redis, Celery, and routes."""

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery
import redis

from .config import Config
from .routes import main as main_blueprint

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

db = SQLAlchemy(app)

# Ensure models are registered with SQLAlchemy's metadata for migrations
from app.models import *  # noqa: F401,F403
migrate = Migrate(app, db)

redis_client = redis.from_url(app.config["REDIS_URL"])

celery = Celery(app.import_name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)

app.logger.info("✅ Database connection configured for %s", app.config["SQLALCHEMY_DATABASE_URI"])

app.register_blueprint(main_blueprint)
