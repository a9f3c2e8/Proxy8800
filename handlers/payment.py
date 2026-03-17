"""Обработчик пополнения баланса через Platega.io"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.database import db
from services.payment import create_payment, check_payment

logger = logging.getLogger(__name__)

PRESET_AMOUNTS = [100, 200, 500, 1000]


async def topup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать меню пополнения баланса"""
    query = update.callback_query
    await query.answer()

    keyboard = []
    # Пресеты по 2 в ряд
    for i in range(0, len(PRESET_AMOUNTS), 2):
        row = []
        for j in range(2):
            if i + j < len(PRESET_AMOUNTS):
                amt = PRESET_AMOUNTS[i + j]
                row.append(InlineKeyboardButton(f"{amt} ₽", callback_data=f"topup_amt_{amt}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✏️ Своя сумма", callback_data="topup_custom")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="profile")])

    text = (
        "💳 <b>Пополнение баланса</b>\n\n"
        "Выберите сумму или введите свою:"
    )

    try:
        await query.message.edit_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
    except Exception:
        await query.message.edit_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )


async def topup_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пользователь выбрал пресетную сумму — выбор метода оплаты"""
    query = update.callback_query
    await query.answer()

    amount = int(query.data.split("_")[-1])
    context.user_data["topup_amount"] = amount
    await _show_payment_methods(query.message, amount)


async def topup_custom_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пользователь хочет ввести свою сумму"""
    query = update.callback_query
    await query.answer()

    context.user_data["waiting_for"] = "topup_amount"

    text = (
        "💳 <b>Введите сумму пополнения</b>\n\n"
        "<blockquote><i>Минимум 50 ₽</i></blockquote>"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Отмена", callback_data="topup")]
    ])

    try:
        msg = await query.message.edit_caption(
            caption=text, reply_markup=keyboard, parse_mode="HTML"
        )
    except Exception:
        msg = await query.message.edit_text(
            text=text, reply_markup=keyboard, parse_mode="HTML"
        )
    context.user_data["topup_message_id"] = msg.message_id


async def topup_method_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пользователь выбрал метод оплаты — создаём платёж"""
    query = update.callback_query
    await query.answer()

    method = int(query.data.split("_")[-1])
    amount = context.user_data.get("topup_amount", 0)
    user_id = update.effective_user.id

    if amount < 50:
        await query.answer("Минимум 50 ₽", show_alert=True)
        return

    # Создаём платёж
    result = await create_payment(amount, user_id, payment_method=method)

    if not result:
        text = "❌ <b>Ошибка создания платежа</b>\n\nПопробуйте позже."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="topup")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
        ])
        try:
            await query.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            await query.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Сохраняем transaction_id для проверки
    context.user_data["pending_tx_id"] = result["transaction_id"]
    context.user_data["pending_tx_amount"] = amount

    text = (
        f"💳 <b>Оплата {amount} ₽</b>\n\n"
        f"Нажмите кнопку ниже для перехода к оплате.\n"
        f"После оплаты нажмите «✅ Я оплатил»."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Перейти к оплате", url=result["redirect"])],
        [InlineKeyboardButton("✅ Я оплатил", callback_data="topup_check")],
        [InlineKeyboardButton("❌ Отмена", callback_data="profile")]
    ])

    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await query.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")

    logger.info(f"Платёж создан: {result['transaction_id']} на {amount}₽ для {user_id}")


async def topup_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка статуса платежа"""
    query = update.callback_query
    user_id = update.effective_user.id

    tx_id = context.user_data.get("pending_tx_id")
    amount = context.user_data.get("pending_tx_amount", 0)

    if not tx_id:
        await query.answer("Нет активного платежа", show_alert=True)
        return

    await query.answer("⏳ Проверяю...")

    status = await check_payment(tx_id)

    if status == "CONFIRMED":
        # Зачисляем баланс
        db.add_balance(user_id, amount)
        context.user_data.pop("pending_tx_id", None)
        context.user_data.pop("pending_tx_amount", None)
        context.user_data.pop("balance", None)  # сбросить кэш

        new_balance = db.get_balance(user_id)
        text = (
            f"✅ <b>Оплата подтверждена!</b>\n\n"
            f"Зачислено: <b>{amount} ₽</b>\n"
            f"Баланс: <b>{new_balance:.2f} ₽</b>"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Приобрести", callback_data="buy_proxy")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
        ])
        logger.info(f"Платёж {tx_id} подтверждён, +{amount}₽ для {user_id}")

    elif status in ("EXPIRED", "CANCELED", "FAILED"):
        context.user_data.pop("pending_tx_id", None)
        context.user_data.pop("pending_tx_amount", None)

        status_text = {"EXPIRED": "истёк", "CANCELED": "отменён", "FAILED": "ошибка"}
        text = (
            f"❌ <b>Платёж {status_text.get(status, status)}</b>\n\n"
            f"Попробуйте ещё раз."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Попробовать снова", callback_data="topup")],
            [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")]
        ])

    else:
        # PENDING или неизвестный
        text = (
            f"⏳ <b>Ожидание оплаты</b>\n\n"
            f"Сумма: <b>{amount} ₽</b>\n\n"
            f"Если вы уже оплатили — подождите минуту и нажмите «✅ Я оплатил» ещё раз."
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Я оплатил", callback_data="topup_check")],
            [InlineKeyboardButton("❌ Отмена", callback_data="profile")]
        ])

    try:
        await query.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await query.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")


async def _show_payment_methods(message, amount: int):
    """Показать выбор метода оплаты"""
    text = (
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
        await message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
