import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection settings from environment variables or defaults
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ebook_app")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
)

def reset_alembic_version():
    """
    Connects to the database and drops the 'alembic_version' table if it exists.
    """
    if not DATABASE_URL:
        print("Error: DATABASE_URL is not set. Please check your .env file or environment variables.")
        return

    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            print("Successfully connected to the database.")
            
            # Use a transaction to execute the command
            with connection.begin():
                print("Attempting to drop 'alembic_version' table...")
                connection.execute(text("DROP TABLE IF EXISTS alembic_version;"))
                print("'alembic_version' table dropped successfully (if it existed).")

    except ProgrammingError as e:
        # This can happen if the database itself doesn't exist, which is fine.
        if "does not exist" in str(e):
             print(f"Database '{POSTGRES_DB}' might not exist, which is okay for this script.")
        else:
            print(f"A database error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    reset_alembic_version()
