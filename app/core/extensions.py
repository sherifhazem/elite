from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail
from celery import Celery

login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
mail = Mail()
celery = Celery()
