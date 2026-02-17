from django.core.management.base import BaseCommand
from orcamento_2026.core.models import Category, SubCategory
from orcamento_2026.core.services.consolidation import consolidate_transaction, get_unconsolidated_transactions


class Command(BaseCommand):
    help = "Revisa e consolida transações com sugestões do Larry"

    def handle(self, *args, **options):
        # Alterado para buscar todas as transações não consolidadas, não apenas as com sugestão
        transactions = get_unconsolidated_transactions()
        total = transactions.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nenhuma transação pendente de consolidação."))
            return

        self.stdout.write(f"Iniciando revisão de {total} transações...")

        for idx, transaction in enumerate(transactions, 1):
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(f"Transação {idx}/{total}")
            self.stdout.write(f"Conta: {transaction.account.name}")
            self.stdout.write(f"Data: {transaction.date}")
            self.stdout.write(f"Valor: {transaction.amount}")
            self.stdout.write(f"Memo: {transaction.memo}")
            self.stdout.write("-" * 60)

            # Tenta pegar a sugestão se existir
            suggestion = getattr(transaction, "suggestion", None)

            if suggestion:
                self.stdout.write(self.style.SUCCESS("Sugestão do Larry:"))
                self.stdout.write(f"  Categoria:   {suggestion.category.name if suggestion.category else 'N/A'}")
                self.stdout.write(f"  Subcategoria:{suggestion.subcategory.name if suggestion.subcategory else 'N/A'}")
                self.stdout.write(f"  Descrição:   {suggestion.description}")
            else:
                self.stdout.write(self.style.WARNING("Sem sugestão do Larry."))

            while True:
                try:
                    self.stdout.write("\nOpções: [A]=Aceitar Sugestão, [E]=Editar/Inserir, [I]=Ignorar/Pular, [Q]=Sair")
                    if not suggestion:
                        self.stdout.write(self.style.NOTICE("Nota: Sem sugestão disponível. Use [E] para inserir dados."))

                    choice = input("Sua escolha: ").strip().upper()

                    if choice == "Q":
                        self.stdout.write("Encerrando revisão.")
                        return

                    if choice == "I":
                        self.stdout.write("Transação pulada.")
                        break

                    if choice == "A":
                        # Aceitar sugestão
                        if suggestion and suggestion.category and suggestion.subcategory and suggestion.description:
                            try:
                                consolidate_transaction(
                                    transaction,
                                    suggestion.category.name if suggestion.category else "",
                                    suggestion.subcategory.name if suggestion.subcategory else "",
                                    suggestion.description,
                                    transaction.reference_date,
                                )
                                self.stdout.write(self.style.SUCCESS("Consolidado e Aceito!"))
                                break
                            except ValueError as e:
                                self.stdout.write(self.style.ERROR(f"Erro ao consolidar: {e}"))
                                self.stdout.write("Dados da sugestão inválidos. Tente editar [E].")
                        else:
                            self.stdout.write(self.style.WARNING("Não há sugestão completa para aceitar. Use [E] para editar."))

                    if choice == "E":
                        # Editar
                        # Pre-fill com dados da sugestão se houver
                        current_cat = suggestion.category if suggestion and suggestion.category else None

                        category = self.select_category() or current_cat
                        subcategory = (
                            self.select_subcategory(category)
                            if category
                            else (suggestion.subcategory if suggestion and suggestion.subcategory else None)
                        )

                        desc_default = suggestion.description if suggestion and suggestion.description else ""
                        description = input(f"Descrição [{desc_default}]: ") or desc_default

                        ref_month = transaction.reference_date

                        try:
                            consolidate_transaction(
                                transaction,
                                category.name if category else "",
                                subcategory.name if subcategory else "",
                                description,
                                ref_month,
                            )
                            # Atualiza sugestão como editada/aceita se existir
                            if suggestion:
                                suggestion.status = "EDITED"
                                suggestion.save()

                            self.stdout.write(self.style.SUCCESS("Consolidado manualmente!"))
                            break
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Erro: {e}"))

                except KeyboardInterrupt:
                    self.stdout.write("\nOperação interrompida pelo usuário.")
                    return

    def select_category(self):
        categories = Category.objects.all().order_by("name")
        for i, cat in enumerate(categories, 1):
            self.stdout.write(f"{i}. {cat.name}")

        while True:
            try:
                inp = input("Escolha a Categoria (número): ")
                if not inp:
                    return None
                idx = int(inp)
                if 1 <= idx <= len(categories):
                    return categories[idx - 1]
            except ValueError:
                pass
            self.stdout.write(self.style.ERROR("Inválido."))

    def select_subcategory(self, category):
        if not category:
            return None
        subs = SubCategory.objects.filter(category=category).order_by("name")
        for i, sub in enumerate(subs, 1):
            self.stdout.write(f"{i}. {sub.name}")

        while True:
            try:
                inp = input("Escolha a Subcategoria (número): ")
                if not inp:
                    return None
                idx = int(inp)
                if 1 <= idx <= len(subs):
                    return subs[idx - 1]
            except ValueError:
                pass
            self.stdout.write(self.style.ERROR("Inválido."))
