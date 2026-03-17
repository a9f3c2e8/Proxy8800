"""Обработчик баланса — перенаправляет на пополнение"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Перенаправление на пополнение баланса"""
    from .payment import topup_handler
    await topup_handler(update, context)
