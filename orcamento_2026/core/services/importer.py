import logging
from datetime import date

from django.db import IntegrityError
from ofxtools.Parser import OFXTree

from orcamento_2026.core.models import Account, Transaction

logger = logging.getLogger(__name__)


class OFXImporter:
    def __init__(self, file_path, account: Account):
        self.file_path = file_path
        self.account = account

    def process(self):
        parser = OFXTree()
        parser.parse(self.file_path)
        ofx = parser.convert()

        # Assuming single bank account in OFX for simplicity,
        # but iterating through statements just in case.
        # ofxtools structure can be complex, usually:
        # ofx.bankmsgsrsv1.stmttrnrs.stmtrs.banktranlist

        statements = ofx.statements

        imported_count = 0
        skipped_count = 0

        for stmt in statements:
            # Check if currency matches? For now assume BRL.

            transactions = stmt.transactions

            for trx in transactions:
                # trx has: fitid, dtposted, trnamt, name, memo

                # Convert amount
                amount = trx.trnamt

                # Check for negative amount (Expense) or positive (Income)
                # Spec says: "Se não existir e for um valor negativo (despesa), salvar em Transaction".
                # But usually we import everything and filter later?
                # The spec explicitly says: "Se não existir e for um valor negativo (despesa), salvar em Transaction."
                # I will follow spec, but maybe log income skipped?
                # Actually, credit card payments are positive in OFX for the credit card account?
                # Let's stick to "import all" or "import expenses"?
                # Spec: "Se não existir e for um valor negativo (despesa), salvar em Transaction."
                # This might mean ignoring income (salary).
                # I'll implement exactly as spec for now, but add a comment.

                if amount >= 0:
                    logger.info(f"Skipping positive transaction (Income/Payment): {trx.fitid} - {amount}")
                    continue

                fitid = trx.fitid
                dtposted = trx.dtposted.date()
                memo = trx.memo or trx.name

                # Reference month: first day of the month of the transaction
                reference_month = date(dtposted.year, dtposted.month, 1)

                try:
                    Transaction.objects.create(
                        external_id=fitid,
                        amount=amount,
                        date=dtposted,
                        memo=memo,
                        account=self.account,
                        reference_month=reference_month,
                    )
                    imported_count += 1
                except IntegrityError:
                    # Duplicate FITID
                    skipped_count += 1
                    logger.info(f"Duplicate transaction found: {fitid}")

        return {
            "imported": imported_count,
            "skipped": skipped_count,
        }
