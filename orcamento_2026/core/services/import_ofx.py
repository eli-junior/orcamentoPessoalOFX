import logging
from datetime import date
from decimal import Decimal

from ofxparse import OfxParser

from orcamento_2026.core.models import Account, Category, Expense, SubCategory, Transaction

logger = logging.getLogger(__name__)


def import_ofx(file_path: str, account: Account, reference_month: date):
    """
    Importa transações de um arquivo OFX para uma conta específica.
    """
    with open(file_path, "rb") as f:
        ofx = OfxParser.parse(f)

    # Garante categoria e subcategoria padrão para despesas nao categorizadas
    category, _ = Category.objects.get_or_create(name="Sem Categoria")
    subcategory, _ = SubCategory.objects.get_or_create(name="Sem Subcategoria", category=category)

    new_transactions_count = 0
    new_expenses_count = 0

    for tx in ofx.account.statement.transactions:
        # ofxparse retorna amount como float ou decimal, garantimos Decimal
        amount = Decimal(str(tx.amount))
        date_obj = tx.date.date()

        # Cria a transação se não existir (baseado no fitid)
        transaction, created = Transaction.objects.get_or_create(
            fitid=tx.id, defaults={"account": account, "amount": amount, "date": date_obj, "memo": tx.memo or ""}
        )

        if created:
            new_transactions_count += 1

            # Se for despesa (valor negativo), cria o objeto Expense
            if amount < 0:
                Expense.objects.create(
                    transaction=transaction,
                    description=tx.memo or "Despesa Importada",
                    subcategory=subcategory,
                    reference_month=reference_month,
                    is_ignored=False,
                )
                new_expenses_count += 1

    return {"transactions_created": new_transactions_count, "expenses_created": new_expenses_count}
