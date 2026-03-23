"""Обработчик текстовых сообщений"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.database import db

logger = logging.getLogger(__name__)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка текстовых сообщений"""
    waiting_for = context.user_data.get('waiting_for')

    if waiting_for == 'topup_amount':
        await handle_topup_amount_input(update, context, update.message.text)
    else:
        await update.message.reply_text(
            "Используйте кнопки меню для навигации.",
            parse_mode='HTML'
        )


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
            await context.bot.send_message(chat_id=user_id, text="❌ Минимальная сумма — 50 ₽", parse_mode="HTML")
            return

        context.user_data["topup_amount"] = amount
        context.user_data.pop("waiting_for", None)

        msg_id = context.user_data.get("topup_message_id")
        if msg_id:
            text_msg = f"💳 <b>Пополнение на {amount} ₽</b>\n\nВыберите способ оплаты:"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 СБП / QR", callback_data="topup_pay_2")],
                [InlineKeyboardButton("💳 Карта МИР", callback_data="topup_pay_10")],
                [InlineKeyboardButton("🌍 International", callback_data="topup_pay_12")],
                [InlineKeyboardButton("◀️ Назад", callback_data="topup")]
            ])
            try:
                await context.bot.edit_message_caption(
                    chat_id=user_id, message_id=msg_id,
                    caption=text_msg, reply_markup=keyboard, parse_mode="HTML")
            except Exception:
                await context.bot.edit_message_text(
                    chat_id=user_id, message_id=msg_id,
                    text=text_msg, reply_markup=keyboard, parse_mode="HTML")
    except ValueError:
        await context.bot.send_message(chat_id=user_id, text="❌ Введите число.", parse_mode="HTML")
