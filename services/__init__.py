"""Сервисы бота"""
from .api_client import webshare_client
from .proxy_api import proxy_api, init_proxy_api

__all__ = ['webshare_client', 'proxy_api', 'init_proxy_api']
