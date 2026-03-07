# ═══════════════════════════════════════════════════════════════════════════════
# Makefile - Orçamento 2026
# Gerenciamento de ambiente Django com Docker e UV
# ═══════════════════════════════════════════════════════════════════════════════

# ── Configurações ─────────────────────────────────────────────────────────────
ENV               ?= development
PROJECT           := orcamento_2026
COMPOSE_FILE      := compose.yml
TEST_FOLDER       := ./tests

# Cores para output
CYAN              := \033[36m
GREEN             := \033[32m
YELLOW            := \033[33m
RED               := \033[31m
MAGENTA           := \033[35m
RESET             := \033[0m
BOLD              := \033[1m

# Flags para ferramentas
ISORT_FLAGS       := --profile=django --lines-after-import=2

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 AJUDA
# ═══════════════════════════════════════════════════════════════════════════════
.PHONY: all help
all: help

help: ## Mostra esta ajuda
	@echo ""
	@echo "$(BOLD)$(CYAN)╔════════════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(BOLD)$(CYAN)║           Orçamento 2026 - Comandos Disponíveis               ║$(RESET)"
	@echo "$(BOLD)$(CYAN)╚════════════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "$(BOLD)$(GREEN)🐳 Docker:$(RESET)"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*Docker' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)$(GREEN)🚀 Django:$(RESET)"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*Django' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)$(GREEN)📊 Dados:$(RESET)"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*Dados' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)$(GREEN)🧪 Testes e Qualidade:$(RESET)"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## (Testes|Qualidade)' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)$(GREEN)🔧 Ambiente:$(RESET)"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*Ambiente' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# 🐳 DOCKER
# ═══════════════════════════════════════════════════════════════════════════════
.PHONY: up down build rebuild logs ps shell-web shell-zsh shell-db dev-up dev-shell dev-down

up: ## Docker: Sobe os containers em background
	@echo "$(GREEN)🚀 Subindo containers...$(RESET)"
	docker compose -f $(COMPOSE_FILE) up -d

down: ## Docker: Derruba os containers
	@echo "$(YELLOW)🛑 Derrubando containers...$(RESET)"
	docker compose -f $(COMPOSE_FILE) down

down-v: ## Docker: Derruba containers e remove volumes (CUIDADO!)
	@echo "$(RED)⚠️  Derrubando containers e removendo volumes...$(RESET)"
	docker compose -f $(COMPOSE_FILE) down -v

build: ## Docker: Build das imagens
	@echo "$(GREEN)🔨 Building imagens...$(RESET)"
	docker compose -f $(COMPOSE_FILE) build

rebuild: down build up ## Docker: Rebuild completo (down + build + up)

logs: ## Docker: Mostra logs dos containers
	docker compose -f $(COMPOSE_FILE) logs -f

logs-web: ## Docker: Logs apenas do container web
	docker compose -f $(COMPOSE_FILE) logs -f web

logs-db: ## Docker: Logs apenas do container do banco
	docker compose -f $(COMPOSE_FILE) logs -f db

ps: ## Docker: Status dos containers
	docker compose -f $(COMPOSE_FILE) ps

shell-web: ## Docker: Shell no container web (zsh)
	docker compose -f $(COMPOSE_FILE) exec web /bin/zsh


dev-up: ## Docker: Inicia ambiente de desenvolvimento com shell Zsh
	docker compose -f $(COMPOSE_FILE) --profile dev up -d dev

dev-shell: ## Docker: Acessa shell Zsh do container de desenvolvimento
	docker compose -f $(COMPOSE_FILE) exec dev /bin/zsh

dev-down: ## Docker: Para o container de desenvolvimento
	docker compose -f $(COMPOSE_FILE) --profile dev down

shell-db: ## Docker: Shell no container do PostgreSQL
	docker compose -f $(COMPOSE_FILE) exec db psql -U $(DB_USER) -d $(DB_NAME)

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 DJANGO
# ═══════════════════════════════════════════════════════════════════════════════
.PHONY: run run-docker admin shell dbshell collectstatic check check-deploy

run: ## Django: Executa o servidor de desenvolvimento local
	@echo "$(GREEN)🚀 Iniciando servidor Django...$(RESET)"
	@uv run manage.py collectstatic --no-input && uv run manage.py runserver 0.0.0.0:8000

run-docker: ## Django: Executa o servidor via Docker
	@echo "$(GREEN)🚀 Iniciando servidor Django no Docker...$(RESET)"
	docker compose -f $(COMPOSE_FILE) up

admin: ## Django: Cria superusuário
	@echo "$(GREEN)👤 Criando superusuário no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec web python manage.py createsuperuser

shell: ## Django: Shell Plus com IPython no container
	@echo "$(GREEN)🐚 Abrindo shell do Django no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec web python manage.py shell_plus --ipython

dbshell: ## Django: Shell do banco de dados no container
	@echo "$(GREEN)🗄️  Abrindo shell do PostgreSQL no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec web python manage.py dbshell

collectstatic: ## Django: Coleta arquivos estáticos
	@echo "$(GREEN)📦 Coletando arquivos estáticos...$(RESET)"
	@uv run manage.py collectstatic --no-input

check: ## Django: Verifica problemas no projeto
	@echo "$(GREEN)🔍 Verificando projeto...$(RESET)"
	@uv run manage.py check

check-deploy: ## Django: Verifica problemas de deploy
	@echo "$(GREEN)🔍 Verificando configurações de deploy...$(RESET)"
	@uv run manage.py check --deploy

# ═══════════════════════════════════════════════════════════════════════════════
# 🗄️ MIGRAÇÕES - Executadas no container
# ═══════════════════════════════════════════════════════════════════════════════
.PHONY: makemigrations migrate migrar_db showmigrations sqlmigrate makemigrations-merge

makemigrations: ## Migrações: Cria novas migrações
	@echo "$(GREEN)📝 Criando migrações no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py makemigrations

makemigrations-merge: ## Migrações: Resolve conflitos de migração
	@echo "$(YELLOW)🔀 Resolvendo conflitos de migração no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py makemigrations --merge

migrate: ## Migrações: Aplica migrações pendentes
	@echo "$(GREEN)🗄️  Aplicando migrações no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py migrate

migrar_db: makemigrations migrate ## Migrações: Cria e aplica migrações (alias)

showmigrations: ## Migrações: Lista migrações e seu status
	@echo "$(GREEN)📋 Listando migrações no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py showmigrations

sqlmigrate: ## Migrações: Mostra SQL de uma migração (use: make sqlmigrate APP=MIGRATION)
	@if [ -z "$(APP)" ]; then \
		echo "$(RED)❌ Informe o app e migração: make sqlmigrate APP=nome_app MIGRATION=0001$(RESET)"; \
		exit 1; \
	fi
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py sqlmigrate $(APP) $(MIGRATION)

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 DADOS (Management Commands) - Executados no container
# ═══════════════════════════════════════════════════════════════════════════════
.PHONY: popular importar consolidar sugerir limpar_transacoes full-import

popular: ## Dados: Popula categorias e dados iniciais
	@echo "$(GREEN)🌱 Populando dados iniciais no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py popular

importar: ## Dados: Importa arquivos OFX
	@echo "$(GREEN)📥 Importando arquivos OFX no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py importar

consolidar: ## Dados: Consolida transações em despesas
	@echo "$(GREEN)🔄 Consolidando transações no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py consolidar

sugerir: ## Dados: Sugere categorias via IA
	@echo "$(MAGENTA)🤖 Sugerindo categorias com IA no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py sugerir

limpar_transacoes: ## Dados: Remove transações antigas (opcional)
	@echo "$(YELLOW)🧹 Limpando transações antigas no container...$(RESET)"
	@docker compose -f $(COMPOSE_FILE) exec -T web python manage.py shell -c "from core.models import Transacao; Transacao.objects.filter(consolidada=True).delete()"

full-import: ## Dados: Pipeline completo (importar + consolidar + sugerir)
	@echo "$(BOLD)$(GREEN)🚀 Executando pipeline completo de importação...$(RESET)"
	@$(MAKE) importar
	@$(MAKE) consolidar
	@$(MAKE) sugerir
	@echo "$(BOLD)$(GREEN)✅ Pipeline concluído!$(RESET)"

# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TESTES & QUALIDADE
# ═══════════════════════════════════════════════════════════════════════════════
.PHONY: test test-cov test-failfast test-path lint format lint_all format_all

test: ## Testes: Executa todos os testes com pytest
	@echo "$(GREEN)🧪 Executando testes...$(RESET)"
	@uv run pytest

test-cov: ## Testes: Executa testes com relatório de cobertura detalhado
	@echo "$(GREEN)🧪 Executando testes com cobertura...$(RESET)"
	@uv run pytest --cov-report=term-missing

test-failfast: ## Testes: Para no primeiro erro
	@echo "$(GREEN)🧪 Executando testes (fail-fast)...$(RESET)"
	@uv run pytest -x

test-path: ## Testes: Executa testes de um caminho específico (use: make test-path PATH=tests/test_core.py)
	@if [ -z "$(PATH)" ]; then \
		echo "$(RED)❌ Informe o caminho: make test-path PATH=tests/test_core.py$(RESET)"; \
		exit 1; \
	fi
	@uv run pytest $(PATH) -v

# ── Lint & Format ─────────────────────────────────────────────────────────────
lint_all: ## Qualidade: Executa flake8 e isort em todo o projeto
	@echo "$(GREEN)🔍 Executando linters...$(RESET)"
	@uvx flake8 $(PROJECT)
	@uvx isort $(PROJECT) --check --diff $(ISORT_FLAGS)

format_all: ## Qualidade: Formata todo o código com black e isort
	@echo "$(GREEN)✨ Formatando código...$(RESET)"
	@uvx isort $(PROJECT) $(ISORT_FLAGS)
	@uvx black $(PROJECT)

lint: ## Qualidade: Lint apenas nos arquivos modificados (git)
	@echo "$(GREEN)🔍 Verificando arquivos modificados...$(RESET)"
	@uvx flake8 $$(git diff --name-only --diff-filter=ACM | grep '\.py$$' || echo "$(PROJECT)")
	@uvx isort $$(git diff --name-only --diff-filter=ACM | grep '\.py$$' || echo "$(PROJECT)") --check --diff $(ISORT_FLAGS)

format: ## Qualidade: Formata apenas os arquivos modificados (git)
	@echo "$(GREEN)✨ Formatando arquivos modificados...$(RESET)"
	@uvx black $$(git diff --name-only --diff-filter=ACM | grep '\.py$$' || echo "$(PROJECT)")
	@uvx isort $$(git diff --name-only --diff-filter=ACM | grep '\.py$$' || echo "$(PROJECT)") $(ISORT_FLAGS)

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 AMBIENTE & UTILITÁRIOS
# ═══════════════════════════════════════════════════════════════════════════════
.PHONY: install install-dev update clean requirements env

install: ## Ambiente: Instala dependências de produção
	@echo "$(GREEN)📦 Instalando dependências...$(RESET)"
	@uv sync --no-dev

install-dev: ## Ambiente: Instala dependências de desenvolvimento
	@echo "$(GREEN)📦 Instalando dependências de desenvolvimento...$(RESET)"
	@uv sync
	@git init 2>/dev/null || true
	@uvx pre-commit install 2>/dev/null || true
	@uvx pre-commit autoupdate 2>/dev/null || true

update: ## Ambiente: Atualiza dependências
	@echo "$(GREEN)🔄 Atualizando dependências...$(RESET)"
	@uv lock --upgrade
	@uv sync

clean: ## Ambiente: Remove arquivos de cache e temporários
	@echo "$(YELLOW)🧹 Limpando arquivos temporários...$(RESET)"
	@py3clean . 2>/dev/null || find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@rm -rf .cache build dist *.egg-info htmlcov coverage-report coverage .coverage .tox/
	@rm -rf docs/_build .mypy_cache .pytest_cache
	@echo "$(GREEN)✅ Limpo!$(RESET)"

requirements: ## Ambiente: Gera arquivo requirements.txt
	@echo "$(GREEN)📄 Gerando requirements.txt...$(RESET)"
	@uv export --no-dev -o requirements.txt

requirements-dev: ## Ambiente: Gera requirements com dev dependencies
	@echo "$(GREEN)📄 Gerando requirements-dev.txt...$(RESET)"
	@uv export -o requirements-dev.txt

env: ## Ambiente: Mostra variáveis de ambiente configuradas
	@echo "$(GREEN)🔧 Variáveis de ambiente:$(RESET)"
	@echo "  ENV=$(ENV)"
	@echo "  PROJECT=$(PROJECT)"
	@uv run python -c "import os; [print(f'  {k}={v}') for k, v in os.environ.items() if k.startswith('DJANGO') or k.startswith('DB_')]" 2>/dev/null || true

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 DEPLOY & PRODUÇÃO
# ═══════════════════════════════════════════════════════════════════════════════
.PHONY: docker-build docker-push docker-run

docker-build: ## Deploy: Build da imagem Docker
	@echo "$(GREEN)🐳 Building imagem Docker...$(RESET)"
	@docker build -t $(PROJECT):latest .

docker-run: ## Deploy: Roda container localmente
	@echo "$(GREEN)🚀 Rodando container...$(RESET)"
	@docker run -p 8000:8000 --env-file .env $(PROJECT):latest

# ═══════════════════════════════════════════════════════════════════════════════
# 📋 ALIASES CURTOS
# ═══════════════════════════════════════════════════════════════════════════════
.PHONY: mm m t r s d

mm: makemigrations ## Alias: makemigrations
m: migrate        ## Alias: migrate
t: test           ## Alias: test
r: run            ## Alias: run
s: shell          ## Alias: shell
d: up             ## Alias: docker up
