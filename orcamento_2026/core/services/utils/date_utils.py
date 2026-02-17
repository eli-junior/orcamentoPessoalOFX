from datetime import date
from dateutil.relativedelta import relativedelta


def get_period_options(base_date: date | None = None, num_options: int = 3, ref_day: int = 20) -> list[tuple[date, str]]:
    """
    Retorna uma lista de opções de datas de referência baseadas na data base.
    As opções são: mês passado, mês corrente, próximo mês.

    Args:
        base_date: Data base para o cálculo. Se None, usa o dia atual.
        num_options: Número de opções a retornar (default 3).

    Returns:
        Lista de tuplas (data_referencia, label_descritiva)
    """
    if base_date is None:
        base_date = date.today()

    # Normaliza para o dia de referência do mês
    current_month = base_date.replace(day=ref_day)

    options = []

    # Mês passado
    prev_month = current_month - relativedelta(months=1)
    options.append((prev_month, f"Mês Passado ({prev_month.strftime('%B %Y')})"))

    # Mês corrente
    options.append((current_month, f"Mês Corrente ({current_month.strftime('%B %Y')})"))

    # Próximo mês
    next_month = current_month + relativedelta(months=1)
    options.append((next_month, f"Próximo Mês ({next_month.strftime('%B %Y')})"))

    return options
