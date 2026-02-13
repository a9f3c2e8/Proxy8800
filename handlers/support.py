"""Обработчик поддержки"""
import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from keyboards import back_to_main_keyboard
from core.config import MENU_IMAGES

logger = logging.getLogger(__name__)


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать информацию о поддержке"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    text = (
        "💬 <b>Поддержка</b>\n\n"
        "По всем вопросам обращайтесь:\n\n"
        "@eight80zero_support\n\n"
        "<blockquote><i>Мы всегда готовы помочь вам</i></blockquote>\n\n"
        "<a href='https://telegra.ph/Politika-konfidencialnosti-08-15-17'>Политика конфиденциальности</a> • "
        "<a href='https://telegra.ph/Polzovatelskoe-soglashenie-08-15-10'>Пользовательское соглашение</a>"
    )
    
    logger.info(f"Пользователь {user_id} открыл поддержку")
    
    try:
        media = InputMediaPhoto(
            media=MENU_IMAGES['support'],
            caption=text,
            parse_mode='HTML'
        )
        await query.message.edit_media(
            media=media,
            reply_markup=back_to_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования медиа: {e}")
        await query.message.delete()
        await query.message.reply_photo(
            photo=MENU_IMAGES['support'],
            caption=text,
            reply_markup=back_to_main_keyboard(),
            parse_mode='HTML'
        )
