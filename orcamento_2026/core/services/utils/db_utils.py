"""Utilitários para operações de banco de dados."""

from typing import TypeVar

from django.db.models import QuerySet
from django.db.models.functions import Lower

T = TypeVar("T")


def case_insensitive_lookup(queryset: QuerySet[T], field_name: str, value: str | None) -> QuerySet[T]:
    """
    Realiza um lookup case-insensitive que funciona corretamente com caracteres acentuados.

    O __iexact padrão do SQLite pode ter problemas com acentos em maiúsculo.
    Esta função usa Lower() annotation para garantir comparação case-insensitive correta.

    Args:
        queryset: QuerySet do Django
        field_name: Nome do campo para filtrar
        value: Valor a ser comparado

    Returns:
        QuerySet filtrado
    """
    if value is None:
        return queryset.none()

    # Usa Lower() para garantir comparação case-insensitive correta
    return queryset.annotate(_lower_field=Lower(field_name)).filter(_lower_field=value.lower())


def case_insensitive_get(
    queryset: QuerySet[T],
    field_name: str,
    value: str | None,
    **kwargs,
) -> T | None:
    """
    Obtém um objeto usando lookup case-insensitive.

    Args:
        queryset: QuerySet do Django
        field_name: Nome do campo para filtrar
        value: Valor a ser comparado
        **kwargs: Filtros adicionais

    Returns:
        Objeto encontrado ou None
    """
    filtered = case_insensitive_lookup(queryset, field_name, value)

    # Aplica filtros adicionais
    for key, val in kwargs.items():
        filtered = filtered.filter(**{key: val})

    return filtered.first()
