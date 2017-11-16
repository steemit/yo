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
	pipenv run pytest -vv --cov=yo --cov-report term tests

test-pylint:
	pipenv run pytest -v --pylint

.PHONY: format
format:
	pipenv run yapf -i **/*.py

.PHONY: run-local
run-local:
	env YO_DATABASE_URL=sqlite:///yo.db pipenv run python -m yo.cli

.PHONY: init-db
init-db:
	pipenv run python -m yo.db_utils sqlite:///yo.db init

.PHONY: reset-db
reset-db:
	pipenv run python -m yo.db_utils sqlite:///yo.db reset

clean: clean-build clean-pyc

clean-build:
	rm -fr build/ dist/ *.egg-info .eggs/ .tox/ __pycache__/ .cache/ .coverage htmlcov src yo.db

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

install: clean
	if [[ $(shell uname) == 'Darwin' ]]; then \
    	brew install openssl; \
        env LDFLAGS="-L$(shell brew --prefix openssl)/lib" CFLAGS="-I$(shell brew --prefix openssl)/include" pipenv install --python 3.6 --dev; \
        else \
		pipenv lock --python 3.6 --hashes; \
		pipenv install --python 3.6 --dev; \
        fi


.PHONY: install-python-steem-macos
install-python-steem-macos: ## install steem-python lib on macos using homebrew's openssl
	env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" pipenv install steem

