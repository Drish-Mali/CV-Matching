import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
import os
# Initialize the model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to generate embeddings
def generate_query_embeddings(work_experience, education, skills):
    return {
        "work_experience_embedding": model.encode(work_experience),
        "education_embedding": model.encode(education),
        "skills_embedding": model.encode(skills)
    }

# Function to insert job data into the database
def insert_job_data_from_df(cv_df, db_config):
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Fill NaN values with empty strings
    cv_df = cv_df.fillna('')

    for _, job in cv_df.iterrows():
        embeddings = generate_query_embeddings(
            job['work'],
            job['education'],
            job['skills_projects']
        )
        cursor.execute("""
            INSERT INTO cv_embeddings (
                cv_id, work_experience_embedding, education_embedding, skills_embedding
            ) VALUES (%s, %s::vector, %s::vector, %s::vector)
        """, (
            job['id'],
            embeddings['work_experience_embedding'].tolist(),  # Convert to list
            embeddings['education_embedding'].tolist(),        # Convert to list
            embeddings['skills_embedding'].tolist()            # Convert to list
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print("CV data from DataFrame inserted successfully!")



# Database configuration
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

if __name__=="__main__":
    cv_df = pd.read_csv('./data/cv data/cv_data.csv')
    insert_job_data_from_df(cv_df, db_config)
