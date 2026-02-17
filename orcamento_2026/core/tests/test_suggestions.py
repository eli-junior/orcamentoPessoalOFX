"""Testes para o serviço de sugestões."""

import json
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from orcamento_2026.core.models import (
    Account,
    Category,
    Expense,
    SubCategory,
    Transaction,
    TransactionSuggestion,
)
from orcamento_2026.core.services.suggestions import (
    find_similar_expenses,
    generate_suggestion_for_transaction,
    get_pending_suggestions,
)


@pytest.mark.django_db
class TestGetPendingSuggestions:
    """Testes para get_pending_suggestions."""

    def test_returns_only_pending_suggestions(self):
        """Testa que retorna apenas sugestões pendentes."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        tx1 = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 2, 15), memo="Test 1")
        tx2 = Transaction.objects.create(fitid="tx2", account=account, amount=Decimal("200.00"), date=date(2026, 2, 16), memo="Test 2")
        tx3 = Transaction.objects.create(fitid="tx3", account=account, amount=Decimal("300.00"), date=date(2026, 2, 17), memo="Test 3")

        # Cria sugestões com diferentes status
        sugg_pending = TransactionSuggestion.objects.create(
            transaction=tx1, category=category, subcategory=subcategory, description="Pending", status="PENDENTE"
        )
        TransactionSuggestion.objects.create(
            transaction=tx2, category=category, subcategory=subcategory, description="Aceito", status="ACEITO"
        )
        TransactionSuggestion.objects.create(
            transaction=tx3, category=category, subcategory=subcategory, description="Rejeitado", status="REJEITADO"
        )

        pending = get_pending_suggestions()

        assert pending.count() == 1
        assert pending.first() == sugg_pending

    def test_returns_empty_when_no_pending(self):
        """Testa que retorna vazio quando não há pendentes."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        tx = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 2, 15), memo="Test 1")
        TransactionSuggestion.objects.create(
            transaction=tx, category=category, subcategory=subcategory, description="Aceito", status="ACEITO"
        )

        pending = get_pending_suggestions()
        assert pending.count() == 0


@pytest.mark.django_db
class TestFindSimilarExpenses:
    """Testes para find_similar_expenses."""

    def test_finds_similar_by_memo_content(self):
        """Testa que encontra despesas com memo similar."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        # Cria transações/despesas
        tx1 = Transaction.objects.create(
            fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 1, 15), memo="Supermercado Extra"
        )
        tx2 = Transaction.objects.create(
            fitid="tx2", account=account, amount=Decimal("200.00"), date=date(2026, 2, 10), memo="Supermercado Carrefour"
        )
        tx3 = Transaction.objects.create(fitid="tx3", account=account, amount=Decimal("50.00"), date=date(2026, 2, 5), memo="Uber")

        Expense.objects.create(transaction=tx1, description="Compras", subcategory=subcategory, reference_month=date(2026, 1, 1))
        Expense.objects.create(transaction=tx2, description="Compras", subcategory=subcategory, reference_month=date(2026, 2, 1))
        Expense.objects.create(transaction=tx3, description="Transporte", subcategory=subcategory, reference_month=date(2026, 2, 1))

        # Busca por "Supermercado"
        similar = find_similar_expenses("Supermercado Pão de Açúcar")

        assert len(similar) == 2
        # Deve estar ordenado por reference_month decrescente
        assert similar[0].transaction.memo == "Supermercado Carrefour"

    def test_returns_empty_when_no_matches(self):
        """Testa que retorna vazio quando não há matches."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        tx = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 1, 15), memo="Supermercado")
        Expense.objects.create(transaction=tx, description="Compras", subcategory=subcategory, reference_month=date(2026, 1, 1))

        similar = find_similar_expenses("Uber Transporte")
        assert len(similar) == 0

    def test_respects_limit_parameter(self):
        """Testa que respeita o parâmetro limit."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        # Cria várias despesas similares
        for i in range(5):
            tx = Transaction.objects.create(
                fitid=f"tx{i}", account=account, amount=Decimal("100.00"), date=date(2026, 1, 15), memo=f"Supermercado {i}"
            )
            Expense.objects.create(transaction=tx, description="Compras", subcategory=subcategory, reference_month=date(2026, 1, 1))

        similar = find_similar_expenses("Supermercado Novo", limit=2)
        assert len(similar) == 2

    def test_handles_short_words(self):
        """Testa que ignora palavras muito curtas e retorna vazio se todas forem curtas."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        tx = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 1, 15), memo="Supermercado")
        Expense.objects.create(transaction=tx, description="Compras", subcategory=subcategory, reference_month=date(2026, 1, 1))

        # Descrição apenas com palavras curtas (<= 2 caracteres) - deve retornar vazio
        # A função considera apenas as 2 primeiras palavras
        similar = find_similar_expenses("X A")
        assert len(similar) == 0

        # Descrição onde a primeira palavra é válida
        similar = find_similar_expenses("Supermercado X")
        assert len(similar) == 1


