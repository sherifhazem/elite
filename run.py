# -*- coding: utf-8 -*-
"""Entry point for running the ELITE Flask application in development mode."""

from app import create_app

app = create_app()


if __name__ == "__main__":
    print("ELITE backend running...")
    app.run(host="0.0.0.0", port=5000, debug=True)
