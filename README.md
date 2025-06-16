<p align="center">
    <a href="https://github.com/rafaelnunes/core-saida-middleware/actions">
        <img alt="GitHub Actions status" src="https://github.com/rafaelnunes/core-saida-middleware/actions/workflows/main.yml/badge.svg">
    </a>
    <a href="https://github.com/rafaelnunes/core-saida-middleware/releases"><img alt="Release Status" src="https://img.shields.io/github/v/release/rafaelnunes/core-saida-middleware"></a>
</p>


## Architecture

## Usage

1. `make up`


## Backend local development, additional details

Initialize first migration (project must be up with docker compose up and contain no 'version' files)

```shell
$ make alembic-init
```

Create new migration file

```shell
$ docker compose exec backend alembic revision --autogenerate -m "some cool comment"
```

Apply migrations

```shell
$ make alembic-migrate
```

### Migrations

Every migration after that, you can create new migrations and apply them with

```console
$ make alembic-make-migrations "cool comment dude"
$ make alembic-migrate
```

### General workflow

See the [Makefile](/Makefile) to view available commands.

By default, the dependencies are managed with [Poetry](https://python-poetry.org/), go there and install it.

From `./backend/` you can install all the dependencies with:

```console
$ poetry install
```

### pre-commit hooks

If you haven't already done so, download [pre-commit](https://pre-commit.com/) system package and install. Once done, install the git hooks with

```console
$ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```


### Deployments

A common scenario is to use an orchestration tool, such as docker swarm, to deploy your containers to the cloud (DigitalOcean). This can be automated via GitHub Actions workflow. See [main.yml](/.github/workflows/main.yml) for more.

You will be required to add `secrets` in your repo settings:

- DIGITALOCEAN_TOKEN: your DigitalOcean api token
- REGISTRY: container registry url where your images are hosted
- POSTGRES_PASSWORD: password to postgres database
- STAGING_HOST_IP: ip address of the staging droplet
- PROD_HOST_IP: ip address of the production droplet
- SSH_KEY: ssh key of user connecting to server (`ubuntu` in this case)
