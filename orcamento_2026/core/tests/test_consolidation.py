"""Testes para o serviço de consolidação."""

from datetime import date
from decimal import Decimal

import pytest

from orcamento_2026.core.models import (
    Account,
    Category,
    Expense,
    SubCategory,
    Transaction,
    TransactionSuggestion,
)
from orcamento_2026.core.services.consolidation import (
    consolidate_transaction,
    get_unconsolidated_transactions,
)


@pytest.mark.django_db
class TestGetUnconsolidatedTransactions:
    """Testes para get_unconsolidated_transactions."""

    def test_returns_only_unconsolidated(self):
        """Testa que retorna apenas transações não consolidadas."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        # Cria transação não consolidada
        tx_unconsolidated = Transaction.objects.create(
            fitid="unconsolidated",
            account=account,
            amount=Decimal("100.00"),
            date=date(2026, 2, 15),
            memo="Unconsolidated",
        )

        # Cria transação consolidada
        tx_consolidated = Transaction.objects.create(
            fitid="consolidated",
            account=account,
            amount=Decimal("200.00"),
            date=date(2026, 2, 16),
            memo="Consolidated",
        )
        Expense.objects.create(
            transaction=tx_consolidated,
            description="Already consolidated",
            subcategory=subcategory,
            reference_month=date(2026, 2, 1),
        )

        unconsolidated = get_unconsolidated_transactions()

        assert unconsolidated.count() == 1
        assert unconsolidated.first() == tx_unconsolidated

    def test_returns_empty_when_all_consolidated(self):
        """Testa que retorna queryset vazio quando todas estão consolidadas."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        tx = Transaction.objects.create(
            fitid="consolidated",
            account=account,
            amount=Decimal("100.00"),
            date=date(2026, 2, 15),
            memo="Consolidated",
        )
        Expense.objects.create(
            transaction=tx,
            description="Already consolidated",
            subcategory=subcategory,
            reference_month=date(2026, 2, 1),
        )

        unconsolidated = get_unconsolidated_transactions()
        assert unconsolidated.count() == 0

    def test_orders_by_date(self):
        """Testa que as transações são ordenadas por data."""
        account = Account.objects.create(name="Test", type="C")

        tx2 = Transaction.objects.create(
            fitid="tx2",
            account=account,
            amount=Decimal("200.00"),
            date=date(2026, 2, 20),
            memo="Later",
        )
        tx1 = Transaction.objects.create(
            fitid="tx1",
            account=account,
            amount=Decimal("100.00"),
            date=date(2026, 2, 10),
            memo="Earlier",
        )

        unconsolidated = list(get_unconsolidated_transactions())

        assert unconsolidated[0] == tx1
        assert unconsolidated[1] == tx2


@pytest.mark.django_db
class TestConsolidateTransaction:
    """Testes para consolidate_transaction."""

    def test_creates_expense_successfully(self):
        """Testa criação bem-sucedida de despesa."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="Alimentação")
        subcategory = SubCategory.objects.create(category=category, name="Supermercado")

        tx = Transaction.objects.create(
            fitid="test-tx",
            account=account,
            amount=Decimal("-150.00"),
            date=date(2026, 2, 15),
            memo="Supermercado XYZ",
        )

        expense = consolidate_transaction(
            transaction=tx,
            category_name="Alimentação",
            subcategory_name="Supermercado",
            description="Compras do mês",
            reference_month=date(2026, 2, 1),
        )

        assert Expense.objects.count() == 1
        assert expense.transaction == tx
        assert expense.subcategory == subcategory
        assert expense.description == "Compras do mês"
        assert expense.reference_month == date(2026, 2, 1)
        assert expense.is_ignored is False

    def test_case_insensitive_category_lookup(self):
        """Testa busca case-insensitive de categoria."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="Alimentação")
        SubCategory.objects.create(category=category, name="Supermercado")

        tx = Transaction.objects.create(
            fitid="test-tx",
            account=account,
            amount=Decimal("-150.00"),
            date=date(2026, 2, 15),
            memo="Test",
        )

        # Usa nome em caixa diferente
        expense = consolidate_transaction(
            transaction=tx,
            category_name="ALIMENTAÇÃO",  # Maiúsculo
            subcategory_name="SUPERMERCADO",  # Maiúsculo
            description="Test",
            reference_month=date(2026, 2, 1),
        )

        assert expense.subcategory.category == category

    def test_updates_suggestion_status_if_exists(self):
        """Testa que atualiza o status da sugestão se existir."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="Alimentação")
        subcategory = SubCategory.objects.create(category=category, name="Supermercado")

        tx = Transaction.objects.create(
            fitid="test-tx",
            account=account,
            amount=Decimal("-150.00"),
            date=date(2026, 2, 15),
            memo="Test",
        )

        # Cria sugestão
        suggestion = TransactionSuggestion.objects.create(
            transaction=tx,
            category=category,
            subcategory=subcategory,
            description="Test suggestion",
            status="PENDENTE",
        )

        consolidate_transaction(
            transaction=tx,
            category_name="Alimentação",
            subcategory_name="Supermercado",
            description="Consolidated",
            reference_month=date(2026, 2, 1),
        )

        suggestion.refresh_from_db()
        assert suggestion.status == "ACEITO"

    def test_raises_error_for_invalid_category(self):
        """Testa erro quando categoria não existe."""
        account = Account.objects.create(name="Test", type="C")

        tx = Transaction.objects.create(
            fitid="test-tx",
            account=account,
            amount=Decimal("-150.00"),
            date=date(2026, 2, 15),
            memo="Test",
        )

        with pytest.raises(ValueError, match="Categoria 'Inexistente' não encontrada"):
            consolidate_transaction(
                transaction=tx,
                category_name="Inexistente",
                subcategory_name="Teste",
                description="Test",
                reference_month=date(2026, 2, 1),
            )

    def test_raises_error_for_invalid_subcategory(self):
        """Testa erro quando subcategoria não existe."""
        account = Account.objects.create(name="Test", type="C")
        Category.objects.create(name="Alimentação")

        tx = Transaction.objects.create(
            fitid="test-tx",
            account=account,
            amount=Decimal("-150.00"),
            date=date(2026, 2, 15),
            memo="Test",
        )

        with pytest.raises(ValueError, match="Subcategoria 'Inexistente' não encontrada na categoria 'Alimentação'"):
            consolidate_transaction(
                transaction=tx,
                category_name="Alimentação",
                subcategory_name="Inexistente",
                description="Test",
                reference_month=date(2026, 2, 1),
            )

    def test_raises_error_for_subcategory_in_wrong_category(self):
        """Testa erro quando subcategoria existe mas em categoria diferente."""
        account = Account.objects.create(name="Test", type="C")
        cat1 = Category.objects.create(name="Alimentação")
        Category.objects.create(name="Transporte")
        SubCategory.objects.create(category=cat1, name="Supermercado")

        tx = Transaction.objects.create(
            fitid="test-tx",
            account=account,
            amount=Decimal("-150.00"),
            date=date(2026, 2, 15),
            memo="Test",
        )

        with pytest.raises(ValueError, match="Subcategoria 'Supermercado' não encontrada na categoria 'Transporte'"):
            consolidate_transaction(
                transaction=tx,
                category_name="Transporte",
                subcategory_name="Supermercado",
                description="Test",
                reference_month=date(2026, 2, 1),
            )
