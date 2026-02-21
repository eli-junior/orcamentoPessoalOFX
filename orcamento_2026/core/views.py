"""Views do sistema de orçamento."""

import json
import logging
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Sum
from django.db.models.functions import Abs, TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from orcamento_2026.core.forms import (
    CategoryForm,
    ConsolidationForm,
    DashboardFilterForm,
    ExpenseForm,
    ExpenseManualForm,
    OFXImportForm,
    SubCategoryForm,
)
from orcamento_2026.core.models import Account, Category, Expense, SubCategory, Transaction, TransactionSuggestion
from orcamento_2026.core.services.consolidation import consolidate_transaction, get_unconsolidated_transactions
from orcamento_2026.core.services.import_ofx import import_ofx
from orcamento_2026.core.services.suggestions import generate_suggestion_for_transaction, get_pending_suggestions

logger = logging.getLogger(__name__)


# =============================================================================
# Dashboard Views
# =============================================================================


@login_required
def dashboard(request):
    """View principal do dashboard com gráficos interativos."""
    form = DashboardFilterForm(request.GET or None)

    # Período padrão: últimos 6 meses
    reference = date.today()

    start_date = (reference - relativedelta(months=1)).replace(day=21)
    end_date = (reference + relativedelta(months=1)).replace(day=20)

    # Aplicar filtros
    if form.is_valid():
        if form.cleaned_data.get("start_date"):
            start_date = form.cleaned_data["start_date"]
        if form.cleaned_data.get("end_date"):
            end_date = form.cleaned_data["end_date"]

    # Estatísticas gerais
    total_expenses = Expense.objects.filter(
        reference_month__gte=start_date,
        reference_month__lte=end_date,
        is_ignored=False,
    ).count()

    total_amount = Expense.objects.filter(
        reference_month__gte=start_date,
        reference_month__lte=end_date,
        is_ignored=False,
    ).aggregate(
        total=Sum(Abs("transaction__amount"))
    )["total"] or Decimal("0")

    unconsolidated_count = get_unconsolidated_transactions().count()
    pending_suggestions = get_pending_suggestions().count()

    # Gráfico 1: Despesas por Categoria (Donut)
    expenses_by_category = (
        Expense.objects.filter(
            reference_month__gte=start_date,
            reference_month__lte=end_date,
            is_ignored=False,
        )
        .values("subcategory__category__name")
        .annotate(total=Sum(Abs("transaction__amount")))
        .order_by("-total")
    )

    pie_chart = json.dumps(
        {
            "labels": [item["subcategory__category__name"] for item in expenses_by_category],
            "series": [float(item["total"]) for item in expenses_by_category],
        },
        cls=DjangoJSONEncoder,
    )

    # Gráfico 2: Evolução Mensal (Area)
    monthly_data = (
        Expense.objects.filter(
            reference_month__gte=start_date,
            reference_month__lte=end_date,
            is_ignored=False,
        )
        .annotate(month=TruncMonth("reference_month"))
        .values("month")
        .annotate(total=Sum(Abs("transaction__amount")))
        .order_by("month")
    )

    line_chart = json.dumps(
        {
            "categories": [item["month"].strftime("%b %Y") for item in monthly_data],
            "series": [float(item["total"]) for item in monthly_data],
        },
        cls=DjangoJSONEncoder,
    )

    # Gráfico 3: Top Subcategorias (Horizontal Bar)
    top_subcategories = (
        Expense.objects.filter(
            reference_month__gte=start_date,
            reference_month__lte=end_date,
            is_ignored=False,
        )
        .values("subcategory__name")
        .annotate(total=Sum(Abs("transaction__amount")))
        .order_by("-total")[:10]
    )

    bar_chart = json.dumps(
        {
            "categories": [item["subcategory__name"] for item in top_subcategories],
            "series": [float(item["total"]) for item in top_subcategories],
        },
        cls=DjangoJSONEncoder,
    )

    # Gráfico 4: Comparativo por Conta (Vertical Bar)
    expenses_by_account = (
        Expense.objects.filter(
            reference_month__gte=start_date,
            reference_month__lte=end_date,
            is_ignored=False,
        )
        .values("transaction__account__name")
        .annotate(total=Sum(Abs("transaction__amount")))
        .order_by("-total")
    )

    account_chart = json.dumps(
        {
            "categories": [item["transaction__account__name"] for item in expenses_by_account],
            "series": [float(item["total"]) for item in expenses_by_account],
        },
        cls=DjangoJSONEncoder,
    )

    context = {
        "form": form,
        "total_expenses": total_expenses,
        "total_amount": total_amount,
        "unconsolidated_count": unconsolidated_count,
        "pending_suggestions": pending_suggestions,
        "pie_chart": pie_chart,
        "line_chart": line_chart,
        "bar_chart": bar_chart,
        "account_chart": account_chart,
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "core/dashboard.html", context)


