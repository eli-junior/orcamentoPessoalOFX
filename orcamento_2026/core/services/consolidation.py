from decouple import config
import logging
from orcamento_2026.core.models import Transaction, Expense, Category, SubCategory

logger = logging.getLogger(__name__)

OLLAMA_URL = config("OLLAMA_URL", default="http://localhost:11434")
OLLAMA_MODEL = config("OLLAMA_MODEL", default="qwen2.5:1.5b")


def get_unconsolidated_transactions():
    """Retorna transações que ainda não possuem despesa associada."""
    return Transaction.objects.filter(expense__isnull=True).order_by("date")


def consolidate_transaction(transaction, category_name, subcategory_name, description, reference_month):
    """
    Cria a despesa associada à transação.
    """
    try:
        category = Category.objects.get(name__iexact=category_name)
        subcategory = SubCategory.objects.get(name__iexact=subcategory_name, category=category)

        expense = Expense.objects.create(
            transaction=transaction, description=description, subcategory=subcategory, reference_month=reference_month, is_ignored=False
        )

        # Atualiza status da sugestão se existir
        if hasattr(transaction, "suggestion"):
            transaction.suggestion.status = "ACCEPTED"
            transaction.suggestion.save()

        return expense
    except (Category.DoesNotExist, SubCategory.DoesNotExist) as e:
        logger.error(f"Categoria ou Subcategoria não encontrada: {e}")
        raise ValueError(f"Categoria '{category_name}' ou Subcategoria '{subcategory_name}' inválida.")
