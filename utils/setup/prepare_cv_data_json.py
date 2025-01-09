import os
import json
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pdfplumber
from dotenv import load_dotenv
from tqdm import tqdm  # Import tqdm for progress tracking
import openai  # Ensure this library is installed and properly configured
from utils.preprocessing.text_fecther import process_single_file
from config.config import settings
from language_handler import lang_identiy
def parse_contents(text):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    resume_schema = json.dumps({
        "basics": {
            "name": "John Doe",
            "label": "Programmer",
            "image": "",
            "email": "john@gmail.com",
            "phone": "(912) 555-4321",
            "url": "https://johndoe.com",
            "summary": "A summary of John Doe…",
            "location": {
                "address": "2712 Broadway St",
                "postalCode": "CA 94115",
                "city": "San Francisco",
                "countryCode": "US",
                "region": "California"
            },
            "profiles": [ {
                "network": "Twitter",
                "username": "john",
                "url": "https://twitter.com/john"
            }]
        },
        "work": [ {
            "name": "Company",
            "position": "President",
            "url": "https://company.com",
            "startDate": "2013-01-01",
            "endDate": "2014-01-01",
            "summary": "Description…",
            "highlights": [
                "Started the company"
            ]
        }],
        "volunteer": [ {
            "organization": "Organization",
            "position": "Volunteer",
            "url": "https://organization.com/",
            "startDate": "2012-01-01",
            "endDate": "2013-01-01",
            "summary": "Description…",
            "highlights": [
                "Awarded 'Volunteer of the Month'"
            ]
        }],
        "education": [ {
            "institution": "University",
            "url": "https://institution.com/",
            "area": "Software Development",
            "studyType": "Bachelor",
            "startDate": "2011-01-01",
            "endDate": "2013-01-01",
            "score": "4.0",
            "courses": [
                "DB1101 - Basic SQL"
            ]
        }],
        "awards": [ {
            "title": "Award",
            "date": "2014-11-01",
            "awarder": "Company",
            "summary": "There is no spoon."
        }],
        "certificates": [ {
            "name": "Certificate",
            "date": "2021-11-07",
            "issuer": "Company",
            "url": "https://certificate.com"
        }],
        "publications": [ {
            "name": "Publication",
            "publisher": "Company",
            "releaseDate": "2014-10-01",
            "url": "https://publication.com",
            "summary": "Description…"
        }],
        "skills": [ {
            "name": "Web Development",
            "level": "Master",
            "keywords": [
                "HTML",
                "CSS",
                "JavaScript"
            ]
        }],
        "languages": [ {
            "language": "English",
            "fluency": "Native speaker"
        }],
        "interests": [ {
            "name": "Wildlife",
            "keywords": [
                "Ferrets",
                "Unicorns"
            ]
        }],
        "references": [ {
            "name": "Jane Doe",
            "reference": "Reference…"
        }],
        "projects": [ {
            "name": "Project",
            "startDate": "2019-01-01",
            "endDate": "2021-01-01",
            "description": "Description...",
            "highlights": [
                "Won award at AIHacks 2016"
            ],
            "url": "https://project.com/"
        }]
    }, indent=2)
    
    prompt = f"""
    Convert the following resume text into a structured JSON CV format. Follow this schema exactly, leaving unspecified fields empty and refraining from adding anything not mentioned in the text. Return only the JSON output without any additional information.
     - If a field is not explicitly mentioned in the resume, leave it empty.   
     - Return only the JSON object without additional text or commentary
Schema: {resume_schema}

Resume Text: {text}
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


def tranlaste_given_text(resume_text):
    LANGUAGE_TRANSLATE_TEMPLATE = """
    Translate the following text into English. Maintain the original meaning and tone of the text as accurately as possible. Do not include any explanations or additional information—only return the translated English text.

    Text: {resume_text}
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4-mini",
        messages=[
            {"role": "system", "content": "You are a helpful translation assistant."},
            {"role": "user", "content":LANGUAGE_TRANSLATE_TEMPLATE}
        ]
    )
    result = response.choices[0].message.content
def extract_information(pdf_path):
    return process_single_file(pdf_path,lower_case = False)

def process_with_chatgpt(text):

    
    language = lang_identiy(text)
    if language != "en":
       
        translate_text = tranlaste_given_text(text)
        print(translate_text)
        parsed_content = parse_contents(text)
        return parsed_content
    else:            
        parsed_content =  parse_contents(text)
        print(parsed_content)
        return parsed_content

# def process_with_chatgpt(text):
#     openai.api_key = os.getenv("OPENAI_API_KEY")
    
    
#     prompt = f"""
#     Convert the following resume text into a structured JSON CV format. Leave the feilds that are not given empty and don't add anything not mentioned. Return a json file as specificed below and add nothing on it. The schema should match this format:
#     {schema_example}
    
#     Resume Text:
#     {text}
#     """
#     client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
#     response = client.chat.completions.create(
#         model="gpt-4",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": prompt}
#         ]
#     )
#     result = response.choices[0].message.content
#     return result

def extract_and_format_resume(pdf_path):
    text = extract_information(pdf_path)
    print("here :")
    print(text)
    structured_data =  process_with_chatgpt(text)
    return structured_data

def process_pdfs_in_folder(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    subdirs = [f for f in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, f))]

    for subdir in tqdm(subdirs, desc="Processing Folders"):
        subdir_path = os.path.join(input_folder, subdir)
        print(subdir_path)
        pdf_files = [f for f in os.listdir(subdir_path) if f.endswith(".pdf")]

        for file_name in pdf_files:
            pdf_path = os.path.join(subdir_path, file_name)
            try:
                structured_data = extract_and_format_resume(pdf_path)
                output_file = os.path.join(output_folder, subdir, f"{os.path.splitext(file_name)[0]}.json")
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, "w") as f:
                    f.write(structured_data)
            except Exception as e:
                print(f"Error processing {file_name}: {e}")


if __name__=="__main__":
    input_folder = ".\data\data"
    output_folder = ".\output_json_new_try"
    process_pdfs_in_folder(input_folder, output_folder)