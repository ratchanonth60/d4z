COMPOSE_FILE := docker-compose.yml
BASE_COMPOSE_CMD := docker-compose -f $(COMPOSE_FILE)
help:
	@awk -F: '/^[a-zA-Z0-9_-]+:.*##/ { printf "\033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | sort

build: 
	$(BASE_COMPOSE_CMD) up -d --build $(target)

stop:
	$(BASE_COMPOSE_CMD) stop $(target)


logs:
	$(BASE_COMPOSE_CMD) logs -f $(target)


ssh:
	$(BASE_COMPOSE_CMD) exec $(target) $(user)

tests:
	$(BASE_COMPOSE_CMD) exec app pytest --disable-pytest-warnings

restart:
	$(BASE_COMPOSE_CMD) restart $(target)
