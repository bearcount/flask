"""
Flask Instance Configuration Loader

This module demonstrates how to load configuration from instance/instance.json
in a Flask application.

Flask's instance folder is the perfect place to store:
- Database files
- Instance-specific configuration
- Sensitive credentials (not tracked by version control)
- Runtime-generated data

The instance folder path can be configured via:
- FLASK_INSTANCE_PATH environment variable
- Or defaults to <app_root>/instance for regular packages
"""

import json
import os
from pathlib import Path
from typing import Any

import flask


def load_instance_config(app: flask.Flask, config_path: str | None = None) -> dict[str, Any]:
    """
    Load configuration from instance/instance.json file.

    Args:
        app: Flask application instance
        config_path: Optional path to config file. Defaults to instance/instance.json

    Returns:
        Dictionary containing configuration values
    """
    if config_path is None:
        config_path = os.path.join(app.instance_path, "instance.json")

    config_data = {}

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

    return config_data


def init_app(app: flask.Flask) -> None:
    """
    Initialize Flask application with instance configuration.

    Usage:
        from flask import Flask
        from instance.config_loader import init_app

        app = Flask(__name__, instance_relative_config=True)
        init_app(app)
    """
    config_path = os.path.join(app.instance_path, "instance.json")

    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        app.config.update(config_data)

        if app.config.get("DEBUG"):
            print(f"Loaded instance config from: {config_path}")
    else:
        print(f"Warning: No instance config found at {config_path}")


def create_app(config_override: dict[str, Any] | None = None) -> flask.Flask:
    """
    Application factory with instance configuration support.

    Returns:
        Configured Flask application instance
    """
    app = flask.Flask(
        __name__,
        instance_relative_config=True,
        template_folder="templates",
        static_folder="static",
    )

    app.config.from_object("src.flask.default_config")

    init_app(app)

    if config_override:
        app.config.update(config_override)

    if app.config.get("DEBUG"):
        app.config["TEMPLATES_AUTO_RELOAD"] = True

    @app.route("/health")
    def health():
        return {"status": "healthy", "environment": app.config.get("FLASK_ENV", "production")}

    @app.route("/config")
    def show_config():
        safe_config = {
            k: v
            for k, v in app.config.items()
            if not any(secret in k.lower() for secret in ["key", "password", "secret", "token"])
        }
        return flask.jsonify(safe_config)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
