from fastapi import FastAPI, File, UploadFile
import os
import json
import pdfplumber
from dotenv import load_dotenv
from tqdm import tqdm
import openai  
import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
import uvicorn
from utils.preprocessing.text_fecther import process_single_file
from config.config import settings
from language_handler import lang_identiy
from pipelines.resume_parser import ResumeParser
from pipelines.langauge_translator import LanguageTranslator
import asyncio
from pydantic import BaseModel
from typing import Optional
import shutil

class JobRequest(BaseModel):
    pdf_path:str 
    top_k: Optional[int] = None

class CVRequest(BaseModel):
    job_description:str 
    top_k: Optional[int] = None

# resume schema format
resume_schema = {
  "basics": {
    "name": "",
    "label": "",
    "image": "",
    "email": "",
    "phone": "",
    "url": "",
    "summary": "",
    "location": {
      "address": "",
      "postalCode": "",
      "city": "",
      "countryCode": "",
      "region": ""
    },
    "profiles": [
      {
        "network": "",
        "username": "",
        "url": ""
      }
    ]
  },
  "work": [
    {
      "name": "",
      "position": "",
      "url": "",
      "startDate": "",
      "endDate": "",
      "summary": "",
      "highlights": []
    }
  ],
  "volunteer": [
    {
      "organization": "",
      "position": "",
      "url": "",
      "startDate": "",
      "endDate": "",
      "summary": "",
      "highlights": []
    }
  ],
  "education": [
    {
      "institution": "",
      "url": "",
      "area": "",
      "studyType": "",
      "startDate": "",
      "endDate": "",
      "score": "",
      "courses": []
    }
  ],
  "awards": [
    {
      "title": "",
      "date": "",
      "awarder": "",
      "summary": ""
    }
  ],
  "certificates": [
    {
      "name": "",
      "date": "",
      "issuer": "",
      "url": ""
    }
  ],
  "publications": [
    {
      "name": "",
      "publisher": "",
      "releaseDate": "",
      "url": "",
      "summary": ""
    }
  ],
  "skills": [
    {
      "name": "",
      "level": "",
      "keywords": []
    }
  ],
  "languages": [
    {
      "language": "",
      "fluency": ""
    }
  ],
  "interests": [
    {
      "name": "",
      "keywords": []
    }
  ],
  "references": [
    {
      "name": "",
      "reference": ""
    }
  ],
  "projects": [
    {
      "name": "",
      "startDate": "",
      "endDate": "",
      "description": "",
      "highlights": [],
      "url": ""
    }
  ]
}

load_dotenv()

app = FastAPI()

