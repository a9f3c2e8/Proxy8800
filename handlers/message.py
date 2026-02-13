"""Обработчик текстовых сообщений"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from core.database import db
from keyboards import confirm_order_keyboard, back_to_main_keyboard
from core.config import COUNTRIES, PERIODS, MIN_QUANTITY, MAX_QUANTITY

logger = logging.getLogger(__name__)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    waiting_for = context.user_data.get('waiting_for')
    
    if waiting_for == 'api_key':
        await handle_api_key_input(update, context, text)
    elif waiting_for == 'quantity':
        await handle_quantity_input(update, context, text)
    else:
        await update.message.reply_text(
            "Используйте кнопки меню для навигации.",
            parse_mode='HTML'
        )


async def handle_api_key_input(update: Update, context: ContextTypes.DEFAULT_TYPE, api_key: str) -> None:
    """Обработка ввода API ключа"""
    from .api_key import save_api_key_handler
    await save_api_key_handler(update, context)


async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Обработка ввода количества прокси"""
    user_id = update.effective_user.id
    
    # Удаляем сообщение пользователя с числом
    try:
        await update.message.delete()
    except Exception as e:
        logger.error(f"Не удалось удалить сообщение: {e}")
    
    try:
        quantity = int(text)
        
        if quantity < MIN_QUANTITY or quantity > MAX_QUANTITY:
            # Если неправильное число, отправляем новое сообщение
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Введите число от {MIN_QUANTITY} до {MAX_QUANTITY}.",
                parse_mode='HTML'
            )
            return
        
        db.set_user_data(user_id, 'buy_quantity', quantity)
        context.user_data.pop('waiting_for', None)
        
        # Получаем тип сервиса
        service_type = db.get_user_data(user_id, 'service_type', 'proxy')
        
        # Цены за 1 прокси на 1 месяц (30 дней)
        if service_type == 'vpn':
            price_per_month = 99.0  # VPN: 99₽ за месяц
        else:
            price_per_month = 50.0  # Прокси: 50₽ за месяц
        
        # Рассчитываем пропорционально периоду
        period_days = int(db.get_user_data(user_id, 'buy_period'))
        price_per_day = price_per_month / 30  # цена за 1 день
        amount = price_per_day * period_days * quantity
        db.set_user_data(user_id, 'buy_amount', amount)
        
        # Получаем тип сервиса
        service_name = "📱 Прокси (Telegram)" if service_type == 'proxy' else "🌐 VPN (Все сервисы)"
        
        text = (
            f"📝 <b>Подтверждение заказа</b>\n\n"
            f"Сервис: {service_name}\n"
            f"Локация: Ближайшая\n"
            f"Количество: {quantity} шт.\n"
            f"Период: {PERIODS.get(db.get_user_data(user_id, 'buy_period'))}\n\n"
            f"💰 Стоимость: <b>{amount:.2f} ₽</b>\n\n"
            f"💳 Ваш баланс: <b>{db.get_balance(user_id):.2f} ₽</b>"
        )
        
        logger.info(f"Пользователь {user_id} рассчитал заказ: {amount:.2f} ₽")
        
        # Получаем ID сообщения с запросом количества
        quantity_message_id = context.user_data.get('quantity_message_id')
        
        if quantity_message_id:
            # Редактируем предыдущее сообщение
            try:
                await context.bot.edit_message_caption(
                    chat_id=user_id,
                    message_id=quantity_message_id,
                    caption=text,
                    reply_markup=confirm_order_keyboard(),
                    parse_mode='HTML'
                )
                context.user_data.pop('quantity_message_id', None)
            except Exception as e:
                logger.error(f"Не удалось отредактировать сообщение: {e}")
                # Если не получилось отредактировать, отправляем новое
                await context.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=confirm_order_keyboard(),
                    parse_mode='HTML'
                )
        else:
            # Если нет ID, отправляем новое сообщение
            await context.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=confirm_order_keyboard(),
                parse_mode='HTML'
            )
    
    except ValueError:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Введите корректное число.",
            parse_mode='HTML'
        )
