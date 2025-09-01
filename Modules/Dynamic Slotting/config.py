import os


class Config:
    # Database configuration
    DB_NAME = os.getenv("DB_NAME", "warehouse1_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", 5432)

    # Any other configurations (e.g., Flask secret key)
    SECRET_KEY = 'your_secret_key'
