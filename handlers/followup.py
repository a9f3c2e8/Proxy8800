"""Система добивов — follow-up сообщения для конверсии"""
import logging
import asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, Application
from core.database import db
from core.config import ADMIN_ID

logger = logging.getLogger(__name__)

# Тексты добивов после получения триала (не подключился)
TRIAL_FOLLOWUPS = [
    {
        "delay": 300,  # 5 минут
        "text": (
            "🔑 <b>Ключ готов, осталось подключить</b>\n\n"
            "Ты получил бесплатный доступ, но ещё не подключился.\n\n"
            "Это займёт буквально 2 минуты:\n"
            "1️⃣ Скачай приложение\n"
            "2️⃣ Вставь ссылку\n"
            "3️⃣ Готово — интернет без ограничений\n\n"
            "<blockquote><i>Не упусти — пробный период уже идёт ⏳</i></blockquote>"
        ),
        "buttons": [
            [("⚡ Подключиться сейчас", "my_proxies")],
            [("📱 Как подключить?", "followup_howto")],
        ]
    },
    {
        "delay": 3600,  # 1 час
        "text": (
            "👀 <b>Ты ещё не подключился</b>\n\n"
            "Пробный период тикает, а ты пока не пользуешься.\n\n"
            "🔓 Доступ ко всем сайтам и приложениям\n"
            "🎮 Стабильное соединение для игр\n"
            "📺 Стриминг без буферизации\n\n"
            "<blockquote><i>Подключение — 2 минуты. Попробуй, это бесплатно.</i></blockquote>"
        ),
        "buttons": [
            [("🚀 Подключить", "my_proxies")],
            [("💬 Нужна помощь", "support")],
        ]
    },
    {
        "delay": 86400,  # 24 часа
        "text": (
            "⏰ <b>Остался 1 день пробного периода</b>\n\n"
            "Завтра бесплатный доступ закончится.\n\n"
            "Если понравилось — продли подписку.\n"
            "Если не подключался — попробуй сейчас, пока бесплатно.\n\n"
            "💰 Подписка от <b>50₽/мес</b> — дешевле чашки кофе"
        ),
        "buttons": [
            [("⚡ Подключиться", "my_proxies")],
            [("🛒 Купить подписку", "buy_proxy")],
        ]
    },
]

# Добивы после покупки (не подключился)
PURCHASE_FOLLOWUPS = [
    {
        "delay": 180,  # 3 минуты
        "text": (
            "✅ <b>Оплата прошла — подключайся</b>\n\n"
            "Подписка активна, осталось настроить.\n\n"
            "📲 Нажми кнопку ниже — покажем как подключить за 2 минуты.\n\n"
            "<blockquote><i>Чем раньше подключишь — тем больше пользуешься</i></blockquote>"
        ),
        "buttons": [
            [("📲 Подключить сейчас", "my_proxies")],
            [("📖 Инструкция", "followup_howto")],
        ]
    },
    {
        "delay": 7200,  # 2 часа
        "text": (
            "🔔 <b>Напоминание</b>\n\n"
            "Ты оплатил подписку, но пока не подключился.\n\n"
            "Не теряй время — подписка уже активна.\n"
            "Подключение занимает 2 минуты.\n\n"
            "Если что-то не получается — напиши в поддержку, поможем."
        ),
        "buttons": [
            [("⚡ Подключить", "my_proxies")],
            [("💬 Поддержка", "support")],
        ]
    },
]

# Добив для тех у кого заканчивается подписка
EXPIRY_FOLLOWUP = {
    "text": (
        "⚠️ <b>Подписка скоро закончится</b>\n\n"
        "Через пару дней доступ будет отключён.\n\n"
        "Продли сейчас — и не потеряешь соединение.\n\n"
        "💰 От <b>50₽/мес</b> за прокси\n"
        "💰 От <b>99₽/мес</b> за VPN"
    ),
    "buttons": [
        [("🔄 Продлить подписку", "buy_proxy")],
        [("◀️ Главное меню", "main_menu")],
    ]
}

