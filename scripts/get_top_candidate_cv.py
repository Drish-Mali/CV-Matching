import os
import json
import pdfplumber
from dotenv import load_dotenv
from tqdm import tqdm
import openai  
import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
import argparse
import datetime 
load_dotenv()

db_config = {
    "dbname": os.getenv("DBNAME"),
    "user": os.getenv("USER"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST"),
    "port": os.getenv("PORT")
}


# Function to generate embeddings
def generate_query_embeddings(work_experience, education, skills):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return {
        "work_experience_embedding": model.encode(work_experience),
        "education_embedding": model.encode(education),
        "skills_embedding": model.encode(skills)
    }
def query_top_k_similar_cv(work_experience, education, skills, db_config, weights=None, k=3):
    if weights is None:
        weights = {"work_experience": 1.0, "education": 1.0, "skills": 1.0}

    embeddings = generate_query_embeddings(work_experience, education, skills)

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Prepare embeddings as lists for PostgreSQL compatibility
    work_experience_embedding = embeddings['work_experience_embedding'].tolist()
    education_embedding = embeddings['education_embedding'].tolist()
    skills_embedding = embeddings['skills_embedding'].tolist()

    query = """
    SELECT 
        id,
        cv_id,

        (
            (%s * (work_experience_embedding <-> %s::vector)) +
            (%s * (education_embedding <-> %s::vector)) +
            (%s * (skills_embedding <-> %s::vector))
        ) AS combined_distance
    FROM 
        cv_embeddings
    ORDER BY 
        combined_distance ASC  -- Order by ascending distance
    LIMIT %s;
    """

    cursor.execute(query, (
        weights['work_experience'], work_experience_embedding,
        weights['education'], education_embedding,
        weights['skills'], skills_embedding,
        k
    ))

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results



def process_with_chatgpt(text):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    prompt = f"""
    Convert the following job description into a JSON object with exactly three keys: "work_experience", "education", and "skills". Each key should have its corresponding information as a value. Ensure the response is strictly JSON with no comments or additional text outside the JSON object.
    
    Job description:
    {text}
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    result = response.choices[0].message.content
    return result


def extract_top_k(job_description):
    result = process_with_chatgpt(job_description)
    parsed_result = json.loads(result) 
    df=pd.Series(parsed_result)
    df.fillna('',inplace=True)
    results=query_top_k_similar_cv(df['work_experience'], df['education'], df['skills'], db_config)
    return results


def save_results_as_json(results, job_description):
    output_dir = "output/cv_recommendation/"
    os.makedirs(output_dir, exist_ok=True)

    # Reformat results with descriptive keys
    formatted_results = [
        {"id": result[0], "cv_id": result[1], "distance": result[2]} for result in results
    ]

    output = {
        "job_description": job_description,
        "results": formatted_results
    }

    # Save with current timestamp in the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file_path = os.path.join(output_dir, f"job_description__{timestamp}.json")

    with open(json_file_path, 'w') as json_file:
        json.dump(output, json_file, indent=4)
    print(f"Results saved to {json_file_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a job description to get top candidates')
    parser.add_argument('job_description', type=str, help='Job description text')
    args = parser.parse_args()
    

    top_k = extract_top_k(args.job_description)  
    
    save_results_as_json(top_k, args.job_description)
    