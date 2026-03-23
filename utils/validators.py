"""Валидаторы данных"""

MIN_QUANTITY = 1
MAX_QUANTITY = 100


def validate_quantity(quantity: str) -> tuple[bool, int, str]:
    """Валидация количества прокси"""
    try:
        qty = int(quantity)
        if qty < MIN_QUANTITY or qty > MAX_QUANTITY:
            return False, 0, f"Количество должно быть от {MIN_QUANTITY} до {MAX_QUANTITY}"
        return True, qty, ""
    except ValueError:
        return False, 0, "Введите корректное число"
