"""Serviço de sugestões de IA para categorização de transações."""

import difflib
import json
import logging
import threading

import requests
from decouple import config
from django.db.models import Q

from orcamento_2026.core.models import Expense, Transaction, TransactionSuggestion
from orcamento_2026.core.services.utils.db_utils import case_insensitive_get

logger = logging.getLogger(__name__)

OLLAMA_URL: str = config("OLLAMA_URL", default="http://localhost:11434")
OLLAMA_MODEL: str = config("OLLAMA_MODEL", default="qwen2.5:1.5b")


def get_pending_suggestions() -> TransactionSuggestion:
    """Retorna sugestões pendentes de revisão."""
    return TransactionSuggestion.objects.filter(status="PENDENTE").select_related(
        "transaction", "category", "subcategory"
    )


def find_similar_expenses(description: str, limit: int = 5) -> list[Expense]:
    """
    Encontra despesas passadas com descrições similares usando SequenceMatcher.
    Mais inteligente que busca por palavras simples.

    Args:
        description: Descrição para buscar similares
        limit: Número máximo de resultados

    Returns:
        Lista de despesas similares ranqueadas por similaridade
    """
    # Busca candidatos com filtro inicial por palavras-chave
    parts = [p for p in description.split() if len(p) > 3]
    if not parts:
        return []

    query = Q()
    for part in parts[:3]:
        query |= Q(transaction__memo__icontains=part) | Q(description__icontains=part)

    candidates = list(
        Expense.objects.filter(query)
        .select_related("subcategory", "subcategory__category")
        .order_by("-reference_month")[:50]
    )

    # Ranqueia por similaridade com SequenceMatcher
    def similarity_score(expense: Expense) -> float:
        memo_sim = difflib.SequenceMatcher(
            None, description.lower(), expense.transaction.memo.lower()
        ).ratio()
        desc_sim = difflib.SequenceMatcher(
            None, description.lower(), (expense.description or "").lower()
        ).ratio()
        return max(memo_sim, desc_sim)

    ranked = sorted(candidates, key=similarity_score, reverse=True)
    return ranked[:limit]


def _build_prompt(
    transaction: Transaction,
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
        "description": "Descrição normalizada (sem CNPJs, códigos, números de loja)",
        "confidence": 0.9
    }}

    O campo "confidence" deve ser um float entre 0.0 e 1.0 indicando sua confiança na sugestão.
    """


def _call_ollama_api(prompt: str) -> dict | None:
    """Chama a API do Ollama e retorna a resposta parseada."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

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
    category = case_insensitive_get(
        Category.objects.all(), "name", data.get("category")
    )
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


def generate_suggestions_async(transaction_ids: list[int]) -> None:
    """
    Processa sugestões em background thread para não bloquear o request.
    Seguro para uso pessoal (app single-user).
    """

    def _worker():
        for tx_id in transaction_ids:
            try:
                tx = Transaction.objects.get(id=tx_id)
                generate_suggestion_for_transaction(tx)
                logger.info(f"Sugestão gerada async para transação {tx_id}")
            except Transaction.DoesNotExist:
                logger.warning(f"Transação {tx_id} não encontrada")
            except Exception as e:
                logger.error(f"Erro ao gerar sugestão async para {tx_id}: {e}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    logger.info(
        f"Thread de sugestões iniciada para {len(transaction_ids)} transação(ões)"
    )
