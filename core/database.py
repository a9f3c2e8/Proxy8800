"""Управление данными пользователей (в продакшене заменить на БД)"""
from typing import Optional, Dict, List

class UserDatabase:
    """Класс для работы с данными пользователей"""
    
    def __init__(self):
        self._api_keys: Dict[int, str] = {}
        self._user_data: Dict[int, dict] = {}
        self._balances: Dict[int, float] = {}
        self._user_proxies: Dict[int, List[str]] = {}  # user_id -> список ID прокси
        self._assigned_proxies: Dict[str, dict] = {}  # proxy_id -> данные прокси с user_id
    
    def set_api_key(self, user_id: int, api_key: str) -> None:
        """Сохранить API ключ пользователя"""
        self._api_keys[user_id] = api_key
    
    def get_api_key(self, user_id: int) -> Optional[str]:
        """Получить API ключ пользователя"""
        return self._api_keys.get(user_id)
    
    def has_api_key(self, user_id: int) -> bool:
        """Проверить наличие API ключа"""
        return user_id in self._api_keys
    
    def remove_api_key(self, user_id: int) -> None:
        """Удалить API ключ пользователя"""
        self._api_keys.pop(user_id, None)
    
    def set_user_data(self, user_id: int, key: str, value) -> None:
        """Сохранить данные пользователя"""
        if user_id not in self._user_data:
            self._user_data[user_id] = {}
        self._user_data[user_id][key] = value
    
    def get_user_data(self, user_id: int, key: str, default=None):
        """Получить данные пользователя"""
        return self._user_data.get(user_id, {}).get(key, default)
    
    def clear_user_data(self, user_id: int) -> None:
        """Очистить данные пользователя"""
        self._user_data.pop(user_id, None)
    
    # Методы для работы с балансом
    def get_balance(self, user_id: int) -> float:
        """Получить баланс пользователя"""
        if user_id not in self._balances:
            self._balances[user_id] = 1000.0  # Начальный баланс
        return self._balances[user_id]
    
    def add_balance(self, user_id: int, amount: float) -> float:
        """Пополнить баланс"""
        current = self.get_balance(user_id)
        self._balances[user_id] = current + amount
        return self._balances[user_id]
    
    def subtract_balance(self, user_id: int, amount: float) -> bool:
        """Списать с баланса (возвращает True если успешно)"""
        current = self.get_balance(user_id)
        if current >= amount:
            self._balances[user_id] = current - amount
            return True
        return False
    
    # Методы для работы с прокси
    def assign_proxy(self, user_id: int, proxy_id: str, proxy_data: dict) -> None:
        """Назначить прокси пользователю"""
        if user_id not in self._user_proxies:
            self._user_proxies[user_id] = []
        
        self._user_proxies[user_id].append(proxy_id)
        self._assigned_proxies[proxy_id] = {
            **proxy_data,
            'user_id': user_id
        }
    
    def get_user_proxies(self, user_id: int) -> List[dict]:
        """Получить все прокси пользователя"""
        proxy_ids = self._user_proxies.get(user_id, [])
        return [self._assigned_proxies[pid] for pid in proxy_ids if pid in self._assigned_proxies]
    
    def is_proxy_assigned(self, proxy_id: str) -> bool:
        """Проверить, назначен ли прокси"""
        return proxy_id in self._assigned_proxies
    
    def get_proxy_count(self, user_id: int) -> int:
        """Получить количество прокси пользователя"""
        return len(self._user_proxies.get(user_id, []))


# Глобальный экземпляр
db = UserDatabase()
