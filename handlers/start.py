"""Обработчик команды /start"""
import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from keyboards import main_menu_keyboard
from core.config import MENU_IMAGES
from utils import emoji

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")
    
    welcome_text = (
        f"{emoji.star()} <b>Добро пожаловать в 8800 Proxy!</b>\n\n"
        f"<i>Ваш надежный партнер в мире прокси-серверов</i>\n\n"
        f"<blockquote>\"Качество и надежность - наш приоритет\"</blockquote>"
    )
    
    if update.message:
        await update.message.reply_photo(
            photo=MENU_IMAGES['main'],
            caption=welcome_text,
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )
    elif update.callback_query:
        try:
            media = InputMediaPhoto(
                media=MENU_IMAGES['main'],
                caption=welcome_text,
                parse_mode='HTML'
            )
            await update.callback_query.message.edit_media(
                media=media,
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка редактирования медиа: {e}")
            await update.callback_query.message.delete()
            await update.callback_query.message.reply_photo(
                photo=MENU_IMAGES['main'],
                caption=welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode='HTML'
            )
