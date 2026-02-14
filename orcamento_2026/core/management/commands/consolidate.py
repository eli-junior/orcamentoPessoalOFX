from django.core.management.base import BaseCommand
from orcamento_2026.core.services.consolidation import ConsolidationService


class Command(BaseCommand):
    help = "Consolidate pending transactions into expenses"

    def handle(self, *args, **kwargs):
        count = ConsolidationService.consolidate()
        self.stdout.write(self.style.SUCCESS(f"Successfully consolidated {count} transactions."))
