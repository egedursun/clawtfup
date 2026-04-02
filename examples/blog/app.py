import logging
import os

from flask import Flask, session
from flask_wtf.csrf import CSRFProtect

logger = logging.getLogger(__name__)

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder="templates")

    app.config["SECRET_KEY"] = os.environ["BLOG_SECRET_KEY"]
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    from models import db
    from views import bp as posts_bp
    from auth import bp as auth_bp

    db.init_app(app)
    csrf.init_app(app)
    app.register_blueprint(posts_bp)
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_user():
        return {
            "current_user_id": session.get("user_id"),
            "current_username": session.get("username"),
        }

    with app.app_context():
        db.create_all()

    logger.info("Blog app initialized")
    return app


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    create_app().run(debug=debug)
