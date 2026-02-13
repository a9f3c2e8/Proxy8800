"""Обработчик API ключа (не используется в упрощенной версии)"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import back_to_main_keyboard

logger = logging.getLogger(__name__)


async def set_api_key_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Заглушка для API ключа"""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "ℹ️ API ключ не требуется в этой версии бота.",
        reply_markup=back_to_main_keyboard(),
        parse_mode='HTML'
    )


async def save_api_key_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Заглушка для сохранения API ключа"""
    pass
