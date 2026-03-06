"""Formulários do sistema de orçamento."""

from datetime import date, datetime

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
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
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
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200"
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
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
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200"
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
                    "placeholder": "Ex: Almoço no restaurante",
                }
            ),
            "subcategory": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200"
                }
            ),
            "reference_month": forms.DateInput(
                format="%Y-%m",
                attrs={
                    "type": "month",
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
                }
            ),
            "is_ignored": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"}),
        }

    def clean_reference_month(self):
        value = self.data.get('reference_month', '')
        if value and len(value) == 7:  # formato YYYY-MM vindo do input type=month
            try:
                # Preserva o dia original ao editar; usa dia 1 para registros novos
                original_day = 1
                if self.instance and self.instance.pk and self.instance.reference_month:
                    original_day = self.instance.reference_month.day
                return datetime.strptime(value + f'-{original_day:02d}', '%Y-%m-%d').date()
            except ValueError:
                pass
        return self.cleaned_data.get('reference_month')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reference_month'].input_formats = ['%Y-%m', '%Y-%m-%d']
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
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
                    "placeholder": "Ex: Despesa manual",
                }
            ),
            "subcategory": forms.Select(
                attrs={
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200"
                }
            ),
            "reference_month": forms.DateInput(
                format="%Y-%m",
                attrs={
                    "type": "month",
                    "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
                }
            ),
            "is_ignored": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-600"}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reference_month'].input_formats = ['%Y-%m', '%Y-%m-%d']

    def clean_reference_month(self):
        value = self.data.get('reference_month', '')
        if value and len(value) == 7:  # formato YYYY-MM vindo do input type=month
            try:
                original_day = 1
                if self.instance and self.instance.pk and self.instance.reference_month:
                    original_day = self.instance.reference_month.day
                return datetime.strptime(value + f'-{original_day:02d}', '%Y-%m-%d').date()
            except ValueError:
                pass
        return self.cleaned_data.get('reference_month')


class OFXImportForm(forms.Form):
    """Formulário para importação de arquivo OFX."""

    account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        label="Conta",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200"
            }
        ),
    )
    reference_date = forms.DateField(
        required=False,
        label="Data de Referência (opcional)",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
            }
        ),
    )
    ofx_file = forms.FileField(
        label="Arquivo OFX",
        widget=forms.FileInput(
            attrs={
                "class": "block w-full text-sm text-gray-900 file:mr-4 file:py-2.5 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 file:cursor-pointer rounded-md border-0 py-2.5 px-3 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 transition-shadow duration-200",
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
                "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
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
                "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
                "id": "id_subcategory",
            }
        ),
    )
    description = forms.CharField(
        max_length=255,
        label="Descrição",
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
                "placeholder": "Ex: Almoço no restaurante X",
            }
        ),
    )
    reference_month = forms.DateField(
        initial=date.today,
        label="Mês de Referência",
        input_formats=['%Y-%m', '%Y-%m-%d'],
        widget=forms.DateInput(
            format="%Y-%m",
            attrs={
                "type": "month",
                "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
            }
        ),
    )


    def clean_reference_month(self):
        value = self.data.get('reference_month', '')
        if value and len(value) == 7:  # formato YYYY-MM
            try:
                return datetime.strptime(value + '-01', '%Y-%m-%d').date()
            except ValueError:
                pass
        return self.cleaned_data.get('reference_month')


class DashboardFilterForm(forms.Form):
    """Formulário para filtros do dashboard."""

    start_date = forms.DateField(
        required=False,
        label="Data Inicial",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
            }
        ),
    )
    end_date = forms.DateField(
        required=False,
        label="Data Final",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200",
            }
        ),
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.all(),
        label="Categoria",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-md border-0 py-2.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 transition-shadow duration-200"
            }
        ),
    )
