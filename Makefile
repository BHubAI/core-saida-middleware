BACKEND_CONTAINER_NAME=backend
DB_CONTAINER_NAME=db

all:

# docker
up:
	@echo "bringing up project...."
	docker compose up -d

down:
	@echo "bringing down project...."
	docker compose down

bash:
	@echo "connecting to container...."
	docker compose exec $(BACKEND_CONTAINER_NAME) bash

# alembic
alembic-scaffold:
	@echo "scaffolding migrations folder..."
	docker compose exec $(BACKEND_CONTAINER_NAME) alembic init migrations

alembic-init:
	@echo "initializing first migration...."
	docker compose exec $(BACKEND_CONTAINER_NAME) alembic revision --autogenerate -m "init"

alembic-make-migrations:
	@echo "creating migration file...."
	docker compose exec $(BACKEND_CONTAINER_NAME) alembic revision --autogenerate -m "add year"

alembic-migrate:
	@echo "applying migration...."
	docker compose exec $(BACKEND_CONTAINER_NAME) alembic upgrade head

# lint
test:
	@echo "running pytest...."
	docker compose exec $(BACKEND_CONTAINER_NAME) pytest --cov-report xml --cov=app tests/

lint:
	@echo "running ruff...."
	docker compose exec $(BACKEND_CONTAINER_NAME) ruff check .

black:
	@echo "running black...."
	docker compose exec $(BACKEND_CONTAINER_NAME) black .

mypy:
	@echo "running mypy...."
	docker compose exec $(BACKEND_CONTAINER_NAME) mypy app/

# database
init-db: alembic-init alembic-migrate
	@echo "initializing database...."
	docker compose exec $(BACKEND_CONTAINER_NAME) python3 app/db/init_db.py

hooks: check
	@echo "installing pre-commit hooks...."
	pre-commit install

# AWS ECR commands
build-ecr:
	@echo "building docker image...."
	docker build --platform linux/amd64 \
		--build-arg ENV_FILE=./ops/docker/staging/env \
		-t core-saida/orchestrator \
		-f ./ops/docker/staging/Dockerfile .

push-ecr:
	@echo "pushing to ECR...."
	aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.us-east-2.amazonaws.com
	docker tag core-saida/orchestrator:latest $(AWS_ACCOUNT_ID).dkr.ecr.us-east-2.amazonaws.com/core-saida/orchestrator:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.us-east-2.amazonaws.com/core-saida/orchestrator:latest

# Local container commands
run-local:
	@echo "running container locally...."
	docker run -d \
		--name core-saida-orchestrator \
		-p 8000:8000 \
		--env-file ./ops/docker/staging/env \
		-e PYTHONPATH=/app \
		core-saida/orchestrator

stop-local:
	@echo "stopping local container...."
	docker stop core-saida-orchestrator
	docker rm core-saida-orchestrator
