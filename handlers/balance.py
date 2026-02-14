"""Обработчик баланса"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.database import db
from keyboards import back_to_main_keyboard

logger = logging.getLogger(__name__)


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать баланс пользователя"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Быстрый ответ
    await query.answer()
    
    # Кэшируем данные
    if 'balance' not in context.user_data:
        context.user_data['balance'] = db.get_balance(user_id)
    balance = context.user_data['balance']
    
    proxy_count = db.get_proxy_count(user_id)
    
    text = (
        f"💰 <b>Ваш баланс</b>\n\n"
        f"Доступно: <b>{balance:.2f} ₽</b>\n"
        f"Активных прокси: <b>{proxy_count} шт.</b>\n\n"
        f"Используйте баланс для покупки прокси."
    )
    
    logger.info(f"Пользователь {user_id} проверил баланс: {balance:.2f} ₽")
    
    await query.message.edit_text(
        text,
        reply_markup=back_to_main_keyboard(),
        parse_mode='HTML'
    )