# Инструкция по подключению
HOWTO_VPN = (
    "📖 <b>Как подключить VPN</b>\n\n"
    "<b>iPhone / iPad:</b>\n"
    "1. Скачай <b>V2Box</b> или <b>Streisand</b> из App Store\n"
    "2. В боте нажми «Мои подключения» → VPN\n"
    "3. Скопируй ссылку подписки\n"
    "4. В приложении: + → Подписка → Вставь ссылку\n"
    "5. Нажми «Подключить» ✅\n\n"
    "<b>Android:</b>\n"
    "1. Скачай <b>V2rayNG</b> из Google Play\n"
    "2. В боте нажми «Мои подключения» → VPN\n"
    "3. Скопируй ссылку подписки\n"
    "4. В приложении: + → Импорт из буфера\n"
    "5. Нажми ▶️ для подключения ✅\n\n"
    "<blockquote><i>Занимает 2 минуты. Если не получается — пиши в поддержку.</i></blockquote>"
)

HOWTO_PROXY = (
    "📖 <b>Как подключить прокси</b>\n\n"
    "1. В боте нажми «Мои подключения» → Прокси\n"
    "2. Нажми «Подключить к Telegram»\n"
    "3. Telegram предложит включить прокси — нажми «Подключить»\n"
    "4. Готово ✅\n\n"
    "<blockquote><i>Это буквально 30 секунд.</i></blockquote>"
)


def _build_keyboard(buttons):
    """Собрать клавиатуру из списка кнопок"""
    keyboard = []
    for row in buttons:
        keyboard.append([InlineKeyboardButton(text, callback_data=cb) for text, cb in row])
    return InlineKeyboardMarkup(keyboard)


async def schedule_followups(app: Application, user_id: int, followup_type: str = "trial"):
    """Запланировать цепочку добивов для пользователя"""
    followups = TRIAL_FOLLOWUPS if followup_type == "trial" else PURCHASE_FOLLOWUPS

    for i, fu in enumerate(followups):
        asyncio.get_event_loop().call_later(
            fu["delay"],
            lambda idx=i, uid=user_id, ft=followup_type: asyncio.ensure_future(
                _send_followup(app, uid, ft, idx)
            )
        )
    logger.info(f"Scheduled {len(followups)} {followup_type} followups for user {user_id}")


async def _send_followup(app: Application, user_id: int, followup_type: str, index: int):
    """Отправить конкретный добив"""
    try:
        followups = TRIAL_FOLLOWUPS if followup_type == "trial" else PURCHASE_FOLLOWUPS
        if index >= len(followups):
            return

        fu = followups[index]
        keyboard = _build_keyboard(fu["buttons"])

        await app.bot.send_message(
            chat_id=user_id,
            text=fu["text"],
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.info(f"Sent {followup_type} followup #{index} to user {user_id}")
    except Exception as e:
        logger.error(f"Failed to send followup to {user_id}: {e}")


async def followup_howto_handler(update, context):
    """Обработчик кнопки 'Как подключить'"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # Определяем тип — есть ли VPN ключи
    vpn_keys = db.get_user_vpn_keys(user_id)
    proxies = db.get_user_proxies(user_id)
    has_vpn = any(p.get('service_type') == 'vpn' for p in proxies) or len(vpn_keys) > 0
    has_proxy = any(p.get('service_type', 'proxy') == 'proxy' for p in proxies)

    if has_vpn and has_proxy:
        text = HOWTO_VPN + "\n\n" + HOWTO_PROXY
    elif has_vpn:
        text = HOWTO_VPN
    else:
        text = HOWTO_PROXY

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 Мои подключения", callback_data="my_proxies")],
        [InlineKeyboardButton("💬 Поддержка", callback_data="support")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu")],
    ])

    try:
        await query.message.edit_text(
            text=text, reply_markup=keyboard, parse_mode="HTML"
        )
    except Exception:
        await query.message.reply_text(
            text=text, reply_markup=keyboard, parse_mode="HTML"
        )
