from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from orcamento_2026.core.models import Expense, Category
from orcamento_2026.core.schemas import ExpenseSchema
from django_bolt import BoltAPI

api = BoltAPI()


@api.get("/expenses")
def list_expenses(request):
    """List all expenses not ignored, ordered by date desc."""
    queryset = Expense.objects.filter(is_ignored=False).order_by("-transaction__date")

    results = []
    for expense in queryset:
        results.append(
            ExpenseSchema(
                id=expense.id,
                description=expense.description,
                amount=expense.transaction.amount,
                date=expense.transaction.date,
                category_name=expense.category.name if expense.category else None,
                subcategory_name=expense.subcategory.name if expense.subcategory else None,
                is_ignored=expense.is_ignored,
            )
        )
    return results


@api.get("/stats/summary")
def get_summary(request):
    """Get monthly summary."""
    now = timezone.now()

    # Simple query param handling.
    # Bolt might have better way, but request.GET works.
    try:
        month = int(request.GET.get("month", now.month))
        year = int(request.GET.get("year", now.year))
    except ValueError:
        month = now.month
        year = now.year

    expenses = Expense.objects.filter(transaction__date__year=year, transaction__date__month=month, is_ignored=False)

    total = expenses.aggregate(Sum("transaction__amount"))["transaction__amount__sum"] or Decimal("0.00")

    by_category = []
    categories = Category.objects.all()
    for cat in categories:
        cat_sum = expenses.filter(category=cat).aggregate(Sum("transaction__amount"))["transaction__amount__sum"] or Decimal("0.00")
        if cat_sum != 0:
            by_category.append({"category": cat.name, "total": cat_sum})

    return {"period": f"{year}-{month}", "total": total, "by_category": by_category}
