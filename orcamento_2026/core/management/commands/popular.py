from django.core.management.base import BaseCommand
from orcamento_2026.core.models import Account, Category, SubCategory


class Command(BaseCommand):
    help = "Popula o banco de dados com dados iniciais (Contas e Categorias)"

    def handle(self, *args, **options):
        self.stdout.write("Iniciando população de dados...")

        # 1. Contas
        accounts_data = [
            # Cartões (K)
            ("Visa BB", "K"),
            ("Master BB", "K"),
            ("Elo BB", "K"),
            ("Master Inter", "K"),
            # Corrente (C)
            ("BB CC Funci", "C"),
            ("Santander", "C"),
            ("Inter", "C"),
        ]

        for name, acc_type in accounts_data:
            obj, created = Account.objects.get_or_create(name=name, defaults={"type": acc_type})
            if created:
                self.stdout.write(self.style.SUCCESS(f"Conta criada: {name} ({acc_type})"))
            else:
                self.stdout.write(f"Conta já existente: {name}")

        # 2. Categorias e Subcategorias
        categories_data = [
            {"category": "Moradia", "subcategories": ["Aluguel", "Condomínio", "Energia", "Internet", "Manutenção", "Outros"]},
            {"category": "Alimentação", "subcategories": ["Supermercado", "Restaurante", "Ifood", "Lanches", "Outros"]},
            {"category": "Transporte", "subcategories": ["Combustível", "Uber", "Estacionamento", "Manutenção Veículo", "Outros"]},
            {"category": "Saúde", "subcategories": ["Farmácia", "Consultas", "Plano de Saúde", "Academia", "Outros"]},
            {"category": "Lazer", "subcategories": ["Cinema", "Viagem", "Streaming", "Jogos", "Outros"]},
            {"category": "Educação", "subcategories": ["Cursos", "Livros", "Material Escolar", "Outros"]},
            {"category": "Financeiro", "subcategories": ["Tarifas Bancárias", "Impostos", "Outros"]},
        ]

        for item in categories_data:
            cat_name = item["category"]
            category, created = Category.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Categoria criada: {cat_name}"))

            for sub_name in item["subcategories"]:
                sub, sub_created = SubCategory.objects.get_or_create(name=sub_name, category=category)
                if sub_created:
                    self.stdout.write(self.style.SUCCESS(f"  - Subcategoria criada: {sub_name}"))

        self.stdout.write(self.style.SUCCESS("População concluída com sucesso!"))
