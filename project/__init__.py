import os
import time
import dotenv
import logging

from pytubefix import YouTube
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request

dotenv.load_dotenv()

db = SQLAlchemy()

LOG_LEVEL = os.getenv("LOG_LEVEL", "NOTSET")

if LOG_LEVEL == "DEBUG":
    log_level = logging.DEBUG
elif LOG_LEVEL == "INFO":
    log_level = logging.INFO
elif LOG_LEVEL == "WARN":
    log_level = logging.WARN
elif LOG_LEVEL == "ERROR":
    log_level = logging.ERROR
elif LOG_LEVEL == "FATAL":
    log_level = logging.FATAL
else:
    log_level = logging.NOTSET

logging.basicConfig(
    filename="/app/logs/karatuben.log",
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create a logger
logger = logging.getLogger(__name__)

def create_app():
    
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.urandom(24).hex()

    db_user = os.environ.get("MYSQL_USER", "root")
    db_pass = os.environ.get("MYSQL_ROOT_PASSWORD")
    db_host = os.environ.get("MYSQL_HOST")
    db_port = os.environ.get("MYSQL_PORT", "3306")
    db_name = os.environ.get("MYSQL_DATABASE", "karatube")
    db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    
    db.init_app(app)
    
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app
