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
    elif waiting_for == 'topup_amount':
        await handle_topup_amount_input(update, context, text)
    else:
        await update.message.reply_text(
            "Используйте кнопки меню для навигации.",
            parse_mode='HTML'
        )


async def handle_api_key_input(update: Update, context: ContextTypes.DEFAULT_TYPE, api_key: str) -> None:
    """Обработка ввода API ключа"""
    from .api_key import save_api_key_handler
    await save_api_key_handler(update, context)


async def handle_topup_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Обработка ввода суммы пополнения"""
    user_id = update.effective_user.id

    try:
        await update.message.delete()
    except Exception:
        pass

    try:
        amount = int(text)
        if amount < 50:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Минимальная сумма — 50 ₽",
                parse_mode="HTML",
            )
            return

        context.user_data["topup_amount"] = amount
        context.user_data.pop("waiting_for", None)

        # Показываем выбор метода оплаты
        from handlers.payment import _show_payment_methods
        msg_id = context.user_data.get("topup_message_id")
        if msg_id:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            text_msg = (
                f"💳 <b>Пополнение на {amount} ₽</b>\n\n"
                f"Выберите способ оплаты:"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 СБП / QR", callback_data="topup_pay_2")],
                [InlineKeyboardButton("💳 Карта МИР", callback_data="topup_pay_10")],
                [InlineKeyboardButton("🌍 International", callback_data="topup_pay_12")],
                [InlineKeyboardButton("◀️ Назад", callback_data="topup")]
            ])
            try:
                await context.bot.edit_message_caption(
                    chat_id=user_id,
                    message_id=msg_id,
                    caption=text_msg,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            except Exception:
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=msg_id,
                    text=text_msg,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
    except ValueError:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Введите число.",
            parse_mode="HTML",
        )


async def handle_quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    """Обработка ввода количества прокси"""
    user_id = update.effective_user.id
    
    # Удаляем сообщение пользователя с числом
    try:
        await update.message.delete()
    except Exception:
        pass
    
    try:
        quantity = int(text)
        
        if quantity < MIN_QUANTITY or quantity > MAX_QUANTITY:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Введите число от {MIN_QUANTITY} до {MAX_QUANTITY}.",
                parse_mode='HTML'
            )
            return
        
        # Кэшируем в context
        context.user_data['buy_quantity'] = quantity
        db.set_user_data(user_id, 'buy_quantity', quantity)
        context.user_data.pop('waiting_for', None)
        
        # Получаем тип сервиса из кэша
        service_type = context.user_data.get('service_type') or db.get_user_data(user_id, 'service_type', 'proxy')
        context.user_data['service_type'] = service_type
        
        # Цены за 1 прокси на 1 месяц (30 дней)
        price_per_month = 99.0 if service_type == 'vpn' else 50.0
        
        # Рассчитываем пропорционально периоду
        period_days = int(context.user_data.get('buy_period') or db.get_user_data(user_id, 'buy_period'))
        price_per_day = price_per_month / 30
        amount = price_per_day * period_days * quantity
        
        context.user_data['buy_amount'] = amount
        db.set_user_data(user_id, 'buy_amount', amount)
        
        # Всегда свежий баланс
        balance = db.get_balance(user_id)
        context.user_data['balance'] = balance
        
        # Получаем тип сервиса
        service_name = "📱 Прокси (Telegram)" if service_type == 'proxy' else "🌐 VPN (Все сервисы)"
        period_name = PERIODS.get(context.user_data.get('buy_period') or db.get_user_data(user_id, 'buy_period'))
        
        text = (
            f"📝 <b>Подтверждение заказа</b>\n\n"
            f"Сервис: {service_name}\n"
            f"Локация: Ближайшая\n"
            f"Количество: {quantity} шт.\n"
            f"Период: {period_name}\n\n"
            f"💰 Стоимость: <b>{amount:.2f} ₽</b>\n\n"
            f"💳 Ваш баланс: <b>{balance:.2f} ₽</b>"
        )
        
        logger.info(f"Пользователь {user_id} рассчитал заказ: {amount:.2f} ₽")
        
        # Получаем ID сообщения с запросом количества
        quantity_message_id = context.user_data.get('quantity_message_id')
        
        if quantity_message_id:
            try:
                await context.bot.edit_message_caption(
                    chat_id=user_id,
                    message_id=quantity_message_id,
                    caption=text,
                    reply_markup=confirm_order_keyboard(),
                    parse_mode='HTML'
                )
                context.user_data.pop('quantity_message_id', None)
            except Exception:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=confirm_order_keyboard(),
                    parse_mode='HTML'
                )
        else:
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
