import pytest
from datetime import date
from decimal import Decimal
from django.core.management import call_command
from orcamento_2026.core.models import Account, Transaction, Expense, Category, SubCategory
from orcamento_2026.core.services.consolidation import ConsolidationService


@pytest.mark.django_db
class TestBusinessLogic:
    @pytest.fixture
    def account(self):
        return Account.objects.create(name="Test Bank", type=Account.Type.DEBIT)

    @pytest.fixture
    def category(self):
        cat = Category.objects.create(name="Food")
        SubCategory.objects.create(name="Groceries", category=cat)
        return cat

    def test_duplicate_prevention(self, account):
        # Create a transaction manually
        Transaction.objects.create(
            external_id="12345",
            amount=Decimal("-100.00"),
            date=date(2026, 2, 1),
            memo="Test Transaction",
            account=account,
            reference_month=date(2026, 2, 1),
        )

        # Try to import/create same ID
        # Here we mimic what importer does: try/except IntegrityError
        # or we can test the Importer service if we mock the OFX parsing.
        # Let's test the model constraint directly first
        import django.db.utils

        with pytest.raises(django.db.utils.IntegrityError):
            Transaction.objects.create(
                external_id="12345",
                amount=Decimal("-100.00"),
                date=date(2026, 2, 1),
                memo="Duplicate",
                account=account,
                reference_month=date(2026, 2, 1),
            )

    def test_category_logic(self, category):
        sub = SubCategory.objects.get(name="Groceries")
        assert sub.category == category
        # If we had logic that enforces it on Expense save, we would test it here.
        # Django ForeignKey enforces existence of relationship.

    def test_consolidation_and_calculation(self, account):
        # 1. Create Raw Transactions
        t1 = Transaction.objects.create(
            external_id="A1",
            amount=Decimal("-50.00"),
            date=date(2026, 2, 10),
            memo="Lunch",
            account=account,
            reference_month=date(2026, 2, 1),
        )
        Transaction.objects.create(
            external_id="A2",
            amount=Decimal("-100.00"),
            date=date(2026, 2, 15),
            memo="Dinner",
            account=account,
            reference_month=date(2026, 2, 1),
        )

        # 2. Run Consolidation
        count = ConsolidationService.consolidate()
        assert count == 2

        # 3. Verify Expenses created
        assert Expense.objects.count() == 2
        e1 = Expense.objects.get(transaction=t1)
        assert e1.description == "Lunch"

        # 4. Calculation Logic (Sum)
        from django.db.models import Sum

        total = Expense.objects.filter(is_ignored=False).aggregate(Sum("transaction__amount"))["transaction__amount__sum"]
        assert total == Decimal("-150.00")

        # 5. Ignore one
        e1.is_ignored = True
        e1.save()
        total_ignored = Expense.objects.filter(is_ignored=False).aggregate(Sum("transaction__amount"))["transaction__amount__sum"]
        assert total_ignored == Decimal("-100.00")

    def test_command_setup_categories(self):
        # We need to ensure categories.json exists or mock it.
        # It's in the project root.
        call_command("setup_categories")
        assert Category.objects.exists()
        assert SubCategory.objects.exists()
        assert Category.objects.filter(name="Moradia").exists()
