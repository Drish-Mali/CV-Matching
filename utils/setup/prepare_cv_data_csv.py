import pandas as pd
import json
import os

def process_json(file_path, folder_name):
    # Get the filename from the path
    file_name = os.path.basename(file_path)

    # Extract the id from the filename
    cv_id = os.path.splitext(file_name)[0]  # Assuming the format is something like '10554236.json'

    # Load JSON from the file
    try:
        with open(file_path, 'r') as file:
            cv_data = json.load(file)

        # Extract 'work' section and combine them into a paragraph
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

        # Create a DataFrame with 'id', 'folder_name', 'work', 'education', and 'skills_projects' columns
        df = pd.DataFrame({
            'id': [cv_id],
            'category': [folder_name],
            'work': [work_paragraph],
            'education': [education_paragraph],
            'skills_projects': [skills_projects_paragraph]
        })

        return df

    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return None

def process_folder(folder_path):
    all_data = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                folder_name = os.path.basename(root)
                df = process_json(file_path, folder_name)
                if df is not None:
                    all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

if __name__=='__main__':
    folder_path = './output_json'
    final_df = process_folder(folder_path)
    final_df.to_csv("./data/cv data/cv_data.csv",index=False)

