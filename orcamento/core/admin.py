from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from orcamento.core.models import (
    Account,
    Category,
    Expense,
    SubCategory,
    Transaction,
    User,
)

if TYPE_CHECKING:
    from decimal import Decimal
    from datetime import date


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin para o modelo User com email como identificador."""

    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    """Admin para o modelo Account."""

    list_display: tuple[str, str] = ("name", "type")
    search_fields: tuple[str] = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin para o modelo Category."""

    list_display: tuple[str] = ("name",)
    search_fields: tuple[str] = ("name",)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    """Admin para o modelo SubCategory."""

    list_display: tuple[str, str] = ("name", "category")
    list_filter: tuple[str] = ("category",)
    search_fields: tuple[str] = ("name",)


class ExpenseInline(admin.StackedInline):
    """Inline para despesas dentro de transações."""

    model = Expense
    extra = 1
    max_num = 1
    autocomplete_fields: list[str] = ["subcategory"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin para o modelo Transaction."""

    list_display: tuple[str, str, str, str, str] = (
        "date",
        "amount",
        "account",
        "memo",
        "fitid",
    )
    list_filter: tuple[str, str] = ("account", "date")
    search_fields: tuple[str, str] = ("memo", "fitid")
    date_hierarchy = "date"
    inlines: list[type[admin.StackedInline]] = [ExpenseInline]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Admin para o modelo Expense."""

    list_display: tuple[str, str, str, str, str, str] = (
        "description",
        "get_amount",
        "get_date",
        "subcategory",
        "reference_month",
        "is_ignored",
    )
    list_filter: tuple[str, str, str] = (
        "reference_month",
        "subcategory__category",
        "is_ignored",
    )
    search_fields: tuple[str, str] = ("description", "transaction__memo")
    autocomplete_fields: list[str] = ["subcategory", "transaction"]

    @admin.display(description="Valor", ordering="transaction__amount")
    def get_amount(self, obj: Expense) -> "Decimal | None":
        """Retorna o valor da transação associada."""
        return obj.transaction.amount if obj.transaction else None

    @admin.display(description="Data", ordering="transaction__date")
    def get_date(self, obj: Expense) -> "date | None":
        """Retorna a data da transação associada."""
        return obj.transaction.date if obj.transaction else None
