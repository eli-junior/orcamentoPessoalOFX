from django.core.management.base import BaseCommand
from orcamento_2026.core.models import Category, SubCategory
from orcamento_2026.core.services.consolidation import consolidate_transaction
from orcamento_2026.core.services.suggestions import get_pending_suggestions

import date


class Command(BaseCommand):
    help = "Revisa e consolida transações com sugestões do Larry"

    def handle(self, *args, **options):
        suggestions = get_pending_suggestions()
        total = suggestions.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nenhuma sugestão pendente de revisão."))
            return

        self.stdout.write(f"Iniciando revisão de {total} sugestões...")

        for idx, suggestion in enumerate(suggestions, 1):
            transaction = suggestion.transaction
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(f"Sugestão {idx}/{total}")
            self.stdout.write(f"Conta: {transaction.account.name}")
            self.stdout.write(f"Data: {transaction.date}")
            self.stdout.write(f"Valor: {transaction.amount}")
            self.stdout.write(f"Memo: {transaction.memo}")
            self.stdout.write("-" * 60)

            self.stdout.write(self.style.SUCCESS("Sugestão do Larry:"))
            self.stdout.write(f"  Categoria:   {suggestion.category.name if suggestion.category else 'N/A'}")
            self.stdout.write(f"  Subcategoria:{suggestion.subcategory.name if suggestion.subcategory else 'N/A'}")
            self.stdout.write(f"  Descrição:   {suggestion.description}")

            while True:
                self.stdout.write("\nOpções: [Enter]=Aceitar, [E]=Editar, [I]=Ignorar/Pular, [Q]=Sair")
                choice = input("Sua escolha: ").strip().lower()

                if choice == "q":
                    self.stdout.write("Encerrando revisão.")
                    return

                if choice == "i":
                    self.stdout.write("Sugestão pulada.")
                    break

                if choice == "":
                    # Aceitar sugestão
                    try:
                        # Define referência como o dia 1 do mês da transação
                        ref_month = transaction.date.replace(day=1)
                        consolidate_transaction(
                            transaction,
                            suggestion.category.name if suggestion.category else "",
                            suggestion.subcategory.name if suggestion.subcategory else "",
                            suggestion.description,
                            ref_month,
                        )
                        self.stdout.write(self.style.SUCCESS("Consolidado e Aceito!"))
                        break
                    except ValueError as e:
                        self.stdout.write(self.style.ERROR(f"Erro ao consolidar: {e}"))
                        self.stdout.write("Dados da sugestão inválidos. Por favor, edite.")

                if choice == "e":
                    # Editar
                    category = self.select_category() or (suggestion.category if suggestion.category else None)
                    subcategory = self.select_subcategory(category) if category else None

                    desc_default = suggestion.description if suggestion.description else ""
                    description = input(f"Descrição [{desc_default}]: ") or desc_default

                    # Confirmar mês de referência
                    default_ref = transaction.date.replace(day=1)
                    ref_input = input(f"Mês de Referência (YYYY-MM-DD) [{default_ref}]: ")
                    if ref_input:
                        try:
                            ref_month = date.fromisoformat(ref_input)
                        except ValueError:
                            self.stdout.write(self.style.ERROR("Data inválida. Usando padrão."))
                            ref_month = default_ref
                    else:
                        ref_month = default_ref

                    try:
                        consolidate_transaction(
                            transaction, category.name if category else "", subcategory.name if subcategory else "", description, ref_month
                        )
                        # Atualiza sugestão como editada/aceita (já feito no consolidate_transaction, mas status pode ser refinado)
                        suggestion.status = "EDITED"
                        suggestion.save()

                        self.stdout.write(self.style.SUCCESS("Consolidado manualmente!"))
                        break
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Erro: {e}"))

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
