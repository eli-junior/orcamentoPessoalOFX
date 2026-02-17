"""Testes para utilitários de data."""

from datetime import date


from orcamento_2026.core.services.utils.date_utils import get_period_options


class TestGetPeriodOptions:
    """Testes para a função get_period_options."""

    def test_default_base_date(self):
        """Testa que a função usa date.today() quando base_date é None."""
        options = get_period_options()

        # Deve retornar 3 opções
        assert len(options) == 3

        # Verifica que as opções têm o formato correto (data, label)
        for opt in options:
            assert isinstance(opt, tuple)
            assert len(opt) == 2
            assert isinstance(opt[0], date)
            assert isinstance(opt[1], str)

    def test_specific_base_date(self):
        """Testa com uma data base específica."""
        base = date(2026, 5, 15)
        options = get_period_options(base_date=base)

        assert len(options) == 3

        # Mês passado (abril)
        assert options[0][0].month == 4
        assert options[0][0].year == 2026
        assert "Mês Passado" in options[0][1]

        # Mês corrente (maio)
        assert options[1][0].month == 5
        assert options[1][0].year == 2026
        assert "Mês Corrente" in options[1][1]

        # Próximo mês (junho)
        assert options[2][0].month == 6
        assert options[2][0].year == 2026
        assert "Próximo Mês" in options[2][1]

    def test_custom_ref_day(self):
        """Testa com um dia de referência customizado."""
        base = date(2026, 5, 15)
        options = get_period_options(base_date=base, ref_day=10)

        # Todas as datas devem ter dia 10
        for opt, _ in options:
            assert opt.day == 10

    def test_year_boundary(self):
        """Testa comportamento na virada do ano."""
        base = date(2026, 1, 15)
        options = get_period_options(base_date=base)

        # Mês passado deve ser dezembro de 2025
        assert options[0][0].month == 12
        assert options[0][0].year == 2025

        # Mês corrente é janeiro de 2026
        assert options[1][0].month == 1
        assert options[1][0].year == 2026

        # Próximo mês é fevereiro de 2026
        assert options[2][0].month == 2
        assert options[2][0].year == 2026

    def test_labels_contain_month_names(self):
        """Testa que os labels contêm nomes dos meses."""
        base = date(2026, 6, 15)
        options = get_period_options(base_date=base)

        # Verifica que os labels contêm os nomes dos meses
        assert "June" in options[1][1] or "Junho" in options[1][1]

    def test_num_options_parameter(self):
        """Testa o parâmetro num_options (embora atualmente não seja usado na implementação)."""
        # Nota: A implementação atual sempre retorna 3 opções
        # Este teste documenta o comportamento esperado
        options = get_period_options(num_options=5)
        assert len(options) == 3  # Implementação atual ignora num_options
