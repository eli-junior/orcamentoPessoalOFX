from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from orcamento_2026.core.models import Account, Transaction, Category, SubCategory, Expense, TransactionSuggestion
from datetime import date

User = get_user_model()


class UIViewsTest(TestCase):
    def setUp(self):
        # Create user and login
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.login(username="testuser", password="password")

        # Create basic data
        self.account = Account.objects.create(name="Test Account")
        self.category = Category.objects.create(name="Test Category")
        self.subcategory = SubCategory.objects.create(name="Test Sub", category=self.category)

        self.transaction = Transaction.objects.create(
            account=self.account, date=date.today(), amount=-100.00, memo="Test Transaction", fitid="12345"
        )

        self.expense = Expense.objects.create(
            transaction=self.transaction, subcategory=self.subcategory, description="Test Expense", reference_month=date.today()
        )

        self.suggestion = TransactionSuggestion.objects.create(
            transaction=self.transaction, category=self.category, subcategory=self.subcategory, description="Suggested Expense"
        )

    def test_dashboard_access(self):
        """Test if dashboard loads correctly for authenticated user"""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/dashboard.html")
        # Check for context data
        self.assertIn("total_expenses", response.context)
        self.assertIn("total_amount", response.context)
        self.assertIn("unconsolidated_count", response.context)
        self.assertIn("pending_suggestions", response.context)

    def test_transaction_list_access(self):
        """Test transaction list view"""
        response = self.client.get(reverse("transaction_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/transaction_list.html")
        self.assertContains(response, "Test Transaction")
        self.assertContains(response, "Test Account")

    def test_transaction_list_filter(self):
        """Test searching transactions"""
        response = self.client.get(reverse("transaction_list"), {"search": "Transaction"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Transaction")

        # Test non-matching search
        response = self.client.get(reverse("transaction_list"), {"search": "NonExistent"})
        self.assertNotContains(response, "Test Transaction")

    def test_expense_list_access(self):
        """Test expense list view"""
        response = self.client.get(reverse("expense_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/expense_list.html")
        self.assertContains(response, "Test Expense")

    def test_expense_create_view(self):
        """Test expense creation form access"""
        response = self.client.get(reverse("expense_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/expense_form.html")

    def test_expense_update_view(self):
        """Test expense update form access"""
        response = self.client.get(reverse("expense_update", args=[self.expense.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/expense_form.html")

    def test_suggestion_list_access(self):
        """Test suggestion list view"""
        response = self.client.get(reverse("suggestion_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/suggestion_list.html")
        self.assertContains(response, "Suggested Expense")

    def test_import_ofx_access(self):
        """Test import OFX page"""
        response = self.client.get(reverse("import_ofx"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/import_ofx.html")

    def test_redirect_if_not_logged_in(self):
        """Test if unauthenticated user is redirected to login"""
        self.client.logout()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))
