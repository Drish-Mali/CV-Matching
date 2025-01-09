FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD python utils/database/setup_tables.py && \
    python utils/database/setup_cv.py && \
    python utils/database/setup_job_description.py && \
    python app.py