"""Обработчик помощи"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import back_to_main_keyboard

logger = logging.getLogger(__name__)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать справку"""
    query = update.callback_query
    await query.answer()

    text = (
        "ℹ️ <b>Справка по боту 8800.life</b>\n\n"
        "🛒 <b>Приобрести</b>\n"
        "Покупка прокси или VPN подписки\n\n"
        "📱 <b>Прокси для Telegram</b>\n"
        "Нажмите «Подключить к Telegram» — подключится автоматически\n\n"
        "🌐 <b>VPN для всех приложений</b>\n"
        "1. Скачайте V2Box / Streisand (iOS) или V2rayNG (Android)\n"
        "2. Скопируйте ссылку подписки из бота\n"
        "3. Добавьте подписку в приложение\n\n"
        "👤 <b>Профиль</b>\n"
        "Баланс, подключения, пополнение\n\n"
        "💬 <b>Поддержка:</b> @eight80zero_support"
    )

    try:
        await query.message.edit_caption(caption=text, reply_markup=back_to_main_keyboard(), parse_mode='HTML')
    except Exception:
        await query.message.edit_text(text=text, reply_markup=back_to_main_keyboard(), parse_mode='HTML')
