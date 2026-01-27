lint:
	uvx ruff check

lint-fix:
	uvx ruff check --fix

test:
	uv run pytest

schema:
	uv run sipe-tool-example config-schema --file=./schemas/config_schema.json