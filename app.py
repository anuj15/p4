import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from flask import Flask, session, redirect, url_for

from auth.routes import auth_bp

file_handler = RotatingFileHandler("logs/kafka.log", maxBytes=10240, backupCount=3)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]"
))

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev")
app.register_blueprint(auth_bp)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info("App startup.")


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
