PRJ          = homework
COMPOSE      = docker compose
COMPOSE_APP  = -f docker-compose.yml
COMPOSE_TEST = -f docker-compose-test.yml
COMPOSE_PROD = -f docker-compose.prod.yml
VENV_PY      = .venv\Scripts\python.exe

COMPOSE_FILE ?= docker-compose-test.yml
TEST_FILE    ?= tests
PYTEST_ARGS  ?=

# --- CD ---
REGISTRY     ?= ghcr.io
IMAGE_REPO   ?= $(REGISTRY)/var-py/$(PRJ)
IMAGE_TAG    ?= $(shell git rev-parse --short HEAD)
IMAGE        = $(IMAGE_REPO):$(IMAGE_TAG)

.DEFAULT_GOAL := help

.PHONY: help install install-dev build build-app build-test build-tests up start stop down restart logs ps \
        test pytest test-local test-unit test-integration test-cov test-cov-local lint fmt ci \
        image push prod-up prod-down prod-logs prod-ps shell test-shell clean fclean prune

# $(info ...) вместо @echo: не требует внешней команды, поэтому `make help`
# работает и на Windows (где make не находит shell-встроенный echo).
define HELP_TEXT
Targets:
  make install          - install runtime dependencies into .venv
  make install-dev      - install runtime + test/lint dependencies into .venv
  make lint / make fmt  - ruff check / ruff check --fix + format
  make ci               - what CI does locally: lint + full test suite with coverage
  make build            - build images of the app and test stacks
  make up / make down  - start / stop the app stack (docker-compose.yml)
  make test             - run pytest in docker (docker-compose-test.yml)
  make test-local       - run pytest in the local .venv
  make test-unit        - run only tests/unit
  make test-integration - run only tests/integration
  make test-cov         - pytest with coverage in docker
  make image / make push - build / push the image to $(REGISTRY)
  make prod-up          - start the production stack from the published image
  make logs             - follow app stack logs
  make shell            - shell inside the test container
  make clean / fclean  - stop stacks and remove containers, volumes, images
  make test TEST_FILE=tests/unit/test_delete.py PYTEST_ARGS='-x -vv'
endef

help:
	$(info $(HELP_TEXT))

install:
	$(VENV_PY) -m pip install -r requirements.txt

install-dev:
	$(VENV_PY) -m pip install -r requirements-dev.txt

lint:
	$(VENV_PY) -m ruff check .

fmt:
	$(VENV_PY) -m ruff check --fix .
	$(VENV_PY) -m ruff format .

ci: lint
	$(VENV_PY) -m pytest --cov=app --cov-report=term-missing -q $(TEST_FILE)

build: build-app build-tests

build-app:
	$(COMPOSE) $(COMPOSE_APP) build

build-test build-tests:
	$(COMPOSE) $(COMPOSE_TEST) build

up start:
	$(COMPOSE) $(COMPOSE_APP) up -d --build --wait

down stop:
	$(COMPOSE) $(COMPOSE_APP) down

restart: down up

logs:
	$(COMPOSE) $(COMPOSE_APP) logs -f

ps:
	$(COMPOSE) $(COMPOSE_APP) ps
	$(COMPOSE) $(COMPOSE_TEST) ps

test pytest: build-tests
	$(COMPOSE) -f $(COMPOSE_FILE) run --rm --build tests pytest $(PYTEST_ARGS) $(TEST_FILE)

test-local:
	$(VENV_PY) -m pytest $(PYTEST_ARGS) $(TEST_FILE)

test-unit:
	$(COMPOSE) -f $(COMPOSE_FILE) run --rm tests pytest $(PYTEST_ARGS) tests/unit

test-integration:
	$(COMPOSE) -f $(COMPOSE_FILE) run --rm tests pytest $(PYTEST_ARGS) tests/integration

test-cov: build-tests
	$(COMPOSE) -f $(COMPOSE_FILE) run --rm tests pytest --cov=app --cov-report=term-missing tests

test-cov-local:
	$(VENV_PY) -m pytest --cov=app --cov-report=term-missing $(TEST_FILE)

# --- CD ---
image:
	docker build -t $(IMAGE) -t $(IMAGE_REPO):latest .

push: image
	docker push $(IMAGE)
	docker push $(IMAGE_REPO):latest

prod-up:
	$(COMPOSE) $(COMPOSE_PROD) pull
	$(COMPOSE) $(COMPOSE_PROD) up -d --remove-orphans
	$(COMPOSE) $(COMPOSE_PROD) ps

prod-down:
	$(COMPOSE) $(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE) $(COMPOSE_PROD) logs -f

prod-ps:
	$(COMPOSE) $(COMPOSE_PROD) ps

shell test-shell:
	$(COMPOSE) -f $(COMPOSE_FILE) run --rm --entrypoint sh tests

clean:
	$(COMPOSE) $(COMPOSE_APP) down
	$(COMPOSE) $(COMPOSE_TEST) down

fclean: clean
	$(COMPOSE) $(COMPOSE_APP) down -v --rmi local
	$(COMPOSE) $(COMPOSE_TEST) down -v --rmi local
	$(COMPOSE) $(COMPOSE_PROD) down -v

prune:
	docker system prune -f
