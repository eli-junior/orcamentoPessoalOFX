ENV=development
PROJECT=orcamento_2026

TEST_FOLDER=./tests

ISORT_FLAGS = --profile=django --lines-after-import=2


.PHONY: all help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

## @ Ambiente
.PHONY: clean install

install: ## Instala dependências para executar o projeto em ambiente de desenvolvimento
	git init
	uvx pre-commit install
	uvx pre-commit autoupdate

clean: ## Remove arquivos de cache do projeto
	@echo "cleaning cache files"
	@py3clean .
	@rm -rf .cache
	@rm -rf build
	@rm -rf dist
	@rm -rf *.egg-info
	@rm -rf htmlcov coverage-report coverage .coverage
	@rm -rf .tox/
	@rm -rf docs/_build
	@rm -rf docs/_build
	@echo "Done!"


.PHONY: test run admin populate migrate migrations shell ## @ Application - See pyproject.toml
test: ## Executa testes e salva cobertura
	@uv run pytest

run: ## Executa a aplicação pelo servidor Django
	@uv run manage.py runserver 0.0.0.0:8000

admin: ## Cria usuário admin
	@uv run manage.py createsuperuser --username admin --email admin@localhost

migrate: ## Verifica novas migrações e as executa
	@uv run manage.py makemigrations
	@uv run manage.py migrate


shell: ## Executa o shell do Django
	@uv run manage.py shell_plus --ipython -- --profile=$(PROJECT)


## @ Linters
.PHONY: lint format lint_all format_all
lint_all: ## Executa flake8 e isort para Verificação do código
	@uvx flake8 $(PROJECT)
	@uvx isort $(PROJECT) --check --diff $(ISORT_FLAGS)

format_all:
	@uvx isort $(PROJECT) $(ISORT_FLAGS)
	@uvx black $(PROJECT)

lint: ## Executa lint apenas nos arquivos modificados (git).
	@uvx flake8 $$(git diff --name-only | grep .py)
	@uvx isort $$(git diff --name-only | grep .py) --check --diff $(ISORT_FLAGS)

format: ## Formata apenas os arquivos modificados (git).
	@uvx black $$(git diff --name-only | grep .py)
	@uvx isort  $$(git diff --name-only | grep .py) $(ISORT_FLAGS)
