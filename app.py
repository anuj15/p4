import logging
import os

from flask import Flask, session, redirect, url_for

from auth.routes import auth_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev")
app.register_blueprint(auth_bp)

with open("logs/kafka.log", "w") as f:
    f.write("")
logging.info("Kafka log file cleared")


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
