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
def insert_job_data_from_df(jd_df, db_config):
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Fill NaN values with empty strings
    jd_df = jd_df.fillna('')

    for _, job in jd_df.iterrows():
        embeddings = generate_query_embeddings(
            job['work_experience'],
            job['education'],
            job['skills']
        )
        cursor.execute("""
            INSERT INTO job_embeddings (
                company_name, job_description, work_experience_embedding, education_embedding, skills_embedding
            ) VALUES (%s, %s, %s::vector, %s::vector, %s::vector)
        """, (
            job['company_name'],
            job['job_description'],
            embeddings['work_experience_embedding'].tolist(),  # Convert to list
            embeddings['education_embedding'].tolist(),        # Convert to list
            embeddings['skills_embedding'].tolist()            # Convert to list
        ))

    conn.commit()
    cursor.close()
    conn.close()
    print("Job data from DataFrame inserted successfully!")



# Database configuration
db_config = {
    "dbname": os.getenv("DBNAME"),
    "user": os.getenv("USER"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST"),
    "port": os.getenv("PORT")
}


if __name__=="__main__":
    jd_df = pd.read_csv('./data/jd_data/jd.csv')
    insert_job_data_from_df(jd_df, db_config)
