import asyncio
import os
import psycopg
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
# Credentials for your local PostgreSQL instance.
# They are loaded from the .env file for security.
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
HF_TOKEN = os.getenv("HF_TOKEN")


# A good general-purpose model from Hugging Face is 'all-MiniLM-L6-v2',
# which produces vectors with 384 dimensions.
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


async def setup_database():
    """
    Connects to the database, enables the vector extension,
    and creates the 'documents' table tailored for Hugging Face embeddings.
    """
    conn = None
    try:
        # Check if the password was loaded correctly
        if not DB_PASSWORD:
            print("❌ DATABASE_PASSWORD not found in environment variables.")
            return

        # Establish the connection using a connection string
        conn_string = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
        conn = await psycopg.AsyncConnection.connect(conn_string)
        print("✅ Successfully connected to the database.")

        async with conn.cursor() as cur:
            # NOTE: The 'vector' extension should be enabled once by a superuser.
            # Example: `sudo -u postgres psql -d rag_db -c 'CREATE EXTENSION IF NOT EXISTS vector;'`
            
            # 1. Drop the existing table for a clean setup (optional, but for dev)
            print("ℹ️  Dropping 'documents' table if it exists...")
            await cur.execute("DROP TABLE IF EXISTS documents;")

            # 2. Create the 'documents' table with the correct vector dimension
            print(f"✅ Creating 'documents' table with embedding dimension {EMBEDDING_DIMENSION} for model {EMBEDDING_MODEL_NAME}...")
            await cur.execute(f"""
                CREATE TABLE documents (
                    id BIGSERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    embedding VECTOR({EMBEDDING_DIMENSION})
                );
            """)
            
            await conn.commit()
            print("✅ Database setup complete. The 'documents' table is ready for Hugging Face embeddings.")

    except psycopg.OperationalError as e:
        print(f"❌ DATABASE CONNECTION FAILED: Please check your credentials and ensure PostgreSQL is running.")
        print(f"   Error details: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        if conn:
            await conn.close()
            print("🔌 Database connection closed.")


if __name__ == "__main__":
    # Run the asynchronous setup function
    asyncio.run(setup_database())
