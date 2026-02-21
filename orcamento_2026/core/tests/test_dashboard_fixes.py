import pytest
from datetime import date
from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from orcamento_2026.core.models import Account, Category, SubCategory, Transaction, Expense


@pytest.mark.django_db
class TestDashboardFixes:
    def setup_method(self):
        self.account = Account.objects.create(name="Nubank", type="C")
        self.category = Category.objects.create(name="Alimentação")
        self.subcategory = SubCategory.objects.create(category=self.category, name="Restaurante")

    def create_expense(self, day, amount):
        transaction = Transaction.objects.create(
            fitid=f"trans-{day}", account=self.account, amount=Decimal(amount), date=date(2026, 2, day), memo=f"Expense day {day}"
        )
        return Expense.objects.create(
            transaction=transaction,
            subcategory=self.subcategory,
            description=f"Expense day {day}",
            reference_month=date(2026, 2, day),  # Storing exact date
            is_ignored=False,
        )

    def test_monthly_evolution_grouping(self):
        # Create expenses on different days of the same month
        self.create_expense(10, "-100.00")
        self.create_expense(15, "-200.00")
        self.create_expense(20, "-50.00")

        # Current behavior (before fix):
        # Grouping by "reference_month" which holds dates will result in 3 groups.

        # We want to verify that we can group by Month.
        # This test checks the VIEW logic basically, but since we can't easily introspect the view context without client,
        # we can check the QuerySet logic we intend to use.

        # Reproducing the *current* buggy query logic from views.py:
        current_data = (
            Expense.objects.all().values("reference_month").annotate(total=Sum("transaction__amount")).order_by("reference_month")
        )
        # Should be 3 records because dates are different
        assert current_data.count() == 3

        # The Desired Logic:
        desired_data = (
            Expense.objects.all()
            .annotate(month=TruncMonth("reference_month"))
            .values("month")
            .annotate(total=Sum("transaction__amount"))
            .order_by("month")
        )

        assert desired_data.count() == 1
        assert desired_data[0]["total"] == Decimal("-350.00")
        assert desired_data[0]["month"] == date(2026, 2, 1)

    def test_negative_values_in_charts(self):
        self.create_expense(10, "-100.00")

        # Current aggregate
        total = Expense.objects.aggregate(total=Sum("transaction__amount"))["total"]
        assert total == Decimal("-100.00")

        # We want positive for charts
        from django.db.models.functions import Abs

        positive_total = Expense.objects.aggregate(total=Abs(Sum("transaction__amount")))["total"]
        assert positive_total == Decimal("100.00")
