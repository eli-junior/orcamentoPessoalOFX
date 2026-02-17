"""Serviço de importação de arquivos OFX."""

import logging
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from ofxparse import OfxParser

if TYPE_CHECKING:
    from orcamento_2026.core.models import Account

logger = logging.getLogger(__name__)


def import_ofx(file_path: str, account: "Account", reference_date: date | None = None) -> dict[str, int]:
    """
    Importa transações de um arquivo OFX para uma conta específica.

    Args:
        file_path: Caminho do arquivo OFX
        account: Conta para associar as transações
        reference_date: Data de referência opcional

    Returns:
        Dicionário com estatísticas da importação
    """
    with open(file_path, "rb") as f:
        ofx = OfxParser.parse(f)

    new_transactions_count = 0

    for tx in ofx.account.statement.transactions:
        # ofxparse retorna amount como float ou decimal, garantimos Decimal
        amount = Decimal(str(tx.amount))
        date_obj: date = tx.date.date()

        # Cria a transação se não existir (baseado no fitid)
        # O FITID é a chave para evitar duplicatas
        _, created = account.transaction_set.get_or_create(
            fitid=tx.id,
            defaults={"amount": amount, "date": date_obj, "memo": tx.memo or "", "reference_date": reference_date},
        )

        if created:
            new_transactions_count += 1
            logger.debug(f"Transação criada: {tx.id} - {amount} - {tx.memo}")

    logger.info(f"Importação concluída: {new_transactions_count} novas transações")
    return {"transactions_created": new_transactions_count}
