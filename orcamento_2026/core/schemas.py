from decimal import Decimal
from datetime import date
from msgspec import Struct
from typing import List, Optional


class CategorySchema(Struct):
    id: int
    name: str


class ExpenseSchema(Struct):
    id: int
    description: str
    amount: Decimal
    date: date
    is_ignored: bool
    category_name: Optional[str] = None
    subcategory_name: Optional[str] = None


class SummarySchema(Struct):
    period: str
    total: Decimal
    by_category: List[Struct]  # Simplified for now


class CreateExpenseInput(Struct):
    amount: Decimal
    date: date
    description: str
    account_id: int  # Required for manual creation
