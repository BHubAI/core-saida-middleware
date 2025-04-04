# syntax=docker/dockerfile:1

FROM python:3.12 AS base

# Create and set the working directory
WORKDIR /tmp

# Install system dependencies including PostgreSQL development libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install "poetry>=2.0.1"

# Copy poetry files first
COPY pyproject.toml poetry.lock* /tmp/

RUN poetry install --no-root $(test "${env:-dev}" != "prod" && echo "--with dev") \
    && poetry run pip freeze > requirements.txt


FROM python:3.12

COPY --from=base /tmp/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Set environment variables from env file
ARG ENV_FILE
COPY ${ENV_FILE} /app/.env
RUN set -a && . /app/.env && set +a

WORKDIR /app

# Copy all content from the local app/ folder to the /app folder in the container
COPY app/ /app/

ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
