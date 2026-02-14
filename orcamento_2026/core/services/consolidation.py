import logging
from orcamento_2026.core.models import Transaction, Expense

logger = logging.getLogger(__name__)


class ConsolidationService:
    @staticmethod
    def consolidate():
        """
        Consolidates pending transactions into expenses.
        """
        pending_transactions = Transaction.objects.filter(expense__isnull=True)
        created_count = 0

        for trx in pending_transactions:
            # Basic logic: Create Expense with description = memo
            # Future: Apply regex rules or ML to categorize automatically

            try:
                Expense.objects.create(
                    transaction=trx,
                    description=trx.memo or "Sem descrição",
                    # category=None,
                    # subcategory=None,
                    is_ignored=False,
                )
                created_count += 1
            except Exception as e:
                logger.error(f"Failed to consolidate transaction {trx.id}: {e}")

        return created_count