# =============================================================================
# Category Views
# =============================================================================


class CategoryListView(LoginRequiredMixin, ListView):
    """Lista de categorias."""

    model = Category
    template_name = "core/category_list.html"
    context_object_name = "categories"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset.prefetch_related("subcategories")


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Criar nova categoria."""

    model = Category
    form_class = CategoryForm
    template_name = "core/category_form.html"
    success_url = reverse_lazy("category_list")

    def form_valid(self, form):
        messages.success(self.request, "Categoria criada com sucesso!")
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Editar categoria."""

    model = Category
    form_class = CategoryForm
    template_name = "core/category_form.html"
    success_url = reverse_lazy("category_list")

    def form_valid(self, form):
        messages.success(self.request, "Categoria atualizada com sucesso!")
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Excluir categoria."""

    model = Category
    template_name = "core/category_confirm_delete.html"
    success_url = reverse_lazy("category_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Categoria excluída com sucesso!")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# SubCategory Views
# =============================================================================


class SubCategoryListView(LoginRequiredMixin, ListView):
    """Lista de subcategorias."""

    model = SubCategory
    template_name = "core/subcategory_list.html"
    context_object_name = "subcategories"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.GET.get("category")
        search = self.request.GET.get("search")
        if category:
            queryset = queryset.filter(category_id=category)
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset.select_related("category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["selected_category"] = self.request.GET.get("category")
        return context


class SubCategoryCreateView(LoginRequiredMixin, CreateView):
    """Criar nova subcategoria."""

    model = SubCategory
    form_class = SubCategoryForm
    template_name = "core/subcategory_form.html"
    success_url = reverse_lazy("subcategory_list")

    def form_valid(self, form):
        messages.success(self.request, "Subcategoria criada com sucesso!")
        return super().form_valid(form)


class SubCategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Editar subcategoria."""

    model = SubCategory
    form_class = SubCategoryForm
    template_name = "core/subcategory_form.html"
    success_url = reverse_lazy("subcategory_list")

    def form_valid(self, form):
        messages.success(self.request, "Subcategoria atualizada com sucesso!")
        return super().form_valid(form)


class SubCategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Excluir subcategoria."""

    model = SubCategory
    template_name = "core/subcategory_confirm_delete.html"
    success_url = reverse_lazy("subcategory_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Subcategoria excluída com sucesso!")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# Expense Views
# =============================================================================


class ExpenseListView(LoginRequiredMixin, ListView):
    """Lista de despesas."""

    model = Expense
    template_name = "core/expense_list.html"
    context_object_name = "expenses"
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros
        category = self.request.GET.get("category")
        subcategory = self.request.GET.get("subcategory")
        search = self.request.GET.get("search")
        is_ignored = self.request.GET.get("is_ignored")
        month = self.request.GET.get("month")

        if category:
            queryset = queryset.filter(subcategory__category_id=category)
        if subcategory:
            queryset = queryset.filter(subcategory_id=subcategory)
        if search:
            queryset = queryset.filter(Q(description__icontains=search) | Q(transaction__memo__icontains=search))
        if is_ignored:
            queryset = queryset.filter(is_ignored=is_ignored == "true")
        if month:
            queryset = queryset.filter(reference_month__month=month)

        return queryset.select_related("subcategory__category", "transaction").order_by("-reference_month")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["subcategories"] = SubCategory.objects.all()
        context["total_amount"] = self.get_queryset().aggregate(total=Sum("transaction__amount"))["total"] or Decimal("0")
        return context


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    """Criar nova despesa manual."""

    model = Expense
    form_class = ExpenseManualForm
    template_name = "core/expense_form.html"
    success_url = reverse_lazy("expense_list")

    def form_valid(self, form):
        messages.success(self.request, "Despesa criada com sucesso!")
        return super().form_valid(form)


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    """Editar despesa."""

    model = Expense
    form_class = ExpenseForm
    template_name = "core/expense_form.html"
    success_url = reverse_lazy("expense_list")

    def get_form_class(self):
        # Se tem transação, usa o formulário completo
        if self.object.transaction:
            return ExpenseForm
        return ExpenseManualForm

    def form_valid(self, form):
        messages.success(self.request, "Despesa atualizada com sucesso!")
        return super().form_valid(form)


class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    """Excluir despesa."""

    model = Expense
    template_name = "core/expense_confirm_delete.html"
    success_url = reverse_lazy("expense_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Despesa excluída com sucesso!")
        return super().delete(request, *args, **kwargs)


# =============================================================================
# Transaction Views
# =============================================================================


class TransactionListView(LoginRequiredMixin, ListView):
    """Lista de transações."""

    model = Transaction
    template_name = "core/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros
        account = self.request.GET.get("account")
        search = self.request.GET.get("search")
        has_expense = self.request.GET.get("has_expense")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")

        if account:
            queryset = queryset.filter(account_id=account)
        if search:
            queryset = queryset.filter(memo__icontains=search)
        if has_expense == "yes":
            queryset = queryset.filter(expense__isnull=False)
        elif has_expense == "no":
            queryset = queryset.filter(expense__isnull=True)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset.select_related("account", "expense").order_by("-date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["accounts"] = Account.objects.all()
        context["unconsolidated_count"] = get_unconsolidated_transactions().count()
        return context


@login_required
def transaction_consolidate(request, pk):
    """View para consolidar uma transação."""
    transaction = get_object_or_404(Transaction, pk=pk)

    if request.method == "POST":
        form = ConsolidationForm(request.POST)
        if form.is_valid():
            try:
                expense = consolidate_transaction(
                    transaction=transaction,
                    category_name=form.cleaned_data["category"].name,
                    subcategory_name=form.cleaned_data["subcategory"].name,
                    description=form.cleaned_data["description"],
                    reference_month=form.cleaned_data["reference_month"],
                )
                messages.success(request, f"Transação consolidada com sucesso! Despesa #{expense.id} criada.")
                return redirect("transaction_list")
            except ValueError as e:
                messages.error(request, str(e))
    else:
        # Preenche com sugestão se existir
        initial = {}
        if hasattr(transaction, "suggestion"):
            suggestion = transaction.suggestion
            if suggestion.category:
                initial["category"] = suggestion.category
            if suggestion.subcategory:
                initial["subcategory"] = suggestion.subcategory
            if suggestion.description:
                initial["description"] = suggestion.description
        initial["reference_month"] = transaction.date
        form = ConsolidationForm(initial=initial)

    return render(
        request,
        "core/transaction_consolidate.html",
        {
            "form": form,
            "transaction": transaction,
        },
    )


# =============================================================================
# Suggestion Views
# =============================================================================


@login_required
def suggestion_list(request):
    """Lista de sugestões pendentes."""
    suggestions = get_pending_suggestions()

    # Paginação
    paginator = Paginator(suggestions, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "core/suggestion_list.html",
        {
            "suggestions": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
        },
    )


@login_required
def suggestion_generate(request):
    """Gerar sugestões para transações sem sugestão."""
    if request.method == "POST":
        # Transações sem sugestão
        transactions_without_suggestion = Transaction.objects.filter(
            expense__isnull=True,
            suggestion__isnull=True,
        )[
            :10
        ]  # Processa 10 por vez

        count = 0
        for transaction in transactions_without_suggestion:
            suggestion = generate_suggestion_for_transaction(transaction)
            if suggestion:
                count += 1

        if count > 0:
            messages.success(request, f"{count} sugestões geradas com sucesso!")
        else:
            messages.info(request, "Nenhuma sugestão foi gerada. Verifique se o Ollama está disponível.")

        return redirect("suggestion_list")

    return render(request, "core/suggestion_generate.html")


@login_required
def suggestion_accept(request, pk):
    """Aceitar uma sugestão e consolidar a transação."""
    suggestion = get_object_or_404(TransactionSuggestion, pk=pk)

    if request.method == "POST":
        try:
            expense = consolidate_transaction(
                transaction=suggestion.transaction,
                category_name=suggestion.category.name if suggestion.category else "",
                subcategory_name=suggestion.subcategory.name if suggestion.subcategory else "",
                description=suggestion.description or suggestion.transaction.memo,
                reference_month=suggestion.transaction.date,
            )
            messages.success(request, f"Sugestão aceita! Despesa #{expense.id} criada.")
        except ValueError as e:
            messages.error(request, str(e))

    return redirect("suggestion_list")


@login_required
def suggestion_reject(request, pk):
    """Rejeitar uma sugestão."""
    suggestion = get_object_or_404(TransactionSuggestion, pk=pk)

    if request.method == "POST":
        suggestion.status = "REJEITADO"
        suggestion.save()
        messages.success(request, "Sugestão rejeitada.")

    return redirect("suggestion_list")


@login_required
def pending_suggestions_count(request):
    """Retorna o contador de sugestões pendentes (para HTMX)."""
    count = get_pending_suggestions().count()
    if count > 0:
        return HttpResponse(
            f'<span class="inline-flex items-center rounded-lg bg-purple-500/20 px-2 py-0.5 text-[10px] font-bold text-purple-300">{count}</span>'
        )
    return HttpResponse("")


# =============================================================================
# Import Views
# =============================================================================


@login_required
def import_ofx_view(request):
    """View para importar arquivo OFX."""
    if request.method == "POST":
        form = OFXImportForm(request.POST, request.FILES)
        if form.is_valid():
            account = form.cleaned_data["account"]
            reference_date = form.cleaned_data.get("reference_date")
            ofx_file = request.FILES["ofx_file"]

            # Salva o arquivo temporariamente
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".ofx") as tmp:
                for chunk in ofx_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                result = import_ofx(tmp_path, account, reference_date)
                messages.success(request, f"Importação concluída! {result['transactions_created']} transações criadas.")
                return redirect("transaction_list")
            except Exception as e:
                messages.error(request, f"Erro na importação: {str(e)}")
            finally:
                os.unlink(tmp_path)
    else:
        form = OFXImportForm()

    return render(request, "core/import_ofx.html", {"form": form})


# =============================================================================
# API/HTMX Views
# =============================================================================


@login_required
def get_subcategories_by_category(request):
    """Retorna subcategorias para uma categoria (para HTMX)."""
    category_id = request.GET.get("category")
    subcategories = SubCategory.objects.filter(category_id=category_id)

    options = '<option value="">---------</option>'
    for sub in subcategories:
        options += f'<option value="{sub.id}">{sub.name}</option>'

    return HttpResponse(options)


@login_required
def home(request):
    """Home page redireciona para dashboard."""
    return redirect("dashboard")
