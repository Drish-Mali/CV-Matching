## Introduction

This API uses FastAPI to provide a top candidate CV reccomendation for a given job description and top job reccomendation given a CV. The service leverages OPENAI and json cv schema to parse the given CV and postgres and pgvector as datbases.

## Table of Contents

- [API Endpoints](#api-endpoints)
- [Request and Response](#request-and-response)
- [Installation](#installation)
- [Running with Docker](#running-with-docker)

---

## API Endpoints

### 1. `extract_top_k_cv`
**Method:** `POST`  
**Description:**  Endpoint to extract the top-k CV recommendations from given job_description.

#### Endpoint Request:

- **URL:** `/extract_top_k_cv`
- **Method:** `POST`
- **Request Body (JSON):**
  **job_description (string, required):** Given job description.
  **top_k (integer, optional):** Number of top CV recommendations to return (default: 3).

```json
{
   "job_description": "string",
   "top_k": 3
}
```

#### Example:

```json
{
    "job_description": "bachelors degree or equivalent practical experience years of experience in saas or productivity tools businessexperience managing enterprise accounts with sales cycles",
    "top_k": 3
}
```

#### Response:

- **Success Response (200):**

```json
{
    "results": {
        "job_description": "bachelors degree or equivalent practical experience years of experience in saas or productivity tools businessexperience managing enterprise accounts with sales cycles",
        "results": [
            {
                "id": 773,
                "cv_id": 27219200,
                "distance": 2.974390449384776
            },
            {
                "id": 657,
                "cv_id": 35483925,
                "distance": 3.1214687661372267
            },
            {
                "id": 734,
                "cv_id": 15423153,
                "distance": 3.1222403654921798
            }
        ]
    }
}
```
**Fields in Each Result:** 
- **id:** The database identifier of the CV used in the search.

- **cv_id:** A unique identifier for the CV in the database. This can be used to fetch more details about the CV if needed.

- **distance:** A numerical score representing the distance (or dissimilarity) between the job description and the CV.Lower distances indicate a closer match, meaning the CV aligns well with the job description based on Work experience,education and skill.

- **Error Response (500):**

```json
{
  "detail": "Internal Server Error"
}
```

---

### 2. `extract_top_k_job`
**Method:** `POST`  
**Description:**  Endpoint to extract the top-k jobs recommendations from given CV.

#### Endpoint Request:

- **URL:** `/extract_top_k_job`
- **Method:** `POST`
- **Request Body (JSON):**
  **pdf_path (string, required):** Full file path to the CV PDF file.
  **top_k (integer, optional):** Number of top job recommendations to return (default: 3).

```json
{
   "pdf_path": "string",
   "top_k": 3
}
```

#### Example:

```json
{
    "pdf_path": "abc.pdf",
    "top_k": 3
}
```

#### Response:

- **Success Response (200):**

```json
{
    "results": [
        [
            93,
            "ManTech",
            "where applicable confirmation that you meet customer requirements for facility access which may include proof of vaccination andor attestation and testing unless an accommodation has been approved\n\nsecure our nation ignite your future\n\ndue to the ongoing pandemic the health and safety of our employees and their families remains our highest priority our student employment opportunities may vary in starting onsiteinperson or remain in a virtual setting this will be dependent on the critical needs of the specific role each student is hired for the mantech excelerate program is honored to continue our worldclass early career programs for \n\njob description\n\nbecome an integral part of a diverse team while working at an industry leading organization where our employees come first at mantech international corporation youll help protect our national security while working on innovative projects that offer opportunities for advancement\n\ncurrently mantech is seeking a motivated career and customeroriented software developer associate to join our team locations vary depending on business needs\n\nresponsibilities include but are not limited to\n\nuse your skills learned in and out of school on mantechs mission critical work mantech is seeking a motivated missionoriented software developer associate to join our mission at mantech you will work on innovative projects that offer great technical challenges\n assisting the development leadsmanagers with all aspects of software design and coding\n attending and contributing to company development meetings\n learning the codebase and improving your coding skills\n writing and maintaining code\n working on minor bug fixes\n build and deploy applications in cloud computing\n monitoring the technical performance of internal systems\n responding to requests from the development team\n gathering information from consumers about program functionality\n writing reports\n conducting development tests\n\nbasic qualifications\n bachelors degree in computer science or related field\n experience writing software in nodejs javajavascript r cc andor assembly language\n basic programming experience\n knowledge of relational and nosql databases\n experience working and collaborating within an agile team using collaboration tools like slack office  google suite atlassian\n knowledge or reverse engineer system components as necessary\n basic understanding of cyber security and secure systems\n experience with research tools techniques countermeasures and trends in computer network vulnerabilities data hiding and network security and encryption\n\npreferred qualifications\n a passion for software development and engineering\n strong grasp of operating system fundamentals including interrupts threading virtual memory device drivers and memory management techniques\n knowledge and understanding of operating system internals and the integration of code with the operating system kernel\n ability to learn new software and technologies quickly\n detail oriented\n ability to follow instructions and work in a team\n\nclearance requirements\n individuals must be a us citizen and either hold an active us security clearance or must be eligible to obtain a us security clearance\n applicants with the appropriate skills but without a security clearance are still encouraged to apply\n\nphysical requirements\n must be able to remain in a stationary position \n\nfor all positions requiring access to technologysoftware source code that is subject to export control laws employment with the company is contingent on either verifying usperson status or obtaining any necessary license the applicant will be required to answer certain questions for export control purposes and that information will be reviewed by compliance personnel to ensure compliance with federal law mantech may choose not to apply for a license for such individuals whose access to exportcontrolled technology or software source code may require authorization and may decline to proceed with an applicant on that basis alone\n\nmantech international corporation as well as its subsidiaries proactively fulfills its role as an equal opportunity employer we do not discriminate against any employee or applicant for employment because of race color sex religion age sexual orientation gender identity and expression national origin marital status physical or mental disability status as a disabled veteran recently separated veteran active duty wartime or campaign badge veteran armed forces services medal or any other characteristic protected by law\n\nif you require a reasonable accommodation to apply for a position with mantech through its online applicant system please contact mantechs corporate eeo department at   mantech is an affirmative actionequal opportunity employer  minorities females disabled and protected veterans are urged to apply mantechs utilization of any external recruitment or job placement agency is predicated upon its full compliance with our equal opportunityaffirmative action policies mantech does not accept resumes from unsolicited recruiting firms we pay no fees for unsolicited services\n\nif you are a qualified individual with a disability or a disabled veteran you have the right to request an accommodation if you are unable or limited in your ability to use or access  as a result of your disability to request an accommodation please click careersmantechcom and provide your name and contact information",
            3.0500098749877176
        ],
        [
            141,
            "Helix",
            "you  helix\n\nhelix is a place where innovators and doers gather in order to drive significant progress in population genomics we have come together to work at the intersection of clinical care research and genomics\n\nif youre excited by the idea of making a meaningful impact and joining a team where we pride ourselves on driving innovation through fostering an environment with an emphasis on empowering one another to grow helix might be the place for you\n\nhelix  the world\n\nour endtoend population genomics platform enables health systems life sciences companies and payers to advance genomic research and accelerate the integration of genomic data into routine clinical care we support all aspects of population genomics from recruitment to translational research and help our partners use genomics to improve health outcomes increase patient engagement and lower costs leading health systems including renown health adventhealth and mayo clinic use our population genomics platform to power some of the worlds largest and fastestgrowing population genomics initiatives\n\nfor the covid public health crisis helix has built one of the nations largest covid diagnostic labs and has been on the leading edge of national viral surveillance efforts tracking b and other viral strains\n\nas a senior manager test you will\n lead a team of test engineers te and software engineers in test set to advance helixs mission\n partner with product and engineering managers to execute against quarterly and annual product roadmaps\n work at the intersection of quality assurance and engineering to develop efficient workflows for testing and validation\n evolve testing and validation practices into a key strategic advantage for helix\n drive culture of testing and adoption of best practices across teams\n collaborate with peer leaders across engineering product management and science to advance helixs platforms people and culture\n mentor teammates to reinforce a culture of learning and teaching\n\nrequired\n  years leading test engineering teams\n a proven track record driving adoption of manual and automated testing in a fast paced agile organization\n experience developing automated test frameworks for front and back end api testing\n experience with test case management tools eg testrail jama etc\n proven track record of recruiting managing and retaining engineering talent\n development experience in go python typescript or a similar language\n empathetic diligent datadriven highintegrity leadership style\n\npluses\n bachelormaster of science in computer science\n experience with cloud computing paradigms serverless infrastructure as code etc\n experience with fullstack development\n familiarity with regulated software systems hipaa fda etc\n\nwhat helix has to offer you\n\naside from working alongside brilliant dedicated passionate downtoearth curious warm and thoughtful people we also provide great benefits\n competitive compensation comprehensive health insurance package including employer sponsored hsa\n  weeks of maternity or paternity leave\n k with employer matching and  vested on first day\n corporate fitness rate\n comprehensive well being benefits\n catered meals\n flexible pto\n\nhelix is proud to be an equal opportunity employer and committed to providing employment opportunities regardless of race religious creed color national origin ancestry physical disability mental disability medical condition genetic information marital status sex gender gender identity gender expression pregnancy childbirth and breastfeeding age sexual orientation military or veteran status or any other protected classification in accordance with applicable federal state and local laws",
            3.1335300830300734
        ]
    ]
}
```
**Fields in Each Result:** 
- **id:** The database identifier of the job description used in the search.

- **company name:** Comapny name of that provided the job.

- **distance:** A numerical score representing the distance (or dissimilarity) between the job description and the CV. Lower distances indicate a closer match, meaning the CV aligns well with the job description based on Work experience,education and skill.

- **Error Response (500):**

```json
{
  "detail": "Internal Server Error"
}
```

---



## Installation

To run this API locally, you need the following dependencies:

- Python 3.9+
- FastAPI
- OPENAI
- Numpy
- Pandas
- Docker
- Postgres
- Uvicorn (for running the FastAPI server)

### Steps to Install

1. **Clone the repository**  
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install dependencies**  
- To install the required dependencies and run FastAPI, run the following command:
1. Install dependencies:
```
python -m pip install -r requirements.txt

```
2. Setup the pgvector:
```
docker pull ankane/pgvector
docker run --name pgvector-demo -e POSTGRES_PASSWORD=yourpassword -p 5432:5432 -d ankane/pgvector
```
4. Setup .venv and .secerts.toml appropriately

5. Create tables in postgres:
```
python utils/setup_tables.py
```
6. Setup cv and job embeddings tables:
```
python utils/setup_cv.py
python utils/setup_job_descriptions.py
```
7. Run the FastAPI application:
```
python src/app.py
```

---

## Running with Docker

### Building and Running the Docker Container

The provided Dockerfile creates a slim Python environment to run the FastAPI app. Follow these steps to build and run the container:

1. **Build the Docker image**

   Run the following command in the directory containing your Dockerfile:

   ```bash
   docker build -t resume-api .
   ```

2. **Run the Docker container**

   To run the API server:

   ```bash
   docker run -d -p 8000:8000 resume-api
   ```

   This command exposes the API on port `8000` of your localhost.

3. **Access the API**

   Open your browser or use `curl` to access the FastAPI UI or test the endpoints:

   - FastAPI Swagger Docs: `http://localhost:8000/docs`
   - Example API request:

  - 1. extract_top_k_cv
   ```bash
   curl -X 'POST' \
  'http://localhost:8000/extract_top_k_cv' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_description": "bachelors degree or equivalent practical experience years of experience in saas or productivity tools businessexperience managing enterprise accounts with sales cycles",
    "top_k": 3
   }'
   ```
  - 2. extract_top_k_job
  ```bash
   curl -X 'POST' \
  'http://localhost:8000/extract_top_k_cv' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "job_description": "bachelors degree or equivalent practical experience years of experience in saas or productivity tools businessexperience managing enterprise accounts with sales cycles",
    "top_k": 3
   }'
   ```


---



