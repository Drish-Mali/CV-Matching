

## Introduction
This project aims to a) parse given resume with multi-language support, b) provide job recoomendation given a CV ( top K jobs reccomendation in JSON fromat  and c) provide top k candidates CV reccomendation given a job description.

The project genrates reccomendations based on work experince, education and skills which is extracted from both the resume and job description.

## Installation and Run API end point
To install the required dependencies and run FastAPI, run the following command:

1. Setup .env appropriately with the following fields:
```
OPENAI_API_KEY=' YOUR_OPEN_API_KEY'
DBNAME=vector_db
USER=postgres
PASSWORD=pass123
PORT=5432
HOST=db
```

2. Run the docker compose command:
```
docker-compose up --build
```
3. To Access the API endpoint please have a look at API_documentation.md file.
## Structure 
```
├── README.md                                           # Project overview and instructions
├── requirements.txt                                    # List of dependencies
├── .gitignore                                          # Files to ignore in Git
├── data                                                # Directory for data files
│── app.py                                              # scripts to run Fast API end points : extract_top_k_job,extract_top_k_cv 
│── language_handler.py                                 # scripts to detct langauge used and transalte to english               
├── notebooks                                           # Jupyter notebooks
│       ├── 1-dm-data-preperation-cv.ipynb              # Notebook to create json files from CV pdfs
│       └── 2-dm-data-extract-csv.ipynb                 # Notebook to create csv from json file of CV
│       └── 3-dm-EDA-cv-data.ipynb                      # Notebook to vizualize CV data 
│       └── 4-dm-data-preparation-jd.ipynb              # Notebook to create job description data
│       └── 5-dm-add-jd-embeddings.ipynb                # Experimental notebook to generate job description emdeddings
│       └── 6-dm-add-cv-embeddings.ipynb                # Experimental notebook to generate embeddings from CV
├── results                                             # Directory to save model results
├── Dockerfile                                          # Docker file to expose FastAPI endpoint
├── output                                              # Directory to save top cv and jobs reccomendation jsons
├── output_json                                         # Directory to save json from notebook 2
├── pipeliens                                           # scripts to setup data extraction from CV
│       ├── base.py                                     # script to definebase class for creating and managing of chains 
│       └── langauge_translator.py                      # script to provide a method to translate
│       └── resume_parser.py                            # script to parse the resume using langchain
├── schemas                                             # scripts  defines two Pydantic models, Message and PostData
├── API_documentation.md                                # Detail doument about API
├── scripts                                             # scripts to generate top job decscription or CV
│       ├── get_top_candidate_cv.py                     # scripts to generate and save to top candidate CV
│       └── get_top_jobs.py                             # scripts to generate and save to top jobs
│── utils                                               # scripts with utility function 
│       ├── database                                    # scripts to setup database
│       └── preprocessing                               # script preprocess and parse resume and get text
│       └── setup.py                                    # script create json and csv 
