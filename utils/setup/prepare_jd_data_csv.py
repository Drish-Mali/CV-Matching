import os
import re
import pdfplumber
import pandas as pd
import numpy as np
import openai
import json
from dotenv import load_dotenv
import time
from datasets import load_dataset
from tqdm import tqdm

def process_jd_with_chatgpt(text):
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

tqdm.pandas()
def extract_parts(row):
    try:
        result = process_jd_with_chatgpt(row["job_description"])
        parsed_result = json.loads(result) 
        return pd.Series(parsed_result)  
    except Exception as e:
       
        return pd.Series({"work_experience": None, "education": None, "skills": None})





if __name__=="__main__":
    jd_data = load_dataset('jacob-hugging-face/job-descriptions', split="train")
    jd_df = pd.DataFrame(jd_data)
    jd_df[["work_experience", "education", "skills"]] = jd_df.progress_apply(extract_parts, axis=1)
    jd_df.to_csv('./data/jd_data/jd.csv',index=False)
