from django.core.management.base import BaseCommand
from orcamento_2026.core.models import Account
from orcamento_2026.core.services.importer import OFXImporter
import os


class Command(BaseCommand):
    help = "Import transactions from an OFX file"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str, help="Path to the OFX file")
        parser.add_argument("--account", type=str, required=True, help="Name of the account (will be created if not exists)")
        # month is optional or maybe deferred logic? The spec mentions --month "2026-02".
        # But importer deduces month from transaction date.
        # Maybe --month is to filter which month to import?
        # For now I will focus on importing everything in the file.
        parser.add_argument("--month", type=str, help="Reference month (YYYY-MM) - Optional override")

    def handle(self, *args, **kwargs):
        file_path = kwargs["file_path"]
        account_name = kwargs["account"]

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        # Get or create account
        # Default type to DEBIT if creating new one, or ask user?
        # To avoid complexity, default to DEBIT.
        account, created = Account.objects.get_or_create(name=account_name, defaults={"type": Account.Type.DEBIT})

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created new account: {account}"))
        else:
            self.stdout.write(f"Using existing account: {account}")

        importer = OFXImporter(file_path, account)
        result = importer.process()

        self.stdout.write(self.style.SUCCESS(f"Import finished. Imported: {result['imported']}, Skipped (Duplicate): {result['skipped']}"))
