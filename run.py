import asyncio
import json
import os
import threading
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError

from models import db
from routes.auth import auth_bp
from routes.measurements import measurements_bp
from routes.recommendations import recommendations_bp
from services.websocket_hub import websocket_hub

load_dotenv()


def _env_flag(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def create_app():
    app = Flask(__name__)
    debug_mode = _env_flag("FLASK_DEBUG", True)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["JWT_SECRET"] = os.environ.get("JWT_SECRET", "jwt-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///metabolic_stability.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
    app.config["WEBSOCKET_HOST"] = os.environ.get("WEBSOCKET_HOST", "127.0.0.1")
    app.config["WEBSOCKET_PORT"] = int(os.environ.get("WEBSOCKET_PORT", "8765"))
    app.config["DEBUG"] = debug_mode
    app.config["AUTO_INIT_DB"] = _env_flag("AUTO_INIT_DB", True)

    if not debug_mode:
        if app.config["SECRET_KEY"] == "dev-secret-key" or app.config["JWT_SECRET"] == "jwt-secret-key":
            raise RuntimeError("Production secrets must be set via SECRET_KEY and JWT_SECRET.")

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "static", "css"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "static", "js"), exist_ok=True)

    db.init_app(app)
    Migrate(app, db)
    allowed_origins = os.environ.get("CORS_ORIGINS", "*")
    CORS(
        app,
        supports_credentials=True,
        resources={r"/api/*": {"origins": [origin.strip() for origin in allowed_origins.split(",")] if allowed_origins != "*" else "*"}},
    )

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(measurements_bp, url_prefix="/api")
    app.register_blueprint(recommendations_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return render_template("login.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html", websocket_port=app.config["WEBSOCKET_PORT"])

    @app.route("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory("static", filename)

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory("static", "favicon.ico")

    @app.route("/uploads/<path:filename>")
    def uploaded_files(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "websocket_port": app.config["WEBSOCKET_PORT"],
        }

    @app.errorhandler(413)
    def payload_too_large(_error):
        return jsonify({"error": "Uploaded file exceeds the 10 MB limit"}), 413

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(_error):
        db.session.rollback()
        return jsonify({"error": "Database operation failed"}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        if app.config["DEBUG"]:
            raise error
        return jsonify({"error": "Internal server error"}), 500

    return app


def start_websocket_server(app):
    async def websocket_handler(websocket, path):
        user_id = None
        try:
            parts = [part for part in path.split("/") if part]
            if len(parts) < 3 or parts[0] != "ws" or parts[1] != "monitor":
                await websocket.send(
                    json.dumps({"type": "error", "message": "Invalid websocket path"})
                )
                return

            user_id = int(parts[2])
            await websocket_hub.register(user_id, websocket)
            await websocket.send(
                json.dumps(
                    {
                        "type": "connected",
                        "userId": user_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            )

            async for message in websocket:
                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    await websocket.send(
                        json.dumps({"type": "error", "message": "Invalid JSON"})
                    )
                    continue

                if payload.get("type") == "request_update":
                    cached = websocket_hub.get_latest_snapshot(user_id)
                    if cached:
                        await websocket.send(json.dumps(cached))
                    else:
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "heartbeat",
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            )
                        )
        finally:
            if user_id is not None:
                await websocket_hub.unregister(user_id, websocket)

    async def run_server():
        import websockets
        import socket
        
        # Try to find an available port starting from the configured one
        host = app.config["WEBSOCKET_HOST"]
        base_port = app.config["WEBSOCKET_PORT"]
        
        for port_offset in range(10):  # Try up to 10 different ports
            try_port = base_port + port_offset
            try:
                # Test if port is available
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((host, try_port))
                
                # Port is available, try to start the server
                async with websockets.serve(
                    websocket_handler,
                    host,
                    try_port,
                ):
                    print(f"WebSocket server running on {host}:{try_port}")
                    # Update the app config with the actual port
                    app.config["WEBSOCKET_PORT"] = try_port
                    await asyncio.Future()
                    return
            except (OSError, socket.error):
                continue  # Try next port
            except Exception as e:
                print(f"WebSocket server error: {e}")
                return
        
        print("Could not find an available port for WebSocket server")

    loop = asyncio.new_event_loop()

    def runner():
        asyncio.set_event_loop(loop)
        websocket_hub.set_loop(loop)
        try:
            loop.run_until_complete(run_server())
        except Exception as e:
            print(f"WebSocket runner error: {e}")

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        if app.config["AUTO_INIT_DB"]:
            db.create_all()
    start_websocket_server(app)
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=5000)
