"""Менеджер прокси - интеграция с ботом"""
import asyncio
import random
import string
from typing import Dict, List
from proxy_server import SOCKS5Server


class ProxyManager:
    """Менеджер прокси-сервера"""
    
    def __init__(self, domain: str = '8800.life', port: int = 1080):
        self.domain = domain
        self.port = port
        self.server = SOCKS5Server(host='0.0.0.0', port=port)
        self.active_users = {}  # {user_id: {'username': ..., 'password': ...}}
    
    def generate_credentials(self) -> Dict[str, str]:
        """Генерация логина и пароля"""
        username = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return {'username': username, 'password': password}
    
    def create_proxy(self, user_id: int) -> Dict[str, str]:
        """Создать прокси для пользователя"""
        creds = self.generate_credentials()
        
        # Добавляем пользователя в SOCKS5 сервер
        self.server.add_user(creds['username'], creds['password'])
        
        # Сохраняем
        self.active_users[user_id] = creds
        
        # Возвращаем данные для подключения
        return {
            'server': self.domain,
            'port': self.port,
            'username': creds['username'],
            'password': creds['password'],
            'telegram_link': f"https://t.me/socks?server={self.domain}&port={self.port}&user={creds['username']}&pass={creds['password']}"
        }
    
    def remove_proxy(self, user_id: int):
        """Удалить прокси пользователя"""
        if user_id in self.active_users:
            creds = self.active_users[user_id]
            self.server.remove_user(creds['username'])
            del self.active_users[user_id]
    
    async def start(self):
        """Запуск прокси-сервера"""
        await self.server.start()


# Глобальный экземпляр
proxy_manager = ProxyManager(domain='8800.life', port=1080)
