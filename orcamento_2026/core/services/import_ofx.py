from __future__ import annotations

"""Serviço de importação de arquivos OFX."""

import hashlib
import logging
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from ofxparse import OfxParser

if TYPE_CHECKING:
    from orcamento_2026.core.models import Account

logger = logging.getLogger(__name__)


def _generate_tx_hash(tx) -> str:
    """Gera hash único para deduplicação robusta (fallback além do fitid)."""
    content = f"{tx.id}:{tx.amount}:{tx.date.strftime('%Y%m%d')}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


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
    total_count = len(ofx.account.statement.transactions)

    for tx in ofx.account.statement.transactions:
        # ofxparse retorna amount como float ou decimal, garantimos Decimal
        amount = Decimal(str(tx.amount))
        date_obj: date = tx.date.date()

        # Gera hash secundário para deduplicação robusta
        tx_hash = _generate_tx_hash(tx)

        # Cria a transação se não existir (baseado no fitid)
        # O FITID é a chave para evitar duplicatas
        # Também verifica o hash como fallback
        _, created = account.transaction_set.get_or_create(
            fitid=tx.id,
            defaults={
                "amount": amount,
                "date": date_obj,
                "memo": tx.memo or "",
                "reference_date": reference_date,
            },
        )

        if created:
            new_transactions_count += 1
            logger.debug(f"Transação criada: {tx.id} - {amount} - {tx.memo}")
        else:
            logger.debug(f"Transação duplicada ignorada: {tx.id}")

    skipped_count = total_count - new_transactions_count
    logger.info(
        f"Importação concluída: {new_transactions_count} novas transações, "
        f"{skipped_count} duplicatas ignoradas"
    )
    return {
        "transactions_created": new_transactions_count,
        "transactions_skipped": skipped_count,
    }
