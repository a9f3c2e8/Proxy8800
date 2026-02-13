"""Core модули бота"""
from .config import *
from .database import db
from .proxy_manager import ProxyManager

__all__ = ['db', 'ProxyManager']
