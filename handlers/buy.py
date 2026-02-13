"""Обработчики для покупки прокси"""
import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from core.database import db
from keyboards import (
    back_to_main_keyboard,
    proxy_type_keyboard,
    countries_keyboard,
    periods_keyboard,
    confirm_order_keyboard
)
from core.config import COUNTRIES, PERIODS, MIN_QUANTITY, MAX_QUANTITY, MENU_IMAGES

logger = logging.getLogger(__name__)


async def buy_proxy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало процесса покупки - выбор типа сервиса"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"🛒 <b>Выберите тип сервиса</b>\n\n"
        f"<b>📱 Прокси</b>\n"
        f"<blockquote><i>Обход блокировок Telegram</i></blockquote>\n\n"
        f"<b>🔴 VPN</b>\n"
        f"<blockquote><i>Ведутся работы</i></blockquote>"
    )
    
    from keyboards import service_type_keyboard
    
    try:
        media = InputMediaPhoto(
            media=MENU_IMAGES['locations'],
            caption=text,
            parse_mode='HTML'
        )
        await query.message.edit_media(
            media=media,
            reply_markup=service_type_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования медиа: {e}")
        await query.message.delete()
        await query.message.reply_photo(
            photo=MENU_IMAGES['locations'],
            caption=text,
            reply_markup=service_type_keyboard(),
            parse_mode='HTML'
        )
