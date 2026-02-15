from django.contrib import admin
from .models import User, Account, Category, SubCategory, Transaction, Expense


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    list_filter = ("category",)
    search_fields = ("name",)


class ExpenseInline(admin.StackedInline):
    model = Expense
    extra = 1
    max_num = 1
    autocomplete_fields = ["subcategory"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "amount", "account", "memo", "fitid")
    list_filter = ("account", "date")
    search_fields = ("memo", "fitid")
    date_hierarchy = "date"
    inlines = [ExpenseInline]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "get_amount", "get_date", "subcategory", "reference_month", "is_ignored")
    list_filter = ("reference_month", "subcategory__category", "is_ignored")
    search_fields = ("description", "transaction__memo")
    autocomplete_fields = ["subcategory", "transaction"]

    def get_amount(self, obj):
        return obj.transaction.amount if obj.transaction else None

    get_amount.short_description = "Valor"
    get_amount.admin_order_field = "transaction__amount"

    def get_date(self, obj):
        return obj.transaction.date if obj.transaction else None

    get_date.short_description = "Data"
    get_date.admin_order_field = "transaction__date"
