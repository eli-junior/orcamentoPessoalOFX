from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from orcamento_2026.core.models import Account, Transaction, Expense
from orcamento_2026.core.services.import_ofx import import_ofx


# Fixture para criar conta
@pytest.fixture
def account():
    return Account.objects.create(name="Nubank", type="C")


@pytest.fixture
def mock_ofx_parser():
    with patch("orcamento_2026.core.services.import_ofx.OfxParser") as mock:
        yield mock


@pytest.fixture
def mock_open_file():
    with patch("builtins.open", new_callable=MagicMock) as mock:
        yield mock


@pytest.mark.django_db
def test_import_ofx_success(account, mock_ofx_parser, mock_open_file):
    # Setup do mock
    mock_ofx = MagicMock()
    mock_transaction = MagicMock()
    mock_transaction.id = "fitid-1"
    mock_transaction.amount = -100.50
    mock_transaction.date = MagicMock()
    mock_transaction.date.date.return_value = date(2026, 2, 1)
    mock_transaction.memo = "Supermercado"

    mock_ofx.account.statement.transactions = [mock_transaction]
    mock_ofx_parser.parse.return_value = mock_ofx

    # Executa importação
    result = import_ofx("dummy.ofx", account)

    # Verificações
    assert result["transactions_created"] == 1
    # Expenses não são mais criadas
    assert "expenses_created" not in result

    # Verifica se a transação foi criada
    tx = Transaction.objects.get(fitid="fitid-1")
    assert tx.amount == Decimal("-100.50")
    assert tx.account == account

    # Verifica se a despesa NÃO foi criada
    assert not Expense.objects.filter(transaction=tx).exists()


@pytest.mark.django_db
def test_import_ofx_duplicate_transaction(account, mock_ofx_parser, mock_open_file):
    # Cria transação existente
    Transaction.objects.create(fitid="fitid-dup", account=account, amount=Decimal("-50.00"), date=date(2026, 2, 1), memo="Original")

    # Setup do mock
    mock_ofx = MagicMock()
    mock_transaction = MagicMock()
    mock_transaction.id = "fitid-dup"
    mock_transaction.amount = -50.00
    mock_transaction.date = MagicMock()
    mock_transaction.date.date.return_value = date(2026, 2, 1)
    mock_transaction.memo = "Duplicada"

    mock_ofx.account.statement.transactions = [mock_transaction]
    mock_ofx_parser.parse.return_value = mock_ofx

    # Executa importação
    result = import_ofx("dummy.ofx", account)

    # Nada deve ser criado
    assert result["transactions_created"] == 0
