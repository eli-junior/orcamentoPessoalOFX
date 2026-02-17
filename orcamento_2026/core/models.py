"""Modelos do core do Orçamento 2026."""

from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Modelo de usuário customizado."""

    pass


class Category(models.Model):
    """Categoria de despesa."""

    name: str = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"


class SubCategory(models.Model):
    """Subcategoria de despesa."""

    category: Category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name: str = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"{self.category.name} - {self.name}"

    class Meta:
        verbose_name = "Subcategoria"
        verbose_name_plural = "Subcategorias"


class Account(models.Model):
    """Conta bancária ou cartão de crédito."""

    ACCOUNT_TYPES: list[tuple[str, str]] = [
        ("C", "Corrente"),
        ("K", "Cartão"),
    ]

    name: str = models.CharField(max_length=100)
    type: str = models.CharField(max_length=1, choices=ACCOUNT_TYPES)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Conta"
        verbose_name_plural = "Contas"


class Transaction(models.Model):
    """Transação bancária importada de arquivo OFX."""

    fitid: str = models.CharField(max_length=255, unique=True)
    account: Account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount: Decimal = models.DecimalField(max_digits=10, decimal_places=2)
    date: date = models.DateField()
    reference_date: date | None = models.DateField(null=True, blank=True)
    memo: str = models.TextField()

    def __str__(self) -> str:
        return f"{self.date} - {self.amount} ({self.memo[:20]})"

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"


class Expense(models.Model):
    """Despesa consolidada a partir de uma transação."""

    transaction: Transaction | None = models.OneToOneField(Transaction, on_delete=models.CASCADE, null=True, blank=True)
    description: str = models.CharField(max_length=255)
    subcategory: SubCategory = models.ForeignKey(SubCategory, on_delete=models.PROTECT)
    reference_month: date = models.DateField()
    is_ignored: bool = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.description

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"


class TransactionSuggestion(models.Model):
    """Sugestão de IA para categorização de transação."""

    STATUS_CHOICES: list[tuple[str, str]] = [
        ("PENDENTE", "Pendente"),
        ("ACEITO", "Aceito"),
        ("REJEITADO", "Rejeitado"),
        ("EDITADO", "Editado"),
    ]

    transaction: Transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="suggestion")
    category: Category | None = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory: SubCategory | None = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description: str | None = models.CharField(max_length=255, blank=True, null=True)
    status: str = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDENTE")
    created_at: date = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Sugestão para {self.transaction}"

    class Meta:
        verbose_name = "Sugestão de Transação"
        verbose_name_plural = "Sugestões de Transação"
