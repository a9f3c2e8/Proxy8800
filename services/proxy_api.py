"""Клиент для работы с Proxy API"""
import aiohttp
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class ProxyAPIClient:
    """Клиент для взаимодействия с API прокси-сервера"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def _request(self, method: str, endpoint: str, **kwargs):
        """Выполнить HTTP запрос"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, headers=self.headers, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"API error {response.status}: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Request error: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Проверить доступность API"""
        result = await self._request('GET', '/api/health')
        return result is not None and result.get('status') == 'ok'
    
    async def create_user(self, telegram_user_id: int, username: str, password: str, 
                         days: int = 30, traffic_limit: int = 0) -> Optional[Dict]:
        """Создать пользователя прокси"""
        data = {
            'telegram_user_id': telegram_user_id,
            'username': username,
            'password': password,
            'days': days,
            'traffic_limit': traffic_limit
        }
        
        result = await self._request('POST', '/api/user/create', json=data)
        
        if result and result.get('success'):
            logger.info(f"Создан прокси-пользователь {username} для TG {telegram_user_id}")
            return result
        else:
            logger.error(f"Не удалось создать пользователя: {result}")
            return None
    
    async def get_user(self, telegram_user_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе"""
        result = await self._request('GET', f'/api/user/{telegram_user_id}')
        return result
    
    async def get_user_stats(self, telegram_user_id: int) -> Optional[Dict]:
        """Получить статистику пользователя"""
        result = await self._request('GET', f'/api/user/{telegram_user_id}/stats')
        return result
    
    async def extend_subscription(self, username: str, days: int) -> bool:
        """Продлить подписку"""
        data = {'days': days}
        result = await self._request('POST', f'/api/user/{username}/extend', json=data)
        return result is not None and result.get('success')
    
    async def delete_user(self, username: str) -> bool:
        """Удалить пользователя"""
        result = await self._request('DELETE', f'/api/user/{username}')
        return result is not None and result.get('success')
    
    async def list_users(self) -> Optional[List[Dict]]:
        """Получить список всех пользователей"""
        result = await self._request('GET', '/api/users')
        if result:
            return result.get('users', [])
        return None
    
    async def verify_credentials(self, username: str, password: str) -> Optional[Dict]:
        """Проверить учетные данные"""
        data = {'username': username, 'password': password}
        result = await self._request('POST', '/api/verify', json=data)
        return result


# Глобальный экземпляр клиента
proxy_api = None


def init_proxy_api(base_url: str, api_key: str):
    """Инициализировать клиент API"""
    global proxy_api
    proxy_api = ProxyAPIClient(base_url, api_key)
    logger.info(f"Proxy API клиент инициализирован: {base_url}")
    return proxy_api
