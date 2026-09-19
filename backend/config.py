"""
Central configuration for the app.
Every other file should import settings from HERE instead of
calling os.getenv() directly all over the codebase.
"""

import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Copy .env.example to .env "
        "and add your Groq API key."
    )

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY is missing. Add a long random string to your .env file, "
        "e.g. SECRET_KEY=your_random_secret_here"
    )