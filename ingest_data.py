import asyncio
import os
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Json
from pgvector.psycopg import register_vector_async
from sentence_transformers import SentenceTransformer

# Load environment variables from a .env file
load_dotenv()

# --- Configuration ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# --- Sample Data ---
# Let's create some sample documents to ingest.
documents_to_ingest = [
    {
        "content": "The sky is blue. It is a beautiful day to go for a walk in the park.",
        "metadata": {"source": "nature_observations.txt", "page": 1}
    },
    {
        "content": "Artificial intelligence is transforming industries, from healthcare to finance.",
        "metadata": {"source": "tech_trends_report.pdf", "chapter": 3}
    },
    {
        "content": "The PostgreSQL database is a powerful open-source object-relational database system.",
        "metadata": {"source": "postgres_docs.html", "section": "intro"}
    },
    {
        "content": "Vector embeddings represent text in a high-dimensional space, capturing semantic meaning.",
        "metadata": {"source": "ml_concepts.md", "topic": "embeddings"}
    }
]

async def ingest_data():
    """
    Generates embeddings for sample documents and ingests them into the database.
    """
    print("🚀 Starting data ingestion...")
    
    # 1. Load the Sentence Transformer model
    print(f"🤖 Loading embedding model: '{EMBEDDING_MODEL_NAME}'")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # 2. Generate embeddings for all documents
    contents = [doc["content"] for doc in documents_to_ingest]
    embeddings = model.encode(contents)
    print("✅ Embeddings generated successfully.")

    conn = None
    try:
        # 3. Connect to the database
        conn_string = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"
        conn = await psycopg.AsyncConnection.connect(conn_string)
        print("✅ Successfully connected to the database.")

        # Register the vector type on the async connection
        await register_vector_async(conn)

        async with conn.cursor() as cur:
            # 4. Insert documents and their embeddings
            for i, doc in enumerate(documents_to_ingest):
                print(f"   -> Ingesting document {i+1}...")
                await cur.execute(
                    "INSERT INTO documents (content, metadata, embedding) VALUES (%s, %s, %s)",
                    (doc["content"], Json(doc["metadata"]), embeddings[i])
                )
            await conn.commit()
        print("\n✅ Ingestion complete. All documents have been saved to the database.")

    except Exception as e:
        print(f"❌ An error occurred during ingestion: {e}")
    finally:
        if conn:
            await conn.close()
            print("🔌 Database connection closed.")

if __name__ == "__main__":
    asyncio.run(ingest_data())
