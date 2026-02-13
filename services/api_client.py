"""Клиент для работы с Webshare API"""
import requests
import logging
from typing import Optional, List, Dict
from core.config import WEBSHARE_API_KEY, WEBSHARE_API_URL

logger = logging.getLogger(__name__)


class WebshareClient:
    """Клиент для Webshare API"""
    
    def __init__(self):
        self.api_key = WEBSHARE_API_KEY
        self.base_url = WEBSHARE_API_URL
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_proxies(self, page: int = 1, page_size: int = 25) -> Optional[Dict]:
        """Получить список прокси"""
        try:
            url = f"{self.base_url}/proxy/list/"
            params = {
                "page": page,
                "page_size": page_size
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения прокси: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Исключение при получении прокси: {e}")
            return None
    
    def get_profile(self) -> Optional[Dict]:
        """Получить профиль пользователя"""
        try:
            url = f"{self.base_url}/profile/"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения профиля: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Исключение при получении профиля: {e}")
            return None


# Глобальный экземпляр
webshare_client = WebshareClient()
