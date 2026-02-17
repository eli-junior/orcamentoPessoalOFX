"""Serviço de consolidação de transações em despesas."""

import logging
from datetime import date
from typing import TYPE_CHECKING

from decouple import config

from orcamento_2026.core.services.utils.db_utils import case_insensitive_get

if TYPE_CHECKING:
    from orcamento_2026.core.models import Expense, Transaction

logger = logging.getLogger(__name__)

OLLAMA_URL: str = config("OLLAMA_URL", default="http://localhost:11434")
OLLAMA_MODEL: str = config("OLLAMA_MODEL", default="qwen2.5:1.5b")


def get_unconsolidated_transactions() -> Transaction.QuerySet:
    """Retorna transações que ainda não possuem despesa associada."""
    from orcamento_2026.core.models import Transaction

    return Transaction.objects.filter(expense__isnull=True).order_by("date")


def consolidate_transaction(
    transaction: "Transaction",
    category_name: str,
    subcategory_name: str,
    description: str,
    reference_month: date,
) -> "Expense":
    """
    Cria a despesa associada à transação.

    Args:
        transaction: Transação a ser consolidada
        category_name: Nome da categoria
        subcategory_name: Nome da subcategoria
        description: Descrição da despesa
        reference_month: Mês de referência

    Returns:
        A despesa criada

    Raises:
        ValueError: Se categoria ou subcategoria não forem encontradas
    """
    from orcamento_2026.core.models import Category, Expense, SubCategory

    category = case_insensitive_get(Category.objects.all(), "name", category_name)
    if not category:
        error_msg = f"Categoria '{category_name}' não encontrada"
        logger.error(error_msg)
        raise ValueError(error_msg)

    subcategory = case_insensitive_get(
        SubCategory.objects.filter(category=category),
        "name",
        subcategory_name,
    )
    if not subcategory:
        error_msg = f"Subcategoria '{subcategory_name}' não encontrada na categoria '{category_name}'"
        logger.error(error_msg)
        raise ValueError(error_msg)

    expense = Expense.objects.create(
        transaction=transaction,
        description=description,
        subcategory=subcategory,
        reference_month=reference_month,
        is_ignored=False,
    )

    # Atualiza status da sugestão se existir
    if hasattr(transaction, "suggestion"):
        transaction.suggestion.status = "ACEITO"
        transaction.suggestion.save()
        logger.info(f"Sugestão aceita para transação {transaction.id}")

    logger.info(f"Transação {transaction.id} consolidada como despesa {expense.id}")
    return expense
