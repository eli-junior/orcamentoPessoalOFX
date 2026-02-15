import sys
from django.core.management.base import BaseCommand
from orcamento_2026.core.models import Transaction
from orcamento_2026.core.services.suggestions import generate_suggestion_for_transaction


class Command(BaseCommand):
    help = "Gera sugestões de IA para transações não consolidadas"

    def handle(self, *args, **options):
        # Busca transações sem despesa associada E sem sugestão pendente
        # transactions = Transaction.objects.filter(expense__isnull=True, suggestion__isnull=True).order_by('date')
        # Django 'suggestion__isnull=True' works for reverse OneToOne relation check

        pending_transactions = Transaction.objects.filter(expense__isnull=True).order_by("date")
        transactions_to_process = []

        # Filtrar as que já tem sugestão (embora o generate_suggestion_for_transaction já faça check,
        # é bom filtrar antes para contagem correta)
        for tx in pending_transactions:
            if not hasattr(tx, "suggestion"):
                transactions_to_process.append(tx)

        total = len(transactions_to_process)

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nenhuma transação pendente de sugestão."))
            return

        self.stdout.write(f"Gerando sugestões para {total} transações...")

        for idx, tx in enumerate(transactions_to_process, 1):
            self.stdout.write(f"[{idx}/{total}] Analisando: {tx.memo}...", ending="")
            sys.stdout.flush()

            suggestion = generate_suggestion_for_transaction(tx)

            if suggestion:
                self.stdout.write(self.style.SUCCESS(" OK"))
            else:
                self.stdout.write(self.style.WARNING(" Falha"))

        self.stdout.write(self.style.SUCCESS("\nGeração de sugestões concluída!"))
        self.stdout.write("Execute 'uv run manage.py consolidar' para revisar e aprovar as sugestões.")
