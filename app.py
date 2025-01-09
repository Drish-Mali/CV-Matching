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

# Function to generate embeddings
def generate_query_embeddings(work_experience, education, skills):
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
        ]
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
    results=query_top_k_similar_cv(parsed_result.get("work_experience", {}), parsed_result.get("education", {}), parsed_result.get("skills", {}), db_config,top_k)
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
    #job_description="bachelors degree or equivalent practical experience years of experience in saas or productivity tools businessexperience managing enterprise accounts with sales cycles"
#     job_description = """
# Web designers looking to expand your professional reach, welcome to Robert Half Marketing & Creative. Start the process with Robert Half today.

# We are searching for highly skilled web designers with experience working within corporate brand standards and guidelines. The ideal candidates would have advanced skills in creating wireframes, designing mobile applications, landing pages, interactive sites, QA testing, experience working with various interfaces, and familiarity with UX/UI design principles. Candidates are expected to have strong skills in Adobe Photoshop, Illustrator, and InDesign. Any experience in HTML, CSS, and JavaScript is a major plus. Familiarity with content management systems is highly preferred.

# There is nothing more satisfying when looking for freelance and full-time creative opportunities than working with someone who knows your area of expertise. As industry professionals, Robert Half Marketing & Creative is a team that puts your needs first and effectively represents you as a creative talent. That's the kind of service you'll receive from our team at Robert Half.

# We have marketing, advertising, and creative backgrounds just like yours—so we’re on your side right from the start. Could you ask for a better support team?

# Requirements:
# - 2+ years of experience in a web design role.
# - Experience working within a client's brand standards or guidelines.
# - Advanced skill in the Adobe Creative Cloud.

# Innovation starts with people.

# Robert Half is the world’s first and largest specialized talent solutions firm that connects highly qualified job seekers to opportunities at great companies. We offer contract, temporary, and permanent placement solutions for finance and accounting, technology, marketing and creative, legal, and administrative and customer support roles.

# Robert Half puts you in the best position to succeed by advocating on your behalf and promoting you to employers. We provide access to top jobs, competitive compensation and benefits, and free online training. Stay on top of every opportunity—even on the go.

# Questions? Call your local office at [number]. Robert Half will consider qualified applicants with criminal histories in a manner consistent with the requirements of the San Francisco Fair Chance Ordinance. All applicants applying for U.S. job openings must be legally authorized to work in the United States. Benefits are available to temporary professionals. Visit [website] for more information.

# Robert Half is an Equal Opportunity Employer M/F/Disability/Veterans. By clicking "Apply Now," you’re agreeing to our terms.
# """

    top_k_results = await extract_top_k_cv(job_description=job_description,top_k=top_k)
    return {"results": top_k_results}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