db_config = {
    "dbname": os.getenv("DBNAME"),
    "user": os.getenv("USER"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST"),
    "port": os.getenv("PORT")
}

def generate_query_embeddings(work_experience, education, skills):
    # Handle None values by replacing them with an empty string
    work_experience = work_experience or ""
    education = education or ""
    skills = skills or ""

    model = SentenceTransformer('all-MiniLM-L6-v2')
    return {
        "work_experience_embedding": model.encode(work_experience),
        "education_embedding": model.encode(education),
        "skills_embedding": model.encode(skills)
    }

# results=query_top_k_similar_job_description(work_paragraph, education_paragraph, skills_projects_paragraph, db_config,k=top_k)
def query_top_k_similar_job_description(work_experience, education, skills, db_config,k, weights=None):
    if weights is None:
        weights = {"work_experience": 1.0, "education": 1.0, "skills": 1.0}
    if k is None:
        k=3

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
        company_name,
        job_description,
        (
            (%s * (work_experience_embedding <-> %s::vector)) +
            (%s * (education_embedding <-> %s::vector)) +
            (%s * (skills_embedding <-> %s::vector))
        ) AS combined_distance
    FROM 
        job_embeddings
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

def extract_information(pdf_path):
    # with pdfplumber.open(pdf_path) as pdf:
    #     resume_text = ""
    #     for page in pdf.pages:
    #         resume_text = " ".join([resume_text, page.extract_text()])
    # resume_text = resume_text.strip()
    # return resume_text
    return process_single_file(pdf_path,lower_case = False)

async def process_with_chatgpt(text):

    resume_parser = ResumeParser(query_template=settings.query.RESUME_PARSER_TEMPLATE)
    language = lang_identiy(text)
    if language != "en":
        translate_text = LanguageTranslator(query_template=settings.translate.LANGUAGE_TRANSLATE_TEMPLATE)
        translate_text = await translate_text.translate(resume_text=text)
        parsed_content = await resume_parser.parser(resume_text=translate_text, resume_schema=resume_schema)
        return parsed_content
    else:            
        parsed_content = await resume_parser.parser(resume_text=text, resume_schema=resume_schema)
        return parsed_content


async def extract_top_k(pdf_path,top_k):
    text = extract_information(pdf_path)
    structured_data = await process_with_chatgpt(text)
    cv_data = structured_data
    work_paragraph = ""
    for work in cv_data.get('work', []):
        work_summary = work.get('summary', '')
        work_highlights = ', '.join(work.get('highlights', []))
        if work_summary or work_highlights:
            work_paragraph += f"Position: {work.get('position', '')}\n"
            work_paragraph += f"Company: {work.get('name', '')}\n"
            work_paragraph += f"Summary: {work_summary}\n"
            if work_highlights:
                work_paragraph += f"Highlights: {work_highlights}\n"
            work_paragraph += "\n"

    # Extract 'education' section and combine them into a paragraph
    education_paragraph = ""
    for education in cv_data.get('education', []):
        institution = education.get('institution', '')
        area = education.get('area', '')
        study_type = education.get('studyType', '')
        start_date = education.get('startDate', '')
        end_date = education.get('endDate', '')
        courses = ', '.join(education.get('courses', []))

        education_paragraph += f"Institution: {institution}\n"
        education_paragraph += f"Area of Study: {area}\n"
        education_paragraph += f"Degree: {study_type}\n"
        education_paragraph += f"Start Date: {start_date}\n"
        education_paragraph += f"End Date: {end_date}\n"
        if courses:
            education_paragraph += f"Courses: {courses}\n"
        education_paragraph += "\n"

    # Extract 'skills' section and combine them into a paragraph
    skills_projects_paragraph = ""
    for skills in cv_data.get('skills', []):
        skill_name = skills.get('name', '')
        skill_level = skills.get('level', '')
        skill_keywords = ', '.join(skills.get('keywords', []))

        skills_projects_paragraph += f"Skill: {skill_name}\n"
        if skill_level:
            skills_projects_paragraph += f"Level: {skill_level}\n"
        if skill_keywords:
            skills_projects_paragraph += f"Keywords: {skill_keywords}\n"
        skills_projects_paragraph += "\n"
    print(top_k)
    results=query_top_k_similar_job_description(work_paragraph, education_paragraph, skills_projects_paragraph, db_config,k=top_k)
    return results

# @app.post("/extract_top_k_job/")
# async def extract_top_k_job_endpoint(request: JobRequest):
#     """
#     Endpoint to extract the top-k jobs from a PDF.

#     Args:
#         request (JobRequest): Request body containing 'pdf_path' and 'top_k'.

#     Returns:
#         dict: Dictionary containing the extracted top-k job recommendations for the given CV.
#     """
#     pdf_path = request.pdf_path
#     top_k = request.top_k
#     pdf_path="C:\\Users\\deepa\\Downloads\\cv matching\\data\\data\\INFORMATION-TECHNOLOGY\\10089434.pdf"
#     top_k_results = await extract_top_k(pdf_path,top_k)
#     return {"results": top_k_results}

@app.post("/extract_top_k_job/")
async def extract_top_k_job_endpoint(top_k: Optional[int] = None, file: UploadFile = File(...)):
    """
    Endpoint to extract the top-k jobs from an uploaded PDF.

    Args:
        top_k (Optional[int]): The number of top job recommendations to extract (default is None).
        file (UploadFile): The uploaded PDF file containing the CV.

    Returns:
        dict: Dictionary containing the extracted top-k job recommendations for the uploaded CV.
    """
    # Save the uploaded PDF file temporarily
    pdf_path = f"temp_{file.filename}"
    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Call the extract_top_k function with the uploaded file
    top_k_results = await extract_top_k(pdf_path, top_k)

    # Optionally, remove the temporary file after processing
    os.remove(pdf_path)

    return {"results": top_k_results}






def query_top_k_similar_cv(work_experience, education, skills, db_config,k, weights=None):
    if weights is None:
        weights = {"work_experience": 1.0, "education": 1.0, "skills": 1.0}
    if k is None:
        k=3
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



async def process_with_chatgpt_jd(text):
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
        ],
        temperature=0

    )
    result = response.choices[0].message.content
    return result


async def extract_top_k_cv(job_description,top_k):
    result = await process_with_chatgpt_jd(job_description)
    print(result)
    parsed_result = json.loads(result) 
    df=pd.Series(result)
    print(df)
    df.fillna('',inplace=True)
    results=query_top_k_similar_cv(parsed_result.get("work_experience", {""}), parsed_result.get("education", {""}), parsed_result.get("skills", {""}), db_config,top_k)
    formatted_results = [
        {"id": result[0], "cv_id": result[1], "distance": result[2]} for result in results
    ]

    output = {
        "job_description": job_description,
        "results": formatted_results
    }
    return output


@app.post("/extract_top_k_cv/")
async def extract_top_k_cv_endpoint(request:CVRequest):
    """
    Endpoint to extract the top-k CV recommendations from given job_description.

    Args:
        request (CVRequest): Request body containing 'job_description' and 'top_k'.

    Returns:
        dict: Dictionary containing the extracted top-k CV recommendations for the given job_description.
    """
    job_description=request.job_description
    top_k=request.top_k
    top_k_results = await extract_top_k_cv(job_description=job_description,top_k=top_k)
    return {"results": top_k_results}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
