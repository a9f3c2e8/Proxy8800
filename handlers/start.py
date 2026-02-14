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
        # Кэшируем file_id картинки
        if 'main_photo_file_id' in context.bot_data:
            await update.message.reply_photo(
                photo=context.bot_data['main_photo_file_id'],
                caption=welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode='HTML'
            )
        else:
            msg = await update.message.reply_photo(
                photo=MENU_IMAGES['main'],
                caption=welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode='HTML'
            )
            # Сохраняем file_id для последующего использования
            context.bot_data['main_photo_file_id'] = msg.photo[-1].file_id
    elif update.callback_query:
        try:
            # Используем кэшированный file_id если есть
            photo_id = context.bot_data.get('main_photo_file_id', MENU_IMAGES['main'])
            media = InputMediaPhoto(
                media=photo_id,
                caption=welcome_text,
                parse_mode='HTML'
            )
            msg = await update.callback_query.message.edit_media(
                media=media,
                reply_markup=main_menu_keyboard()
            )
            # Сохраняем file_id если это первый раз
            if 'main_photo_file_id' not in context.bot_data:
                context.bot_data['main_photo_file_id'] = msg.photo[-1].file_id
        except Exception:
            await update.callback_query.message.delete()
            msg = await update.callback_query.message.reply_photo(
                photo=context.bot_data.get('main_photo_file_id', MENU_IMAGES['main']),
                caption=welcome_text,
                reply_markup=main_menu_keyboard(),
                parse_mode='HTML'
            )
            if 'main_photo_file_id' not in context.bot_data:
                context.bot_data['main_photo_file_id'] = msg.photo[-1].file_id
