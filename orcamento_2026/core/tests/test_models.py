from datetime import date
from decimal import Decimal
import pytest
from django.db import IntegrityError
from orcamento_2026.core.models import Account, Category, SubCategory, Transaction, Expense


@pytest.mark.django_db
class TestAccountModel:
    def test_create_account(self):
        account = Account.objects.create(name="Nubank", type="C")
        assert account.name == "Nubank"
        assert account.type == "C"
        assert str(account) == "Nubank"


@pytest.mark.django_db
class TestCategoryModel:
    def test_create_category(self):
        category = Category.objects.create(name="Alimentação")
        assert category.name == "Alimentação"
        assert str(category) == "Alimentação"

    def test_category_unique_name(self):
        Category.objects.create(name="Transporte")
        with pytest.raises(IntegrityError):
            Category.objects.create(name="Transporte")


@pytest.mark.django_db
class TestSubCategoryModel:
    def test_create_subcategory(self):
        category = Category.objects.create(name="Lazer")
        subcategory = SubCategory.objects.create(category=category, name="Cinema")
        assert subcategory.name == "Cinema"
        assert subcategory.category == category
        assert str(subcategory) == "Lazer - Cinema"


@pytest.mark.django_db
class TestTransactionModel:
    def test_create_transaction(self):
        account = Account.objects.create(name="Itaú", type="C")
        transaction = Transaction.objects.create(
            fitid="12345", account=account, amount=Decimal("100.50"), date=date(2026, 2, 15), memo="Supermercado"
        )
        assert transaction.fitid == "12345"
        assert transaction.amount == Decimal("100.50")
        assert str(transaction) == "2026-02-15 - 100.50 (Supermercado)"

    def test_transaction_unique_fitid(self):
        account = Account.objects.create(name="Itaú", type="C")
        Transaction.objects.create(fitid="unique-id", account=account, amount=Decimal("10.00"), date=date(2026, 2, 15), memo="Teste 1")
        with pytest.raises(IntegrityError):
            Transaction.objects.create(fitid="unique-id", account=account, amount=Decimal("20.00"), date=date(2026, 2, 16), memo="Teste 2")


@pytest.mark.django_db
class TestExpenseModel:
    def test_create_expense(self):
        account = Account.objects.create(name="BB", type="C")
        category = Category.objects.create(name="Saúde")
        subcategory = SubCategory.objects.create(category=category, name="Farmácia")

        transaction = Transaction.objects.create(
            fitid="exp-1", account=account, amount=Decimal("-50.00"), date=date(2026, 2, 10), memo="Remédio"
        )

        expense = Expense.objects.create(
            transaction=transaction, description="Remédio Dor de Cabeça", subcategory=subcategory, reference_month=date(2026, 2, 1)
        )

        assert expense.transaction == transaction
        assert expense.subcategory == subcategory
        assert expense.description == "Remédio Dor de Cabeça"
        assert str(expense) == "Remédio Dor de Cabeça"
