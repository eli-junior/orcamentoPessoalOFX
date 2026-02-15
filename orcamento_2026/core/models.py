from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Account(models.Model):
    name = models.CharField(max_length=100)
    # Ex: 'C' para Corrente, 'K' para Cartão
    type = models.CharField(max_length=1, choices=[("C", "Corrente"), ("K", "Cartão")])

    def __str__(self):
        return self.name


class Transaction(models.Model):
    # O FITID é a chave para evitar duplicatas de arquivos OFX parciais
    fitid = models.CharField(max_length=255, unique=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    memo = models.TextField()

    def __str__(self):
        return f"{self.date} - {self.amount} ({self.memo[:20]})"


class Expense(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, null=True, blank=True)
    description = models.CharField(max_length=255)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.PROTECT)
    reference_month = models.DateField()  # Salvar como primeiro dia do mês ex: 2026-02-01
    is_ignored = models.BooleanField(default=False)

    def __str__(self):
        return self.description
