import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os
load_dotenv()

# db_config = {
#     "dbname": os.getenv("DBNAME"),
#     "user": os.getenv("USER"),
#     "password": os.getenv("PASSWORD"),
#     "host": os.getenv("HOST"),
#     "port": os.getenv("PORT")
# }

db_config = {
    "dbname": "vector_db",
    "user": "postgres",
    "password": "pass123",
    "host": "db",
    "port": 5432,
}


# SQL commands
SQL_COMMANDS = [
    "CREATE EXTENSION IF NOT EXISTS vector;",
    """
    CREATE TABLE job_embeddings (
        id SERIAL PRIMARY KEY,
        company_name TEXT,
        job_description TEXT,
        work_experience_embedding VECTOR(384), -- Assuming 384 dimensions for embeddings
        education_embedding VECTOR(384),
        skills_embedding VECTOR(384)
    );
    """,
    """
    CREATE TABLE cv_embeddings (
        id SERIAL PRIMARY KEY,
        cv_id INT,
        work_experience_embedding VECTOR(384), -- Assuming 384 dimensions for embeddings
        education_embedding VECTOR(384),
        skills_embedding VECTOR(384)
    );
    """
]

def execute_sql_commands():
    conn = psycopg2.connect(**db_config)
    try:

        
        conn.autocommit = True
        cursor = conn.cursor()

        for command in SQL_COMMANDS:
            cursor.execute(command)
            print(f"Executed: {command.strip()}")

    except Exception as e:
        print(f"Error occurred: {e}")

    finally:
        # Close the connection
        if conn:
            cursor.close()
            conn.close()
            print("Connection closed.")

if __name__ == "__main__":
    execute_sql_commands()
