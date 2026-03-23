"""Inline клавиатуры бота"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List
from core.config import PERIODS


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("🛒 Приобрести", callback_data='buy_proxy')],
        [
            InlineKeyboardButton("👤 Профиль", callback_data='profile'),
            InlineKeyboardButton("💬 Поддержка", callback_data='support')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def service_type_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Выбор типа сервиса: Прокси или VPN"""
    if is_admin:
        keyboard = [
            [
                InlineKeyboardButton("📱 Прокси", callback_data='buy_service_proxy'),
                InlineKeyboardButton("🌐 VPN", callback_data='buy_service_vpn')
            ],
            [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("📱 Прокси", callback_data='buy_service_proxy'),
                InlineKeyboardButton("🔴 VPN", callback_data='vpn_unavailable')
            ],
            [InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]
        ]
    return InlineKeyboardMarkup(keyboard)


def back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')]])


def periods_keyboard() -> InlineKeyboardMarkup:
    """Выбор периода с ценами для ПРОКСИ (50₽/месяц)"""
    keyboard = []
    periods_list = list(PERIODS.items())
    price_per_day = 50.0 / 30

    if not periods_list:
        keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
        return InlineKeyboardMarkup(keyboard)

    # Первая кнопка — длинная
    period_days, period_name = periods_list[0]
    price = price_per_day * int(period_days)
    keyboard.append([InlineKeyboardButton(
        f"{period_name} - {price:.0f}₽", callback_data=f'buy_period_{period_days}'
    )])

    # Средние — по 2 в ряд
    middle = periods_list[1:-1] if len(periods_list) > 2 else periods_list[1:]
    for i in range(0, len(middle), 2):
        row = []
        for j in range(2):
            if i + j < len(middle):
                pd, pn = middle[i + j]
                p = price_per_day * int(pd)
                row.append(InlineKeyboardButton(f"{pn} - {p:.0f}₽", callback_data=f'buy_period_{pd}'))
        keyboard.append(row)

    # Последняя — длинная
    if len(periods_list) > 1:
        period_days, period_name = periods_list[-1]
        price = price_per_day * int(period_days)
        keyboard.append([InlineKeyboardButton(
            f"{period_name} - {price:.0f}₽", callback_data=f'buy_period_{period_days}'
        )])

    keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)


def vpn_periods_keyboard() -> InlineKeyboardMarkup:
    """Выбор периода с ценами для VPN (99₽/месяц)"""
    keyboard = []
    periods_list = list(PERIODS.items())
    price_per_day = 99.0 / 30

    if not periods_list:
        keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
        return InlineKeyboardMarkup(keyboard)

    period_days, period_name = periods_list[0]
    price = price_per_day * int(period_days)
    keyboard.append([InlineKeyboardButton(
        f"{period_name} - {price:.0f}₽", callback_data=f'buy_period_{period_days}'
    )])

    middle = periods_list[1:-1] if len(periods_list) > 2 else periods_list[1:]
    for i in range(0, len(middle), 2):
        row = []
        for j in range(2):
            if i + j < len(middle):
                pd, pn = middle[i + j]
                p = price_per_day * int(pd)
                row.append(InlineKeyboardButton(f"{pn} - {p:.0f}₽", callback_data=f'buy_period_{pd}'))
        keyboard.append(row)

    if len(periods_list) > 1:
        period_days, period_name = periods_list[-1]
        price = price_per_day * int(period_days)
        keyboard.append([InlineKeyboardButton(
            f"{period_name} - {price:.0f}₽", callback_data=f'buy_period_{period_days}'
        )])

    keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)


def confirm_order_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение заказа"""
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить заказ", callback_data='buy_confirm')],
        [InlineKeyboardButton("❌ Отменить", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


def pagination_keyboard(current_page: int, total_pages: int, prefix: str) -> List[InlineKeyboardButton]:
    """Кнопки пагинации"""
    buttons = []
    if current_page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'{prefix}_page_{current_page-1}'))
    if current_page < total_pages - 1:
        buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f'{prefix}_page_{current_page+1}'))
    return buttons
