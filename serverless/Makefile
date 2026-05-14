.PHONY: help validate build deploy-dev deploy-prod sync-dev logs-dev logs-prod \
        clean test coverage lint format typecheck cfn-lint setup

# ============================================================================
# Atajos del backend serverless del portfolio
# ============================================================================
# Uso: `make <target>` desde serverless/
# Para CLI integrado: `python devtools/run.py serverless <command>`
# ============================================================================

help: ## Lista todos los targets disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Sincroniza .venv via uv sync (primera vez)
	uv sync --frozen

validate: ## Valida sintaxis SAM template
	sam validate --lint --region us-east-1

cfn-lint: ## CFN-lint sobre el template (validacion adicional)
	uv run cfn-lint template.yaml

build: ## Build SAM (compila layers + zips)
	sam build --use-container --cached --parallel

deploy-dev: build ## Deploy stack dev (us-east-1)
	sam deploy --config-env dev

deploy-prod: build ## Deploy stack prod (us-east-1)
	sam deploy --config-env prod

sync-dev: ## Hot-reload de codigo Lambda en dev
	sam sync --stack-name portfolio-backend-dev --watch \
	  --region us-east-1

logs-dev: ## Tail logs de Lambdas dev (uso: make logs-dev FUNC=ContactFormFunction)
	sam logs -n $(FUNC) --stack-name portfolio-backend-dev --tail \
	  --region us-east-1

logs-prod:
	sam logs -n $(FUNC) --stack-name portfolio-backend-prod --tail \
	  --region us-east-1

test: ## Corre tests unitarios con coverage
	uv run pytest tests/unit -v --cov=src

coverage: ## Reporte de coverage HTML
	uv run pytest tests/unit --cov=src --cov-report=html
	@echo "Open htmlcov/index.html"

lint: ## Ruff lint (sin auto-fix)
	uv run ruff check src/ tests/

format: ## Ruff format (auto-fix)
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

typecheck: ## mypy strict
	uv run mypy src/ tests/

clean: ## Limpia .aws-sam/, .pytest_cache/, htmlcov/, __pycache__
	rm -rf .aws-sam .pytest_cache htmlcov .ruff_cache .mypy_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
