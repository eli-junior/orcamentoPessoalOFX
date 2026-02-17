"""Testes para os management commands."""

from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from orcamento_2026.core.models import (
    Account,
    Category,
    SubCategory,
    Transaction,
    TransactionSuggestion,
)


@pytest.mark.django_db
class TestPopularCommand:
    """Testes para o comando 'popular'."""

    def test_creates_default_accounts(self):
        """Testa que cria as contas padrão."""
        out = StringIO()
        call_command("popular", stdout=out)

        # Verifica contas criadas
        accounts = Account.objects.all()
        account_names = [a.name for a in accounts]

        assert "Visa BB" in account_names
        assert "Master BB" in account_names
        assert "Elo BB" in account_names
        assert "Master Inter" in account_names
        assert "BB CC Funci" in account_names
        assert "Santander" in account_names
        assert "Inter" in account_names

        # Verifica tipos
        visa = Account.objects.get(name="Visa BB")
        assert visa.type == "K"

        bb = Account.objects.get(name="BB CC Funci")
        assert bb.type == "C"

    def test_creates_categories_and_subcategories(self):
        """Testa que cria categorias e subcategorias."""
        out = StringIO()
        call_command("popular", stdout=out)

        # Verifica categorias
        categories = Category.objects.all()
        category_names = [c.name for c in categories]

        assert "Moradia" in category_names
        assert "Alimentação" in category_names
        assert "Transporte" in category_names
        assert "Saúde" in category_names
        assert "Lazer" in category_names
        assert "Educação" in category_names
        assert "Financeiro" in category_names

        # Verifica subcategorias
        moradia = Category.objects.get(name="Moradia")
        subcats = SubCategory.objects.filter(category=moradia)
        subcat_names = [s.name for s in subcats]

        assert "Aluguel" in subcat_names
        assert "Condomínio" in subcat_names
        assert "Energia" in subcat_names

    def test_does_not_duplicate_existing(self):
        """Testa que não duplica dados existentes."""
        # Cria uma conta antes
        Account.objects.create(name="Visa BB", type="K")

        out = StringIO()
        call_command("popular", stdout=out)

        # Deve ter apenas uma conta Visa BB
        assert Account.objects.filter(name="Visa BB").count() == 1

    def test_outputs_success_message(self):
        """Testa que exibe mensagem de sucesso."""
        out = StringIO()
        call_command("popular", stdout=out)

        output = out.getvalue()
        assert "População concluída com sucesso" in output


@pytest.mark.django_db
class TestImportarCommand:
    """Testes para o comando 'importar'."""

    @patch("orcamento_2026.core.management.commands.importar.shutil.move")
    @patch("orcamento_2026.core.management.commands.importar.import_ofx")
    @patch("os.listdir")
    @patch("os.path.exists")
    @patch("builtins.input")
    def test_imports_selected_file(self, mock_input, mock_exists, mock_listdir, mock_import_ofx, mock_move):
        """Testa importação de arquivo selecionado."""
        mock_exists.return_value = True
        mock_listdir.return_value = ["extrato.ofx"]
        mock_input.side_effect = ["1", "1", "2", "N"]  # arquivo, conta, data, não gerar sugestões

        mock_import_ofx.return_value = {"transactions_created": 5}

        # Cria conta
        Account.objects.create(name="Test", type="C")

        out = StringIO()
        call_command("importar", stdout=out)

        mock_import_ofx.assert_called_once()
        output = out.getvalue()
        assert "Sucesso! 5 transações novas" in output

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_shows_warning_when_no_files(self, mock_listdir, mock_exists):
        """Testa aviso quando não há arquivos."""
        mock_exists.return_value = True
        mock_listdir.return_value = []

        out = StringIO()
        call_command("importar", stdout=out)

        assert "Nenhum arquivo .ofx encontrado" in out.getvalue()

    @patch("os.path.exists")
    @patch("os.makedirs")
    def test_creates_directories_if_not_exist(self, mock_makedirs, mock_exists):
        """Testa criação de diretórios quando não existem."""
        mock_exists.return_value = False

        with patch("os.listdir") as mock_listdir:
            mock_listdir.return_value = []
            out = StringIO()
            call_command("importar", stdout=out)

        # Verifica que makedirs foi chamado
        assert mock_makedirs.called


