"""Formulários do sistema de orçamento."""

from datetime import date

from django import forms
from django.db import models

from orcamento_2026.core.models import Account, Category, Expense, SubCategory, Transaction


class CategoryForm(forms.ModelForm):
    """Formulário para Categoria."""

    class Meta:
        model = Category
        fields = ["name"]
        labels = {"name": "Nome"}
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                    "placeholder": "Ex: Alimentação",
                }
            )
        }


class SubCategoryForm(forms.ModelForm):
    """Formulário para SubCategoria."""

    class Meta:
        model = SubCategory
        fields = ["category", "name"]
        labels = {"category": "Categoria", "name": "Nome"}
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                    "placeholder": "Ex: Restaurantes",
                }
            ),
        }


class ExpenseForm(forms.ModelForm):
    """Formulário para Despesa."""

    class Meta:
        model = Expense
        fields = ["transaction", "description", "subcategory", "reference_month", "is_ignored"]
        labels = {
            "transaction": "Transação",
            "description": "Descrição",
            "subcategory": "Subcategoria",
            "reference_month": "Mês de Referência",
            "is_ignored": "Ignorar esta despesa",
        }
        widgets = {
            "transaction": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                    "placeholder": "Ex: Almoço no restaurante",
                }
            ),
            "subcategory": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                }
            ),
            "reference_month": forms.DateInput(
                attrs={
                    "type": "month",
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                }
            ),
            "is_ignored": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar transações que não têm despesa associada ou a despesa atual
        if self.instance and self.instance.pk:
            self.fields["transaction"].queryset = Transaction.objects.filter(
                models.Q(expense__isnull=True) | models.Q(expense=self.instance)
            )
        else:
            self.fields["transaction"].queryset = Transaction.objects.filter(expense__isnull=True)


class ExpenseManualForm(forms.ModelForm):
    """Formulário para criar despesa manual (sem transação)."""

    class Meta:
        model = Expense
        fields = ["description", "subcategory", "reference_month", "is_ignored"]
        labels = {
            "description": "Descrição",
            "subcategory": "Subcategoria",
            "reference_month": "Mês de Referência",
            "is_ignored": "Ignorar esta despesa",
        }
        widgets = {
            "description": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                    "placeholder": "Ex: Despesa manual",
                }
            ),
            "subcategory": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                }
            ),
            "reference_month": forms.DateInput(
                attrs={
                    "type": "month",
                    "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                }
            ),
            "is_ignored": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"}),
        }


class OFXImportForm(forms.Form):
    """Formulário para importação de arquivo OFX."""

    account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        label="Conta",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            }
        ),
    )
    reference_date = forms.DateField(
        required=False,
        label="Data de Referência (opcional)",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            }
        ),
    )
    ofx_file = forms.FileField(
        label="Arquivo OFX",
        widget=forms.FileInput(
            attrs={
                "class": "block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none",
                "accept": ".ofx,.qfx",
            }
        ),
    )


class ConsolidationForm(forms.Form):
    """Formulário para consolidação de transação."""

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Categoria",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                "hx-get": "/api/subcategories/",
                "hx-target": "#id_subcategory",
                "hx-trigger": "change",
            }
        ),
    )
    subcategory = forms.ModelChoiceField(
        queryset=SubCategory.objects.all(),
        label="Subcategoria",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                "id": "id_subcategory",
            }
        ),
    )
    description = forms.CharField(
        max_length=255,
        label="Descrição",
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
                "placeholder": "Ex: Almoço no restaurante X",
            }
        ),
    )
    reference_month = forms.DateField(
        initial=date.today,
        label="Mês de Referência",
        widget=forms.DateInput(
            attrs={
                "type": "month",
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            }
        ),
    )


class DashboardFilterForm(forms.Form):
    """Formulário para filtros do dashboard."""

    start_date = forms.DateField(
        required=False,
        label="Data Inicial",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            }
        ),
    )
    end_date = forms.DateField(
        required=False,
        label="Data Final",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            }
        ),
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        label="Categoria",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            }
        ),
    )
