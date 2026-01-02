import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "KommandAI"
    VERSION: str = "1.0.0"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/kommandai"
    )

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")


settings = Settings()
