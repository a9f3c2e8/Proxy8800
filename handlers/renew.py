"""Обработчик продления прокси"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import back_to_main_keyboard

logger = logging.getLogger(__name__)


async def renew_proxy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Продление прокси"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "🔄 <b>Продление прокси</b>\n\n"
        "Функция в разработке.\n\n"
        "Скоро вы сможете продлевать прокси прямо из бота!"
    )
    
    await query.message.edit_text(
        text,
        reply_markup=back_to_main_keyboard(),
        parse_mode='HTML'
    )
