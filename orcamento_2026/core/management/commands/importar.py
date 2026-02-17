import os
import shutil
import traceback
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from orcamento_2026.core.models import Account
from orcamento_2026.core.services.import_ofx import import_ofx


from orcamento_2026.core.services.utils.date_utils import get_period_options


class Command(BaseCommand):
    help = "Importa arquivos OFX do diretório 'dados/' e gera sugestões de IA"

    def handle(self, *args, **options):
        try:
            base_dir = settings.BASE_DIR
            path_dados = os.path.join(base_dir, "dados")
            path_procesados = os.path.join(path_dados, "processados")

            if not os.path.exists(path_dados):
                os.makedirs(path_dados)
            if not os.path.exists(path_procesados):
                os.makedirs(path_procesados)

            files = [f for f in os.listdir(path_dados) if f.lower().endswith(".ofx")]

            if not files:
                self.stdout.write(self.style.WARNING("Nenhum arquivo .ofx encontrado na pasta 'dados'."))
                return

            self.stdout.write("Arquivos encontrados:")
            for i, f in enumerate(files, 1):
                self.stdout.write(f"{i}. {f}")

            try:
                choice = int(input("Escolha o arquivo para importar (número): "))
                if choice < 1 or choice > len(files):
                    self.stdout.write(self.style.ERROR("Opção inválida."))
                    return
                selected_file = files[choice - 1]
            except ValueError:
                self.stdout.write(self.style.ERROR("Entrada inválida."))
                return

            file_path = os.path.join(path_dados, selected_file)

            # 2. Selecionar ou criar conta
            accounts = Account.objects.all()
            if accounts.exists():
                self.stdout.write("\nContas existentes:")
                for i, acc in enumerate(accounts, 1):
                    self.stdout.write(f"{i}. {acc.name} ({acc.get_type_display()})")
                self.stdout.write(f"{len(accounts) + 1}. Criar nova conta")

                try:
                    acc_choice = int(input("Escolha a conta: "))
                    if 1 <= acc_choice <= len(accounts):
                        account = accounts[acc_choice - 1]
                    elif acc_choice == len(accounts) + 1:
                        account = self.create_account()
                    else:
                        self.stdout.write(self.style.ERROR("Opção inválida."))
                        return
                except ValueError:
                    self.stdout.write(self.style.ERROR("Entrada inválida."))
                    return
            else:
                self.stdout.write("\nNenhuma conta encontrada. Vamos criar uma.")
                account = self.create_account()

            # 3. Selecionar Data de Referência
            self.stdout.write("\nSelecione a Data de Referência (Competência):")
            period_options = get_period_options()
            for i, (date_val, label) in enumerate(period_options, 1):
                self.stdout.write(f"{i}. {label}")

            try:
                # Default para opção 2 (Mês Corrente - índice 1 do array, mas opção 2 no input)
                date_choice_input = input(f"Escolha a opção (Padrão 2 - {period_options[1][1]}): ")
                if not date_choice_input:
                    date_choice = 2
                else:
                    date_choice = int(date_choice_input)

                if 1 <= date_choice <= len(period_options):
                    reference_date = period_options[date_choice - 1][0]
                else:
                    self.stdout.write(self.style.ERROR("Opção inválida. Usando mês corrente."))
                    reference_date = period_options[1][0]
            except ValueError:
                self.stdout.write(self.style.ERROR("Entrada inválida. Usando mês corrente."))
                reference_date = period_options[1][0]

            # 4. Executar importação
            self.stdout.write(f"\nImportando '{selected_file}' para conta '{account.name}' com referência {reference_date}...")

            try:
                result = import_ofx(file_path, account, reference_date)
                new_tx_count = result["transactions_created"]
                self.stdout.write(self.style.SUCCESS(f"Sucesso! {new_tx_count} transações novas."))

                new_filename = f"{reference_date.strftime('%Y%m%d')}_{selected_file}"
                shutil.move(file_path, os.path.join(path_procesados, new_filename))

                # 5. Perguntar se deseja gerar sugestões agora
                if new_tx_count > 0:
                    self.stdout.write("\n" + "=" * 50)
                    while True:
                        answer = input("Deseja gerar sugestões do Larry para as novas transações agora? (S/N): ").upper()
                        if answer in ["S", "N"]:
                            break

                    if answer == "S":
                        try:
                            call_command("sugerir")
                        except KeyboardInterrupt:
                            self.stdout.write("Operação cancelada pelo usuário.")
                    else:
                        self.stdout.write("Ok. Você pode gerar depois com 'uv run manage.py sugerir'.")
                else:
                    self.stdout.write("Nenhuma transação nova para analisar.")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro na importação: {e}"))
                if settings.DEBUG:
                    traceback.print_exc()
        except KeyboardInterrupt:
            self.stdout.write("\nImportação cancelada pelo usuário.")

    def create_account(self):
        name = input("Nome da nova conta: ")
        while True:
            type_choice = input("Tipo (C=Corrente, K=Cartão): ").upper()
            if type_choice in ["C", "K"]:
                break
            self.stdout.write("Tipo inválido.")
        return Account.objects.create(name=name, type=type_choice)
