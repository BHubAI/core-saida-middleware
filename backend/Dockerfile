FROM python:3.12 AS base

ARG env

WORKDIR /tmp

RUN pip install "poetry>=2.0.1"

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry install --no-root $(test "${env:-dev}" != "prod" && echo "--with dev") \
    && poetry run pip freeze > requirements.txt

FROM python:3.12

COPY --from=base /tmp/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ADD . /code/
WORKDIR /code
ENV PYTHONPATH=/code

EXPOSE 8000
