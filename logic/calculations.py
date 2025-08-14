import pandas as pd


def calculate_profit(F, G, H):
    """
    Расчёт прибыли предпринимателя.
    F — ставка рефинансирования (в долях, не процентах),
    G — доля авансовых платежей (в долях),
    H — число лет строительства.
    """
    profit = round(0.5 * H * F * (1 + H * F / 3 + G * (1 + (2 * H**2 * F**2) / 3))*100, 0)
    return profit


def get_unit_multiplier(data):
    """
    Определяет коэффициент умножения по единице измерения:
    возвращает значение площади, объёма или длины (или 1 по умолчанию).
    """
    if data.get("line_square") not in [None, 0]:
        return data["line_square"]
    elif data.get("line_weight") not in [None, 0]:
        return data["line_weight"]
    elif data.get("line_length") not in [None, 0]:
        return data["line_length"]
    return 1
def get_actual_unit_value(df: pd.DataFrame, page2_obj) -> float:
    """
    Возвращает значение объёма, площади или длины ОЦЕНИВАЕМОГО ЛИТЕРА
    в зависимости от того, по какой единице дана цена УКУП.
    """
    if df is None or df.empty:
        return 1.0  # Безопасное значение по умолчанию

    row = df.iloc[0]

    try:
        if pd.notna(row.get("Объём до м3")):
            return float(page2_obj.line_weight.text().replace(",", "."))
        elif pd.notna(row.get("Площадь до м2")):
            return float(page2_obj.line_square.text().replace(",", "."))
        elif pd.notna(row.get("Протяженность")):
            return float(page2_obj.line_length.text().replace(",", "."))
    except Exception:
        return 1.0  # Если поле пустое или некорректное

    return 1.0
