import os
import shutil
import traceback
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from orcamento_2026.core.models import Account
from orcamento_2026.core.services.import_ofx import import_ofx


class Command(BaseCommand):
    help = "Importa arquivos OFX da pasta dados para o banco de dados"

    def handle(self, *args, **options):
        # 1. Verificar e listar arquivos
        path_dados = os.path.join(settings.BASE_DIR, "dados")
        path_procesados = os.path.join(path_dados, "procesados")
        if not os.path.exists(path_dados):
            os.makedirs(path_dados, exist_ok=True)
            os.makedirs(path_procesados, exist_ok=True)
            self.stdout.write(self.style.WARNING(f"Pasta '{path_dados}' criada. Coloque seus arquivos .ofx lá."))
            return

        arquivos = [f for f in os.listdir(path_dados) if f.lower().endswith(".ofx")]
        if not arquivos:
            self.stdout.write(self.style.WARNING("Nenhum arquivo .ofx encontrado na pasta dados."))
            return

        self.stdout.write("Arquivos disponíveis:")
        for idx, arquivo in enumerate(arquivos, 1):
            self.stdout.write(f"{idx}. {arquivo}")

        while True:
            try:
                choice = int(input("Escolha o número do arquivo para importar: "))
                if 1 <= choice <= len(arquivos):
                    selected_file = arquivos[choice - 1]
                    break
                else:
                    self.stdout.write(self.style.ERROR("Número inválido."))
            except ValueError:
                self.stdout.write(self.style.ERROR("Por favor, digite um número."))

        file_path = os.path.join(path_dados, selected_file)

        # 2. Selecionar ou criar conta
        accounts = Account.objects.all()
        if accounts.exists():
            self.stdout.write("\nContas disponíveis:")
            for acc in accounts:
                self.stdout.write(f"ID: {acc.id} - Nome: {acc.name} ({acc.get_type_display()})")

            self.stdout.write("0. Criar nova conta")

            while True:
                try:
                    acc_choice = int(input("Escolha o ID da conta (ou 0 para criar): "))
                    if acc_choice == 0:
                        account = self.create_account()
                        break
                    else:
                        try:
                            account = Account.objects.get(id=acc_choice)
                            break
                        except Account.DoesNotExist:
                            self.stdout.write(self.style.ERROR("Conta não encontrada."))
                except ValueError:
                    self.stdout.write(self.style.ERROR("Entrada inválida."))
        else:
            self.stdout.write("\nNenhuma conta encontrada. Vamos criar uma.")
            account = self.create_account()

        # 3. Selecionar mês de referência
        today = date.today()
        first_current = today.replace(day=1)

        # Mês anterior
        last_month = first_current - timedelta(days=1)
        first_previous = last_month.replace(day=1)

        # Próximo mês
        # Adiciona 32 dias para garantir que caia no próximo mês, depois ajusta para dia 1
        next_month_date = first_current + timedelta(days=32)
        first_next = next_month_date.replace(day=1)

        months = {1: first_previous, 2: first_current, 3: first_next}

        self.stdout.write("\nPara qual mês de referência esta importação pertence?")
        self.stdout.write(f"1. Mês Anterior ({first_previous.strftime('%Y-%m')})")
        self.stdout.write(f"2. Mês Atual ({first_current.strftime('%Y-%m')})")
        self.stdout.write(f"3. Próximo Mês ({first_next.strftime('%Y-%m')})")

        while True:
            try:
                period_choice = int(input("Escolha o período (1-3): "))
                if period_choice in months:
                    reference_month = months[period_choice]
                    break
                else:
                    self.stdout.write(self.style.ERROR("Opção inválida."))
            except ValueError:
                self.stdout.write(self.style.ERROR("Entrada inválida."))

        # 4. Executar importação
        self.stdout.write(f"\nImportando '{selected_file}' para conta '{account.name}' com referência {reference_month}...")

        try:
            result = import_ofx(file_path, account, reference_month)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sucesso! {result['transactions_created']} transações novas, {result['expenses_created']} despesas criadas."
                )
            )
            shutil.move(file_path, os.path.join(path_procesados, selected_file))

        except Exception as e:
            # Em caso de erro, logar e exibir
            self.stdout.write(self.style.ERROR(f"Erro na importação: {e}"))
            if settings.DEBUG:
                traceback.print_exc()

    def create_account(self):
        """Helper para criar uma nova conta via CLI"""
        self.stdout.write("\n--- Nova Conta ---")
        name = input("Nome da conta: ").strip()
        while not name:
            name = input("O nome não pode ser vazio. Nome da conta: ").strip()

        self.stdout.write("Tipo da conta:")
        self.stdout.write("C - Corrente")
        self.stdout.write("K - Cartão")

        ac_type = input("Escolha o tipo (C/K): ").strip().upper()
        while ac_type not in ("C", "K"):
            ac_type = input("Tipo inválido. Escolha C ou K: ").strip().upper()

        return Account.objects.create(name=name, type=ac_type)
