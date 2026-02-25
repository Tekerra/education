import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify
from sqlalchemy.exc import OperationalError

from app.config import get_config
from app.extensions import bcrypt, cors, db, jwt, ma, migrate
from app.services.bootstrap_service import bootstrap_demo_data


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    _configure_logging(app)
    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _run_startup_bootstrap(app)

    return app


def _configure_logging(app: Flask) -> None:
    log_level = app.config.get("LOG_LEVEL", "INFO").upper()
    app.logger.setLevel(log_level)
    Path("logs").mkdir(exist_ok=True)
    file_handler = RotatingFileHandler("logs/app.log", maxBytes=2_000_000, backupCount=5)
    file_handler.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        app.logger.addHandler(file_handler)


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    jwt.init_app(app)
    ma.init_app(app)


def _register_blueprints(app: Flask) -> None:
    from app.routes.admin_routes import admin_bp
    from app.routes.advisor_routes import advisor_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.frontend_routes import frontend_bp
    from app.routes.hod_routes import hod_bp
    from app.routes.lecturer_routes import lecturer_bp
    from app.routes.student_routes import student_bp

    app.register_blueprint(frontend_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(hod_bp, url_prefix="/api/hod")
    app.register_blueprint(advisor_bp, url_prefix="/api/advisor")
    app.register_blueprint(lecturer_bp, url_prefix="/api/lecturer")
    app.register_blueprint(student_bp, url_prefix="/api/student")


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(OperationalError)
    def handle_db_error(err):
        app.logger.exception("Database connection error: %s", err)
        return jsonify({"message": "Database unavailable. Ensure PostgreSQL is running and DATABASE_URL is correct."}), 503

    @app.errorhandler(400)
    def handle_400(err):
        return jsonify({"message": "Bad request", "error": str(err)}), 400

    @app.errorhandler(401)
    def handle_401(err):
        return jsonify({"message": "Unauthorized", "error": str(err)}), 401

    @app.errorhandler(403)
    def handle_403(err):
        return jsonify({"message": "Forbidden", "error": str(err)}), 403

    @app.errorhandler(404)
    def handle_404(err):
        return jsonify({"message": "Resource not found", "error": str(err)}), 404

    @app.errorhandler(500)
    def handle_500(err):
        app.logger.exception("Unhandled server error: %s", err)
        return jsonify({"message": "Internal server error"}), 500


def _run_startup_bootstrap(app: Flask) -> None:
    if not app.config.get("AUTO_BOOTSTRAP", True):
        return
    try:
        with app.app_context():
            db.create_all()
            result = bootstrap_demo_data()
            app.logger.info("Startup bootstrap result: %s", result.get("message"))
    except Exception as exc:
        app.logger.exception("Startup bootstrap skipped due to error: %s", exc)
