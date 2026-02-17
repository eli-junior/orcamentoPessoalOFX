import logging
from decimal import Decimal
from datetime import date

from ofxparse import OfxParser

from orcamento_2026.core.models import Account, Transaction

logger = logging.getLogger(__name__)


def import_ofx(file_path: str, account: Account, reference_date: date = None):
    """
    Importa transações de um arquivo OFX para uma conta específica.
    """
    with open(file_path, "rb") as f:
        ofx = OfxParser.parse(f)

    new_transactions_count = 0

    for tx in ofx.account.statement.transactions:
        # ofxparse retorna amount como float ou decimal, garantimos Decimal
        amount = Decimal(str(tx.amount))
        date_obj = tx.date.date()

        # Cria a transação se não existir (baseado no fitid)
        # O FITID é a chave para evitar duplicatas
        _, created = Transaction.objects.get_or_create(
            fitid=tx.id,
            defaults={"account": account, "amount": amount, "date": date_obj, "memo": tx.memo or "", "reference_date": reference_date},
        )

        if created:
            new_transactions_count += 1

    return {"transactions_created": new_transactions_count}
