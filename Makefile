ROOT_DIR := .
DOCS_DIR := $(ROOT_DIR)/docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build

PROJECT_NAME := yo
PROJECT_DOCKER_TAG := steemit/$(PROJECT_NAME)
PROJECT_DOCKER_RUN_ARGS := -p8080:8080 --env-file .env

GIT_USER := steemit
GIT_REMOTE_REPO := $(PROJECT_NAME)
CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
CURRENT_ISSUE := $(subst 'issue-','', $(CURRENT_BRANCH))

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: docker-image
docker-image: clean ## build docker image
	docker build -t $(PROJECT_DOCKER_TAG) .

.env: ${YO_CONFIG} scripts/make_docker_env.py
	pipenv run python scripts/make_docker_env.py ${YO_CONFIG} >.env

Pipfile.lock:
	$(shell docker run $(PROJECT_DOCKER_TAG) /bin/bash -c 'pipenv lock && cat Pipfile.lock' > $@)

.PHONY: begin-fix
begin-fix: ## begin github issue fix: 'make begin-fix issue=99'
	git checkout master
	git pull
	git checkout -b issue-$(issue)

.PHONY: commit-fix
commit-fix: fmt test pre-commit docker-image Pipfile.lock ## commit fix
	git commit -am'Fixes $(CURRENT_ISSUE)'
	git push --set-upstream origin $(CURRENT_BRANCH)

.PHONY: run
run: .env ## run docker image
	docker run $(PROJECT_DOCKER_RUN_ARGS) $(PROJECT_DOCKER_TAG)

.PHONY: test
test: test-without-lint test-pylint ## run pylint tests locally

.PHONY: test-without-lint
test-without-lint:
	pipenv run pytest -vv --cov=yo --cov-report term tests

.PHONY: test-pylint
test-pylint:
	pipenv run pytest -v --pylint $(PROJECT_NAME)

.PHONY: lint
lint: ## lint python files
	pipenv run pylint $(PROJECT_NAME)

.PHONY: fix-imports
fix-imports: remove-unused-imports sort-imports ## remove unused and then sort imports

.PHONY: remove-unused-imports
remove-unused-imports: ## remove unused imports from python files
	pipenv run autoflake --in-place --remove-all-unused-imports --recursive $(PROJECT_NAME)

.PHONY: sort-imports
sort-imports: ## sorts python imports using isort with settings from .editorconfig
	pipenv run isort --verbose --recursive --atomic --settings-path  .editorconfig --virtual-env .venv $(PROJECT_NAME)

.PHONY: fmt
fmt: remove-unused-imports sort-imports ## format python files
    # yapf is disabled until the update 3.6 fstring compat
	pipenv run yapf --in-place --style pep8 --recursive $(PROJECT_NAME)
	pipenv run autopep8 --verbose --verbose --max-line-length=100 --aggressive --jobs -1 --in-place  --recursive $(PROJECT_NAME)

.PHONY: pre-commit
pre-commit: ## run pre-commit against modified files
	pipenv run pre-commit run

.PHONY: pre-commit-all
pre-commit-all: ## run pre-commit against all files
	pipenv run pre-commit run --all-files

.PHONY: run-local
run-local: ## run application locally
	env YO_DATABASE_URL=sqlite:///yo.db pipenv run python -m yo.cli

.PHONY: init-db
init-db: ## initialize app db
	pipenv run python -m yo.db_utils sqlite:///yo.db init

.PHONY: reset-db
reset-db: ## reset app db
	pipenv run python -m yo.db_utils sqlite:///yo.db reset

.PHONY: clean
clean: clean-build clean-pyc ## clean

.PHONY: clean-build
clean-build:
	rm -fr build/ dist/ *.egg-info .eggs/ .tox/ __pycache__/ .cache/ .coverage htmlcov src yo.db

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

.PHONY: install
install: clean ## install python app
	if [[ $(shell uname) == 'Darwin' ]]; then \
    	brew install openssl; \
        env LDFLAGS="-L$(shell brew --prefix openssl)/lib" CFLAGS="-I$(shell brew --prefix openssl)/include" pipenv install --python 3.6 --dev; \
        else \
        	pipenv install --python 3.6 --dev; \
        fi


.PHONY: install-python-steem-macos
install-python-steem-macos: ## install steem-python lib on macos using homebrew's openssl
	env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" pipenv install steem