@pytest.mark.django_db
class TestSugerirCommand:
    """Testes para o comando 'sugerir'."""

    @patch("orcamento_2026.core.management.commands.sugerir.generate_suggestion_for_transaction")
    def test_generates_suggestions_for_pending(self, mock_generate):
        """Testa geração de sugestões para transações pendentes."""
        account = Account.objects.create(name="Test", type="C")

        # Cria transações sem sugestão
        Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 2, 15), memo="Test 1")
        Transaction.objects.create(fitid="tx2", account=account, amount=Decimal("200.00"), date=date(2026, 2, 16), memo="Test 2")

        mock_generate.return_value = MagicMock()

        out = StringIO()
        call_command("sugerir", stdout=out)

        assert mock_generate.call_count == 2
        output = out.getvalue()
        assert "Geração de sugestões concluída" in output

    @patch("orcamento_2026.core.management.commands.sugerir.generate_suggestion_for_transaction")
    def test_skips_transactions_with_suggestions(self, mock_generate):
        """Testa que pula transações que já têm sugestões."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        tx = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 2, 15), memo="Test 1")
        # Cria sugestão existente
        TransactionSuggestion.objects.create(
            transaction=tx, category=category, subcategory=subcategory, description="Existing", status="PENDENTE"
        )

        out = StringIO()
        call_command("sugerir", stdout=out)

        mock_generate.assert_not_called()
        assert "Nenhuma transação pendente de sugestão" in out.getvalue()

    def test_shows_success_when_none_pending(self):
        """Testa mensagem quando não há transações pendentes."""
        out = StringIO()
        call_command("sugerir", stdout=out)

        assert "Nenhuma transação pendente de sugestão" in out.getvalue()


@pytest.mark.django_db
class TestConsolidarCommand:
    """Testes para o comando 'consolidar'."""

    def test_shows_success_when_none_pending(self):
        """Testa mensagem quando não há transações para consolidar."""
        out = StringIO()
        call_command("consolidar", stdout=out)

        assert "Nenhuma transação pendente de consolidação" in out.getvalue()

    @patch("builtins.input")
    @patch("orcamento_2026.core.management.commands.consolidar.consolidate_transaction")
    def test_accepts_suggestion_option(self, mock_consolidate, mock_input):
        """Testa opção de aceitar sugestão."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        tx = Transaction.objects.create(
            fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 2, 15), memo="Test 1", reference_date=date(2026, 2, 1)
        )
        TransactionSuggestion.objects.create(
            transaction=tx, category=category, subcategory=subcategory, description="Suggested Description", status="PENDENTE"
        )

        mock_input.side_effect = ["A", "Q"]  # Aceitar, depois sair
        mock_consolidate.return_value = MagicMock()

        out = StringIO()
        call_command("consolidar", stdout=out)

        mock_consolidate.assert_called_once()
        assert "Consolidado e Aceito" in out.getvalue()

    @patch("builtins.input")
    def test_ignores_transaction_option(self, mock_input):
        """Testa opção de ignorar transação."""
        account = Account.objects.create(name="Test", type="C")

        Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 2, 15), memo="Test 1")

        mock_input.side_effect = ["I", "Q"]  # Ignorar, depois sair

        out = StringIO()
        call_command("consolidar", stdout=out)

        assert "Transação pulada" in out.getvalue()

    @patch("builtins.input")
    def test_quit_option(self, mock_input):
        """Testa opção de sair."""
        account = Account.objects.create(name="Test", type="C")

        Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 2, 15), memo="Test 1")

        mock_input.side_effect = ["Q"]  # Sair imediatamente

        out = StringIO()
        call_command("consolidar", stdout=out)

        assert "Encerrando revisão" in out.getvalue()
