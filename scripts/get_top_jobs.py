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
from utils.preprocessing.text_fecther import process_single_file
from config.config import settings
from language_handler import lang_identiy
from pipelines.resume_parser import ResumeParser
from pipelines.langauge_translator import LanguageTranslator
load_dotenv()
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
def query_top_k_similar_job_description(work_experience, education, skills, db_config, weights=None, k=3):
    if weights is None:
        weights = {"work_experience": 1.0, "education": 1.0, "skills": 1.0}

    embeddings = generate_query_embeddings(work_experience, education, skills)

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Prepare embeddings as lists for PostgreSQL compatibility
    work_experience_embedding = embeddings['work_experience_embedding'].tolist()[0]
    education_embedding = embeddings['education_embedding'].tolist()[0]
    skills_embedding = embeddings['skills_embedding'].tolist()[0]

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
    return process_single_file(pdf_path,lower_case = False)

def process_with_chatgpt(text):
  resume_parser = ResumeParser(query_template=settings.query.RESUME_PARSER_TEMPLATE)
  language = lang_identiy(text)
  if language != "en":
        translate_text = LanguageTranslator(query_template=settings.translate.LANGUAGE_TRANSLATE_TEMPLATE)
        translate_text =  translate_text.translate(resume_text=text)
        parsed_content =  resume_parser.parser(resume_text=translate_text, resume_schema=resume_schema)
        return parsed_content
  else:            
        parsed_content =  resume_parser.parser(resume_text=text, resume_schema=resume_schema)
        return parsed_content

def extract_top_k(pdf_path):
    text = extract_information(pdf_path)
    structured_data = process_with_chatgpt(text)
    cv_data = json.loads(structured_data)
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

    df = pd.DataFrame({
        'id': pdf_path,
        'work': [work_paragraph],
        'education': [education_paragraph],
        'skills_projects': [skills_projects_paragraph]
    })
    df.fillna('',inplace=True)
    results=query_top_k_similar_job_description(df['work'], df['education'], df['skills_projects'], db_config)
    return results

def save_results_as_json(results, pdf_path):
    output_dir = "output/job_recommendation/"
    os.makedirs(output_dir, exist_ok=True)
    output = {
        "pdf_path": pdf_path,
        "results": results
    }
    json_file_path = os.path.join(output_dir, os.path.basename(pdf_path).replace('.pdf', '_results.json'))
    with open(json_file_path, 'w') as json_file:
        json.dump(output, json_file, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a PDF to extract information and recommend jobs.')
    parser.add_argument('pdf_path', type=str, help='Path to the PDF file')
    args = parser.parse_args()

    top_k = extract_top_k(args.pdf_path)
    save_results_as_json(top_k, args.pdf_path)
    print(f"Results saved for {args.pdf_path}.")
    