import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database connection details from environment variables
DB_HOST = os.getenv("AZURE_POSTGRES_HOST")
DB_PORT = os.getenv("AZURE_POSTGRES_PORT", "5432")
DB_NAME = os.getenv("AZURE_POSTGRES_DB")
DB_USER = os.getenv("AZURE_POSTGRES_USER")
DB_PASSWORD = os.getenv("AZURE_POSTGRES_PASSWORD")


def list_all_database_objects():
    """List all database objects including tables, views, and schemas"""
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

        # List all schemas
        print("\n=== SCHEMAS ===")
        cur.execute(
            """
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT LIKE 'pg_%' 
        AND schema_name != 'information_schema'
        ORDER BY schema_name;
        """
        )
        schemas = [row[0] for row in cur.fetchall()]
        for schema in schemas:
            print(f"- {schema}")

        # List all tables by schema
        print("\n=== TABLES BY SCHEMA ===")
        for schema in schemas:
            cur.execute(
                """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """,
                (schema,),
            )

            tables = [row[0] for row in cur.fetchall()]
            if tables:
                print(f"\nSchema: {schema}")
                for table in tables:
                    # Get row count for each table
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {schema}.{table};")
                        row_count = cur.fetchone()[0]
                        print(f"- {table} ({row_count} rows)")
                    except Exception as e:
                        print(f"- {table} (error counting rows: {e})")

        # List all views
        print("\n=== VIEWS ===")
        cur.execute(
            """
        SELECT table_schema, table_name 
        FROM information_schema.views 
        WHERE table_schema NOT LIKE 'pg_%' 
        AND table_schema != 'information_schema'
        ORDER BY table_schema, table_name;
        """
        )

        views = [(row[0], row[1]) for row in cur.fetchall()]
        for schema, view in views:
            print(f"- {schema}.{view}")

        # List all sequences
        print("\n=== SEQUENCES ===")
        cur.execute(
            """
        SELECT sequence_schema, sequence_name 
        FROM information_schema.sequences 
        WHERE sequence_schema NOT LIKE 'pg_%' 
        AND sequence_schema != 'information_schema'
        ORDER BY sequence_schema, sequence_name;
        """
        )

        sequences = [(row[0], row[1]) for row in cur.fetchall()]
        for schema, sequence in sequences:
            print(f"- {schema}.{sequence}")

        # Close cursor and connection
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error connecting to database: {e}")


if __name__ == "__main__":
    print("Listing all database objects...")

    # Check if connection details are available
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        print(
            "Database connection details are missing. Please check your environment variables."
        )
        sys.exit(1)

    print(f"Connecting to database: {DB_NAME} on {DB_HOST}:{DB_PORT}")

    list_all_database_objects()
