"""Обработчик помощи"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from keyboards import back_to_main_keyboard
from utils import emoji

logger = logging.getLogger(__name__)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать справку"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"ℹ️ <b>Справка по боту</b>\n\n"
        f"{emoji.money()} <b>Баланс</b>\n"
        f"Проверка остатка на счете\n"
        f"Начальный баланс: 1000 ₽\n\n"
        f"🛒 <b>Купить прокси</b>\n"
        f"Заказ новых прокси:\n"
        f"• IPv4 Dedicated\n"
        f"• Ближайший сервер\n"
        f"• Период от 1 до 6 месяцев\n\n"
        f"📋 <b>Мои прокси</b>\n"
        f"Список активных прокси с данными для подключения\n\n"
        f"<b>🔧 Как использовать прокси:</b>\n\n"
        f"<b>Telegram:</b>\n"
        f"Нажмите кнопку 'Подключить к Telegram' в разделе 'Мои прокси'\n\n"
        f"<b>Браузер:</b>\n"
        f"1. Скопируйте IP, порт, логин и пароль\n"
        f"2. В настройках браузера найдите 'Прокси-сервер'\n"
        f"3. Выберите SOCKS5 и введите данные\n\n"
        f"<b>Мобильные приложения:</b>\n"
        f"Используйте приложения типа ProxyDroid (Android) или Shadowrocket (iOS)\n\n"
        f"<blockquote><i>Используйте прокси ответственно</i></blockquote>\n\n"
        f"📞 <b>Поддержка:</b> @proxylin_support"
    )
    
    await query.message.edit_text(
        text,
        reply_markup=back_to_main_keyboard(),
        parse_mode='HTML'
    )
