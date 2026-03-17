"""Обработчики бота"""
from .start import start_handler, check_sub_handler
from .balance import balance_handler
from .proxies import my_proxies_handler, view_proxy_handler, view_vpn_handler, proxy_page_handler
from .buy import buy_proxy_handler
from .help import help_handler
from .profile import profile_handler
from .support import support_handler
from .callback import callback_handler
from .message import message_handler

__all__ = [
    'start_handler',
    'check_sub_handler',
    'balance_handler',
    'my_proxies_handler',
    'view_proxy_handler',
    'view_vpn_handler',
    'proxy_page_handler',
    'buy_proxy_handler',
    'help_handler',
    'profile_handler',
    'support_handler',
    'callback_handler',
    'message_handler'
]
