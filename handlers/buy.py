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
        # Используем кэшированный file_id
        photo_id = context.bot_data.get('locations_photo_file_id', MENU_IMAGES['locations'])
        media = InputMediaPhoto(
            media=photo_id,
            caption=text,
            parse_mode='HTML'
        )
        msg = await query.message.edit_media(
            media=media,
            reply_markup=service_type_keyboard()
        )
        # Сохраняем file_id если это первый раз
        if 'locations_photo_file_id' not in context.bot_data:
            context.bot_data['locations_photo_file_id'] = msg.photo[-1].file_id
    except Exception:
        await query.message.delete()
        msg = await query.message.reply_photo(
            photo=context.bot_data.get('locations_photo_file_id', MENU_IMAGES['locations']),
            caption=text,
            reply_markup=service_type_keyboard(),
            parse_mode='HTML'
        )
        if 'locations_photo_file_id' not in context.bot_data:
            context.bot_data['locations_photo_file_id'] = msg.photo[-1].file_id
