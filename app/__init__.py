# -*- coding: utf-8 -*-
"""Application factory module initializing Flask app, database, Redis, Celery, and routes."""

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery
import redis

from .config import Config

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

redis_client = redis.from_url(app.config["REDIS_URL"])

celery = Celery(app.import_name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)

# Ensure models are registered with SQLAlchemy's metadata for migrations
from .models import Company, Offer, User  # noqa: F401

# Register blueprints after extensions are initialized
from .routes import (  # noqa: E402
    company_routes,
    main as main_blueprint,
    offer_routes,
    user_routes,
)

app.logger.info("✅ Database connection configured for %s", app.config["SQLALCHEMY_DATABASE_URI"])

app.register_blueprint(main_blueprint)
app.register_blueprint(user_routes, url_prefix="/api/users")
app.register_blueprint(company_routes, url_prefix="/api/companies")
app.register_blueprint(offer_routes, url_prefix="/api/offers")
