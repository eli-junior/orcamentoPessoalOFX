from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    class Meta:
        verbose_name = "Subcategoria"
        verbose_name_plural = "Subcategorias"


class Account(models.Model):
    name = models.CharField(max_length=100)
    # Ex: 'C' para Corrente, 'K' para Cartão
    type = models.CharField(max_length=1, choices=[("C", "Corrente"), ("K", "Cartão")])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Conta"
        verbose_name_plural = "Contas"


class Transaction(models.Model):
    # O FITID é a chave para evitar duplicatas de arquivos OFX parciais
    fitid = models.CharField(max_length=255, unique=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    memo = models.TextField()

    def __str__(self):
        return f"{self.date} - {self.amount} ({self.memo[:20]})"

    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"


class Expense(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, null=True, blank=True)
    description = models.CharField(max_length=255)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.PROTECT)
    reference_month = models.DateField()  # Salvar como primeiro dia do mês ex: 2026-02-01
    is_ignored = models.BooleanField(default=False)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"


class TransactionSuggestion(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pendente"),
        ("ACCEPTED", "Aceito"),
        ("REJECTED", "Rejeitado"),
        ("EDITED", "Editado"),
    ]

    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="suggestion")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sugestão para {self.transaction}"

    class Meta:
        verbose_name = "Sugestão de Transação"
        verbose_name_plural = "Sugestões de Transação"
