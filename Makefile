DOCKER_COMPOSE_DEMO=docker-compose -f docker-compose.yml -f docker-compose.demo.yml

ifeq ("$(ENV)", "prod")
PIPENV_ARGS=
else
ENV=dev
PIPENV_ARGS=--dev
endif

.PHONY: init
init: conf venv data-dir migrate

.PHONY: conf
conf:
	@echo "• Autogenerate configuration..."
	./tools/mkconf.sh
	@echo

.PHONY: venv
venv:
	@echo "• Setup virtualenv with all dependencies..."
	# Install pipenv: use pip3 if it exists, or fallback to pip
	command -v pip3 2>&1 >/dev/null && \
		pip3 install pipenv --user --upgrade || \
		pip install pipenv --user --upgrade
	# Install dependencies in a virtual environment
	pipenv install $(PIPENV_ARGS)
	@echo

.PHONY: data-dir
data-dir:
	@echo "• Create data directory if needed..."
	mkdir -p data
	@echo

.PHONY: migrate
migrate:
	@echo "• Migrate database to latest version..."
	pipenv run ./manage.py migrate
	@echo

.PHONY: check
check:
	@pipenv run ./tools/check.sh

.PHONY: test
test:
	@echo "• pytest -vv"
	@pipenv run pytest -vv
	@echo

.PHONY: demo-start demo-stop demo-restart demo-update
demo-start:
	@echo "• Start demo server..."
	$(DOCKER_COMPOSE_DEMO) up -d --build
	@echo

demo-stop:
	@echo "• Stop demo server..."
	$(DOCKER_COMPOSE_DEMO) down
	@echo

demo-restart:
	@echo "• Restart demo server..."
	$(DOCKER_COMPOSE_DEMO) restart
	@echo

demo-update:
	@echo "• Update demo server..."
	git pull --rebase
	$(DOCKER_COMPOSE_DEMO) up -d --no-deps --build
	@echo
