"""Валидаторы данных"""
from core.config import MIN_QUANTITY, MAX_QUANTITY


def validate_quantity(quantity: str) -> tuple[bool, int, str]:
    """
    Валидация количества прокси
    
    Returns:
        (is_valid, quantity, error_message)
    """
    try:
        qty = int(quantity)
        if qty < MIN_QUANTITY or qty > MAX_QUANTITY:
            return False, 0, f"Количество должно быть от {MIN_QUANTITY} до {MAX_QUANTITY}"
        return True, qty, ""
    except ValueError:
        return False, 0, "Введите корректное число"


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """
    Валидация API ключа
    
    Returns:
        (is_valid, error_message)
    """
    if not api_key or len(api_key) < 10:
        return False, "API ключ слишком короткий"
    
    if ' ' in api_key:
        return False, "API ключ не должен содержать пробелы"
    
    return True, ""
