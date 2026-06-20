"""
DevFlow Agent — Entry Point
Run with: python run.py
"""

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.config import Config

app = create_app()

if __name__ == "__main__":
    print(f"\n🚀 DevFlow Agent backend running on http://localhost:{Config.FLASK_PORT}\n")
    app.run(
        host="0.0.0.0",
        port=Config.FLASK_PORT,
        debug=True
    )
