"""Convenience entrypoint so `python run_backend.py` just works in VS Code."""
from backend.app import app
from backend.config import settings


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.backend_port, debug=True)
