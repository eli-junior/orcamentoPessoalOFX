"""Serviço de sugestões de IA para categorização de transações."""

import json
import logging
from typing import TYPE_CHECKING

import requests
from decouple import config
from django.db.models import Q

from orcamento_2026.core.services.utils.db_utils import case_insensitive_get

if TYPE_CHECKING:
    from orcamento_2026.core.models import Transaction, TransactionSuggestion, Expense

logger = logging.getLogger(__name__)

OLLAMA_URL: str = config("OLLAMA_URL", default="http://localhost:11434")
OLLAMA_MODEL: str = config("OLLAMA_MODEL", default="qwen2.5:1.5b")


def get_pending_suggestions() -> TransactionSuggestion.QuerySet:
    """Retorna sugestões pendentes de revisão."""
    return TransactionSuggestion.objects.filter(status="PENDENTE").select_related("transaction", "category", "subcategory")


def find_similar_expenses(description: str, limit: int = 3) -> list[Expense]:
    """
    Encontra despesas passadas com descrições similares.

    Usa um filtro simples por conter parte da string.

    Args:
        description: Descrição para buscar similares
        limit: Número máximo de resultados

    Returns:
        Lista de despesas similares
    """
    from orcamento_2026.core.models import Expense

    # Simplificação: pega as primeiras 2 palavras
    parts = description.split()[:2]
    query = Q()
    for part in parts:
        if len(part) > 2:
            query |= Q(transaction__memo__icontains=part)

    if not query:
        return []

    return list(Expense.objects.filter(query).select_related("subcategory", "subcategory__category").order_by("-reference_month")[:limit])


def _build_prompt(
    transaction: "Transaction",
    similar_expenses: list,
    categories: list,
) -> str:
    """Constrói o prompt para a API do Ollama."""
    # Prepara o contexto com categorias disponíveis
    categories_str = ""
    for cat in categories:
        subs = ", ".join([s.name for s in cat.subcategories.all()])
        categories_str += f"- {cat.name}: [{subs}]\n"

    # Prepara exemplos
    examples_str = ""
    if similar_expenses:
        examples_str = "Exemplos de transações similares passadas:\n"
        for exp in similar_expenses:
            examples_str += (
                f"- Memo: '{exp.transaction.memo}' -> "
                f"Categoria: '{exp.subcategory.category.name}', "
                f"Sub: '{exp.subcategory.name}', "
                f"Desc: '{exp.description}'\n"
            )

    return f"""
    Analise a seguinte transação bancária e sugira a Categoria, Subcategoria e uma Descrição amigável.

    Transação:
    - Memo: {transaction.memo}
    - Valor: {transaction.amount}
    - Data: {transaction.date}

    {examples_str}

    Categorias Disponíveis:
    {categories_str}

    Responda APENAS com um JSON estrito no seguinte formato, sem markdown ou explicações:
    {{
        "category": "Nome da Categoria",
        "subcategory": "Nome da Subcategoria",
        "description": "Descrição sugerida (ex: 'Almoço no Restaurante X')"
    }}
    """


def _call_ollama_api(prompt: str) -> dict | None:
    """Chama a API do Ollama e retorna a resposta parseada."""
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"}

    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return json.loads(result["response"])
    except requests.RequestException as e:
        logger.error(f"Erro na chamada à API do Ollama: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao parsear resposta JSON: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado na chamada à API: {e}")

    return None


def generate_suggestion_for_transaction(
    transaction: "Transaction",
) -> "TransactionSuggestion | None":
    """
    Gera uma sugestão via Ollama e salva no banco de dados.

    Args:
        transaction: Transação para analisar

    Returns:
        A sugestão criada ou None se houver erro
    """
    from orcamento_2026.core.models import Category, TransactionSuggestion

    # Verifica se já existe sugestão
    if hasattr(transaction, "suggestion"):
        logger.debug(f"Sugestão já existe para transação {transaction.id}")
        return transaction.suggestion

    similar_expenses = find_similar_expenses(transaction.memo)
    categories = list(Category.objects.prefetch_related("subcategories").all())

    prompt = _build_prompt(transaction, similar_expenses, categories)
    data = _call_ollama_api(prompt)

    if data is None:
        return None

    # Tenta encontrar a categoria e subcategoria
    category = case_insensitive_get(Category.objects.all(), "name", data.get("category"))
    subcategory = None
    if category:
        subcategory = case_insensitive_get(
            category.subcategories.all(),
            "name",
            data.get("subcategory"),
        )

    suggestion = TransactionSuggestion.objects.create(
        transaction=transaction,
        category=category,
        subcategory=subcategory,
        description=data.get("description"),
        status="PENDENTE",
    )

    logger.info(f"Sugestão gerada para transação {transaction.id}")
    return suggestion
