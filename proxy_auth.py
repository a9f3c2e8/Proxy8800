"""Система аутентификации прокси через URL"""
import base64
import hashlib
from typing import Tuple, Optional


class ProxyAuth:
    """Генерация и проверка учетных данных через URL"""
    
    def __init__(self, secret_key: str = "8800proxy_secret_key_2024"):
        self.secret_key = secret_key
    
    def encode_credentials(self, username: str, password: str) -> str:
        """Кодирование учетных данных в URL-безопасную строку"""
        # Объединяем username:password
        credentials = f"{username}:{password}"
        # Кодируем в base64
        encoded = base64.urlsafe_b64encode(credentials.encode()).decode()
        # Убираем padding
        return encoded.rstrip('=')
    
    def decode_credentials(self, encoded: str) -> Tuple[str, str]:
        """Декодирование учетных данных из строки"""
        # Добавляем padding если нужно
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += '=' * padding
        
        # Декодируем из base64
        decoded = base64.urlsafe_b64decode(encoded.encode()).decode()
        
        # Разделяем username:password
        username, password = decoded.split(':', 1)
        return username, password
    
    def generate_proxy_url(self, username: str, password: str, subdomain: str = None) -> str:
        """Генерация URL для прокси"""
        # Кодируем учетные данные
        encoded = self.encode_credentials(username, password)
        
        # Создаем поддомен с учетными данными
        if subdomain:
            domain = f"{subdomain}.{encoded}.8800.life"
        else:
            domain = f"{encoded}.8800.life"
        
        return domain
    
    def parse_domain(self, domain: str) -> Optional[Tuple[str, str]]:
        """Извлечение учетных данных из домена"""
        try:
            # Убираем .8800.life
            if '.8800.life' in domain:
                parts = domain.replace('.8800.life', '').split('.')
                # Берем последнюю часть (закодированные учетные данные)
                encoded = parts[-1]
                return self.decode_credentials(encoded)
        except Exception as e:
            return None
        return None
    
    def generate_telegram_link(self, username: str, password: str, port: int = 1080) -> str:
        """Генерация ссылки для Telegram"""
        domain = self.generate_proxy_url(username, password)
        return f"https://t.me/socks?server={domain}&port={port}"


# Глобальный экземпляр
proxy_auth = ProxyAuth()
