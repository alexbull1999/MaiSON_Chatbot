import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database connection details from environment variables
DB_HOST = os.getenv("AZURE_POSTGRES_HOST")
DB_PORT = os.getenv("AZURE_POSTGRES_PORT", "5432")
DB_NAME = os.getenv("AZURE_POSTGRES_DB")
DB_USER = os.getenv("AZURE_POSTGRES_USER")
DB_PASSWORD = os.getenv("AZURE_POSTGRES_PASSWORD")


def check_table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        # Create a cursor
        cur = conn.cursor()

        # Query to check if table exists
        cur.execute(
            sql.SQL(
                """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = %s
            );
            """
            ),
            [table_name],
        )

        # Get the result
        exists = cur.fetchone()[0]

        # Close cursor and connection
        cur.close()
        conn.close()

        return exists

    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False


def list_all_tables():
    """List all tables in the database"""
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        # Create a cursor
        cur = conn.cursor()

        # Query to list all tables
        cur.execute(
            """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        )

        # Get the results
        tables = [row[0] for row in cur.fetchall()]

        # Close cursor and connection
        cur.close()
        conn.close()

        return tables

    except Exception as e:
        print(f"Error connecting to database: {e}")
        return []


def get_alembic_version():
    """Get the current Alembic version from the database"""
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )

        # Create a cursor
        cur = conn.cursor()

        # Check if alembic_version table exists
        cur.execute(
            """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name = 'alembic_version'
        );
        """
        )

        if not cur.fetchone()[0]:
            print("Alembic version table does not exist")
            cur.close()
            conn.close()
            return None

        # Query to get the current version
        cur.execute("SELECT version_num FROM alembic_version;")

        # Get the result
        version = cur.fetchone()

        # Close cursor and connection
        cur.close()
        conn.close()

        return version[0] if version else None

    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


if __name__ == "__main__":
    print("Checking database schema...")

    # Check if connection details are available
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print(
            "Database connection details are missing. Please check your environment variables."
        )
        sys.exit(1)

    print(f"Connecting to database: {DB_NAME} on {DB_HOST}:{DB_PORT}")

    # Check if specific tables exist
    tables_to_check = [
        "property_conversations",
        "property_messages",
        "general_conversations",
        "general_messages",
        "external_references",
    ]

    for table in tables_to_check:
        exists = check_table_exists(table)
        print(f"Table '{table}' exists: {exists}")

    # List all tables
    print("\nAll tables in the database:")
    tables = list_all_tables()
    for table in tables:
        print(f"- {table}")

    # Get Alembic version
    print("\nCurrent Alembic version:")
    version = get_alembic_version()
    if version:
        print(f"- {version}")
    else:
        print("- No version found or table does not exist")
