import json
import logging
import requests
from decouple import config
from django.db.models import Q
from orcamento_2026.core.models import Expense, Category, SubCategory, TransactionSuggestion

logger = logging.getLogger(__name__)

OLLAMA_URL = config("OLLAMA_URL", default="http://localhost:11434")
OLLAMA_MODEL = config("OLLAMA_MODEL", default="qwen2.5:1.5b")


def get_pending_suggestions():
    """Retorna sugestões pendentes de revisão."""
    return TransactionSuggestion.objects.filter(status="PENDING").select_related("transaction", "category", "subcategory")


def find_similar_expenses(description, limit=3):
    """
    Encontra despesas passadas com descrições similares.
    Usa um filtro simples por conter parte da string por enquanto.
    """
    # Simplificação: pega as primeiras 2 palavras
    parts = description.split()[:2]
    query = Q()
    for part in parts:
        if len(part) > 2:
            query |= Q(transaction__memo__icontains=part)

    if not query:
        return []

    return Expense.objects.filter(query).select_related("subcategory", "subcategory__category").order_by("-reference_month")[:limit]


def generate_suggestion_for_transaction(transaction):
    """
    Gera uma sugestão via Ollama e salva no banco de dados.
    """
    # Verifica se já existe sugestão pendente
    if hasattr(transaction, "suggestion"):
        return transaction.suggestion

    similar_expenses = find_similar_expenses(transaction.memo)

    # Prepara o contexto com categorias disponíveis
    categories = Category.objects.prefetch_related("subcategories").all()
    categories_str = ""
    for cat in categories:
        subs = ", ".join([s.name for s in cat.subcategories.all()])
        categories_str += f"- {cat.name}: [{subs}]\n"

    # Prepara exemplos
    examples_str = ""
    if similar_expenses:
        examples_str = "Exemplos de transações similares passadas:\n"
        for exp in similar_expenses:
            examples_str += f"- Memo: '{exp.transaction.memo}' -> Categoria: '{exp.subcategory.category.name}', Sub: '{exp.subcategory.name}', Desc: '{exp.description}'\n"

    prompt = f"""
    Analise a seguinte transação bancária e sugira a Categoria, Subcategoria e uma Descrição amigável.

    Transação:
    - Memo: {transaction.memo}
    - Valor: {transaction.amount}
    - Data: {transaction.date}

    {examples_str}

    Categorias Disponíveis:
    {categories_str}

    Responda APENAS com um JSON estrito no seguinte formato, sem markdown ou explicações:
    {{
        "category": "Nome da Categoria",
        "subcategory": "Nome da Subcategoria",
        "description": "Descrição sugerida (ex: 'Almoço no Restaurante X')"
    }}
    """

    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"}

    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        data = json.loads(result["response"])

        # Tenta encontrar a categoria e subcategoria
        category = Category.objects.filter(name__iexact=data.get("category")).first()
        subcategory = None
        if category:
            subcategory = SubCategory.objects.filter(name__iexact=data.get("subcategory"), category=category).first()

        suggestion = TransactionSuggestion.objects.create(
            transaction=transaction, category=category, subcategory=subcategory, description=data.get("description"), status="PENDING"
        )
        return suggestion

    except Exception as e:
        logger.error(f"Erro ao gerar sugestão para transação {transaction.id}: {e}")
        return None
