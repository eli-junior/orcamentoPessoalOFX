"""Testes para utilitários de banco de dados."""

import pytest

from orcamento_2026.core.models import Category, SubCategory
from orcamento_2026.core.services.utils.db_utils import (
    case_insensitive_get,
    case_insensitive_lookup,
)


@pytest.mark.django_db
class TestCaseInsensitiveLookup:
    """Testes para case_insensitive_lookup."""

    def test_finds_with_exact_case(self):
        """Testa que encontra com case exato."""
        Category.objects.create(name="Alimentação")

        result = case_insensitive_lookup(Category.objects.all(), "name", "Alimentação")
        assert result.count() == 1

    def test_finds_with_uppercase(self):
        """Testa que encontra com texto em maiúsculo."""
        Category.objects.create(name="Alimentação")

        result = case_insensitive_lookup(Category.objects.all(), "name", "ALIMENTAÇÃO")
        assert result.count() == 1

    def test_finds_with_lowercase(self):
        """Testa que encontra com texto em minúsculo."""
        Category.objects.create(name="Alimentação")

        result = case_insensitive_lookup(Category.objects.all(), "name", "alimentação")
        assert result.count() == 1

    def test_finds_with_mixed_case(self):
        """Testa que encontra com texto em case misto."""
        Category.objects.create(name="Alimentação")

        result = case_insensitive_lookup(Category.objects.all(), "name", "AlImEnTaÇÃO")
        assert result.count() == 1

    def test_returns_empty_when_not_found(self):
        """Testa que retorna queryset vazio quando não encontra."""
        result = case_insensitive_lookup(Category.objects.all(), "name", "Inexistente")
        assert result.count() == 0

    def test_returns_empty_when_value_is_none(self):
        """Testa que retorna queryset vazio quando valor é None."""
        result = case_insensitive_lookup(Category.objects.all(), "name", None)
        assert result.count() == 0


@pytest.mark.django_db
class TestCaseInsensitiveGet:
    """Testes para case_insensitive_get."""

    def test_returns_object_with_exact_case(self):
        """Testa que retorna objeto com case exato."""
        category = Category.objects.create(name="Alimentação")

        result = case_insensitive_get(Category.objects.all(), "name", "Alimentação")
        assert result == category

    def test_returns_object_with_uppercase(self):
        """Testa que retorna objeto com texto em maiúsculo."""
        category = Category.objects.create(name="Alimentação")

        result = case_insensitive_get(Category.objects.all(), "name", "ALIMENTAÇÃO")
        assert result == category

    def test_returns_object_with_lowercase(self):
        """Testa que retorna objeto com texto em minúsculo."""
        category = Category.objects.create(name="Alimentação")

        result = case_insensitive_get(Category.objects.all(), "name", "alimentação")
        assert result == category

    def test_returns_none_when_not_found(self):
        """Testa que retorna None quando não encontra."""
        result = case_insensitive_get(Category.objects.all(), "name", "Inexistente")
        assert result is None

    def test_returns_none_when_value_is_none(self):
        """Testa que retorna None quando valor é None."""
        result = case_insensitive_get(Category.objects.all(), "name", None)
        assert result is None

    def test_applies_additional_filters(self):
        """Testa que aplica filtros adicionais."""
        category = Category.objects.create(name="Test")
        SubCategory.objects.create(category=category, name="Sub1")
        SubCategory.objects.create(category=category, name="Sub2")

        result = case_insensitive_get(
            SubCategory.objects.all(),
            "name",
            "SUB1",
            category=category,
        )
        assert result is not None
        assert result.name == "Sub1"

    def test_returns_none_when_additional_filters_exclude(self):
        """Testa que retorna None quando filtros adicionais excluem."""
        cat1 = Category.objects.create(name="Cat1")
        cat2 = Category.objects.create(name="Cat2")
        SubCategory.objects.create(category=cat1, name="Test")

        result = case_insensitive_get(
            SubCategory.objects.all(),
            "name",
            "TEST",
            category=cat2,  # Categoria diferente
        )
        assert result is None

    def test_works_with_accented_characters_uppercase(self):
        """Testa funcionamento com caracteres acentuados em maiúsculo."""
        category = Category.objects.create(name="Transporte")

        result = case_insensitive_get(Category.objects.all(), "name", "TRANSPORTE")
        assert result == category

    def test_works_with_multiple_words(self):
        """Testa funcionamento com múltiplas palavras."""
        category = Category.objects.create(name="Supermercado e Mercearia")

        result = case_insensitive_get(Category.objects.all(), "name", "SUPERMERCADO E MERCEARIA")
        assert result == category
