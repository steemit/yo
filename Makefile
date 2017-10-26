ROOT_DIR := .
DOCS_DIR := $(ROOT_DIR)/docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build

PROJECT_NAME := yo
PROJECT_DOCKER_TAG := steemit/$(PROJECT_NAME)


.PHONY: docker-image test-without-lint test-pylint clean clean-build

docker-image: clean
	docker build -t $(PROJECT_DOCKER_TAG) .

.env: ${YO_CONFIG} scripts/make_docker_env.py
	pipenv run python scripts/make_docker_env.py ${YO_CONFIG} >.env

test: test-without-lint test-pylint

test-without-lint:
	pipenv run pytest -vv --cov=yo --cov-report term --cov-report html:cov_html

test-pylint:
	pipenv run pytest -v --pylint

clean: clean-build clean-pyc

clean-build:
	rm -fr build/ dist/ *.egg-info .eggs/ .tox/ __pycache__/ .cache/ .coverage htmlcov src

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

install: clean
	pipenv install