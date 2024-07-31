.PHONY: help
help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

run: ## run python file
	@if [ -f .env ]; then \
		set -a; \
		. ./.env; \
		set +a; \
		echo "Contents of .env file:"; \
		cat .env; \
		echo "Environment variables after loading .env:"; \
		env | grep -E "TOKEN|PYTHON_"; \
		python main.py "$$TOKEN"; \
	else \
		echo "No .env file found. Proceeding without it."; \
		python main.py; \
	fi