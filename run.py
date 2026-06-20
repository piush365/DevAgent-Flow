"""
DevFlow Agent — Entry Point
Run with: python run.py

For production use gunicorn instead:
    gunicorn --config gunicorn.conf.py "run:app"
"""

from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.config import Config

# Validate required configuration before starting the server.
# Raises EnvironmentError with clear instructions if GROQ_API_KEY is missing.
Config.validate()

app = create_app()

if __name__ == "__main__":
    print(f"\n🚀  DevFlow Agent backend → http://localhost:{Config.FLASK_PORT}")
    print("    Frontend command:  streamlit run frontend/streamlit_app.py\n")
    app.run(
        host="127.0.0.1",   # localhost only; use 0.0.0.0 only inside Docker
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG,
    )
