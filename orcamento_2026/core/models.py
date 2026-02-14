from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Account(models.Model):
    class Type(models.TextChoices):
        CREDIT = "CREDIT", "Cartão de Crédito"
        DEBIT = "DEBIT", "Conta Corrente / Débito"

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=Type.choices)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")

    class Meta:
        verbose_name_plural = "Sub Categories"

    def __str__(self):
        return f"{self.category.name} > {self.name}"


class Transaction(models.Model):
    external_id = models.CharField(max_length=255, unique=True, help_text="FITID from OFX")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    memo = models.CharField(max_length=255, blank=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="transactions")
    reference_month = models.DateField(help_text="First day of the reference month")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date} - {self.amount} - {self.memo}"


class Expense(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name="expense")
    description = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    is_ignored = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description