@pytest.mark.django_db
class TestGenerateSuggestionForTransaction:
    """Testes para generate_suggestion_for_transaction."""

    def test_returns_existing_suggestion(self):
        """Testa que retorna sugestão existente em vez de criar nova."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="TestCat")
        subcategory = SubCategory.objects.create(category=category, name="TestSub")

        tx = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("100.00"), date=date(2026, 2, 15), memo="Test")
        existing = TransactionSuggestion.objects.create(
            transaction=tx, category=category, subcategory=subcategory, description="Existing", status="PENDENTE"
        )

        result = generate_suggestion_for_transaction(tx)

        assert result == existing
        assert TransactionSuggestion.objects.count() == 1

    @patch("orcamento_2026.core.services.suggestions.requests.post")
    def test_creates_suggestion_from_ollama_response(self, mock_post):
        """Testa criação de sugestão a partir da resposta do Ollama."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="Alimentação")
        subcategory = SubCategory.objects.create(category=category, name="Supermercado")

        tx = Transaction.objects.create(
            fitid="tx1", account=account, amount=Decimal("-150.00"), date=date(2026, 2, 15), memo="Supermercado Extra"
        )

        # Mock da resposta do Ollama
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": json.dumps({"category": "Alimentação", "subcategory": "Supermercado", "description": "Compras no Extra"})
        }
        mock_post.return_value = mock_response

        suggestion = generate_suggestion_for_transaction(tx)

        assert suggestion is not None
        assert suggestion.transaction == tx
        assert suggestion.category == category
        assert suggestion.subcategory == subcategory
        assert suggestion.description == "Compras no Extra"
        assert suggestion.status == "PENDENTE"

    @patch("orcamento_2026.core.services.suggestions.requests.post")
    def test_handles_case_insensitive_category_match(self, mock_post):
        """Testa matching case-insensitive de categoria/subcategoria."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="Alimentação")
        subcategory = SubCategory.objects.create(category=category, name="Supermercado")

        tx = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("-150.00"), date=date(2026, 2, 15), memo="Test")

        # Mock com nomes em maiúsculo
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": json.dumps({"category": "ALIMENTAÇÃO", "subcategory": "SUPERMERCADO", "description": "Compras"})
        }
        mock_post.return_value = mock_response

        suggestion = generate_suggestion_for_transaction(tx)

        assert suggestion.category == category
        assert suggestion.subcategory == subcategory

    @patch("orcamento_2026.core.services.suggestions.requests.post")
    def test_handles_api_error_gracefully(self, mock_post):
        """Testa tratamento de erro da API."""
        account = Account.objects.create(name="Test", type="C")

        tx = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("-150.00"), date=date(2026, 2, 15), memo="Test")

        mock_post.side_effect = Exception("Connection error")

        suggestion = generate_suggestion_for_transaction(tx)

        assert suggestion is None

    @patch("orcamento_2026.core.services.suggestions.requests.post")
    def test_handles_invalid_json_response(self, mock_post):
        """Testa tratamento de JSON inválido na resposta."""
        account = Account.objects.create(name="Test", type="C")

        tx = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("-150.00"), date=date(2026, 2, 15), memo="Test")

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "invalid json"}
        mock_post.return_value = mock_response

        suggestion = generate_suggestion_for_transaction(tx)

        assert suggestion is None

    @patch("orcamento_2026.core.services.suggestions.requests.post")
    def test_creates_suggestion_with_null_category_when_not_found(self, mock_post):
        """Testa criação de sugestão quando categoria não é encontrada."""
        account = Account.objects.create(name="Test", type="C")

        tx = Transaction.objects.create(fitid="tx1", account=account, amount=Decimal("-150.00"), date=date(2026, 2, 15), memo="Test")

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": json.dumps(
                {"category": "Categoria Inexistente", "subcategory": "Subcategoria Inexistente", "description": "Descrição"}
            )
        }
        mock_post.return_value = mock_response

        suggestion = generate_suggestion_for_transaction(tx)

        assert suggestion is not None
        assert suggestion.category is None
        assert suggestion.subcategory is None
        assert suggestion.description == "Descrição"

    @patch("orcamento_2026.core.services.suggestions.requests.post")
    def test_includes_similar_expenses_in_prompt(self, mock_post):
        """Testa que despesas similares são incluídas no prompt."""
        account = Account.objects.create(name="Test", type="C")
        category = Category.objects.create(name="Alimentação")
        subcategory = SubCategory.objects.create(category=category, name="Supermercado")

        # Cria despesa similar
        tx_similar = Transaction.objects.create(
            fitid="tx_similar", account=account, amount=Decimal("-100.00"), date=date(2026, 1, 15), memo="Supermercado Carrefour"
        )
        Expense.objects.create(
            transaction=tx_similar, description="Compras Carrefour", subcategory=subcategory, reference_month=date(2026, 1, 1)
        )

        tx_new = Transaction.objects.create(
            fitid="tx_new", account=account, amount=Decimal("-150.00"), date=date(2026, 2, 15), memo="Supermercado Extra"
        )

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": json.dumps({"category": "Alimentação", "subcategory": "Supermercado", "description": "Compras"})
        }
        mock_post.return_value = mock_response

        generate_suggestion_for_transaction(tx_new)

        # Verifica que o prompt incluiu a despesa similar
        call_args = mock_post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        prompt = payload.get("prompt", "")

        assert "Supermercado Carrefour" in prompt
        assert "Compras Carrefour" in prompt
