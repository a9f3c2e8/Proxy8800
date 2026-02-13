"""Форматирование данных для отображения"""
from typing import Dict


def format_proxy_info(proxy: Dict) -> str:
    """Форматирование информации о прокси"""
    ip = proxy.get('ip', 'N/A')
    port = proxy.get('port', 'N/A')
    country = proxy.get('country', 'N/A').upper()
    date_end = proxy.get('date_end', 'N/A')
    proxy_type = proxy.get('type', 'N/A')
    
    return (
        f"{ip}:{port}\n"
        f"   🌍 {country} | 📦 {proxy_type}\n"
        f"   📅 До: {date_end}"
    )


def format_currency(amount: float) -> str:
    """Форматирование суммы в рублях"""
    return f"{amount:.2f} ₽"
