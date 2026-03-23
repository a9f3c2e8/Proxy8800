"""Обработчики для покупки прокси"""
import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from core.database import db
from keyboards import service_type_keyboard
from core.config import ADMIN_ID, MENU_IMAGES

logger = logging.getLogger(__name__)


async def buy_proxy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начало процесса покупки - выбор типа сервиса"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_ID

    if is_admin:
        text = (
            "🛒 <b>Выберите тип сервиса</b>\n\n"
            "<b>📱 Прокси</b>\n"
            "<blockquote><i>Для Telegram</i></blockquote>\n\n"
            "<b>🌐 VPN</b>\n"
            "<blockquote><i>Для всех приложений</i></blockquote>"
        )
    else:
        text = (
            "🛒 <b>Выберите тип сервиса</b>\n\n"
            "<b>📱 Прокси</b>\n"
            "<blockquote><i>Для Telegram</i></blockquote>\n\n"
            "<b>🔴 VPN</b>\n"
            "<blockquote><i>Ведутся работы</i></blockquote>"
        )

    try:
        photo_id = context.bot_data.get('locations_photo_file_id', MENU_IMAGES['locations'])
        media = InputMediaPhoto(media=photo_id, caption=text, parse_mode='HTML')
        msg = await query.message.edit_media(media=media, reply_markup=service_type_keyboard(is_admin=is_admin))
        if 'locations_photo_file_id' not in context.bot_data:
            context.bot_data['locations_photo_file_id'] = msg.photo[-1].file_id
    except Exception:
        await query.message.delete()
        msg = await query.message.reply_photo(
            photo=context.bot_data.get('locations_photo_file_id', MENU_IMAGES['locations']),
            caption=text, reply_markup=service_type_keyboard(is_admin=is_admin), parse_mode='HTML'
        )
        if 'locations_photo_file_id' not in context.bot_data:
            context.bot_data['locations_photo_file_id'] = msg.photo[-1].file_id
