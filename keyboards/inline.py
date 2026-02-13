"""Inline клавиатуры бота"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple
from core.config import COUNTRIES, PERIODS, PROXY_TYPES, IP_VERSIONS
import random


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню - упрощенная версия"""
    keyboard = [
        [InlineKeyboardButton("🛒 Приобрести", callback_data='buy_proxy')],
        [
            InlineKeyboardButton("👤 Профиль", callback_data='profile'),
            InlineKeyboardButton("💬 Поддержка", callback_data='support')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def service_type_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа сервиса: Прокси или VPN"""
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


def proxy_type_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа прокси - по 2 в ряд"""
    keyboard = [
        [
            InlineKeyboardButton("IPv4 Dedicated", callback_data='buy_type_4_dedicated'),
            InlineKeyboardButton("IPv4 Shared", callback_data='buy_type_4_shared')
        ],
        [
            InlineKeyboardButton("IPv6 Dedicated", callback_data='buy_type_6_dedicated')
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)


def countries_keyboard(page: int = 0, items_per_page: int = 12) -> InlineKeyboardMarkup:
    """Выбор страны - 3 сервера: 1 активный (рандомный) + 2 неактивных"""
    # Получаем список всех стран
    countries_list = list(COUNTRIES.items())
    
    # Выбираем 3 случайных страны
    selected_countries = random.sample(countries_list, min(3, len(countries_list)))
    
    # Первая - активная (ближайший сервер)
    nearest_code, nearest_name = selected_countries[0]
    
    # Остальные - неактивные
    inactive_countries = selected_countries[1:]
    
    keyboard = []
    
    # Активный сервер (ближайший) - длинная кнопка с планетой
    keyboard.append([
        InlineKeyboardButton(
            "🌍 Ближайший", 
            callback_data=f'buy_country_{nearest_code}'
        )
    ])
    
    # Неактивные серверы - 2 кнопки в ряд с красным кругом
    inactive_row = []
    for code, name in inactive_countries:
        inactive_row.append(
            InlineKeyboardButton(
                "🔴 Недоступен", 
                callback_data='server_unavailable'
            )
        )
    keyboard.append(inactive_row)
    
    keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)


def periods_keyboard() -> InlineKeyboardMarkup:
    """Выбор периода с ценами для ПРОКСИ (50₽/месяц)"""
    keyboard = []
    periods_list = list(PERIODS.items())
    
    price_per_day = 50.0 / 30  # Прокси: 50₽ за месяц
    
    if len(periods_list) == 0:
        keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
        return InlineKeyboardMarkup(keyboard)
    
    # Первая кнопка - длинная с ценой
    period_days, period_name = periods_list[0]
    price = price_per_day * int(period_days)
    keyboard.append([InlineKeyboardButton(
        f"{period_name} - {price:.0f}₽", 
        callback_data=f'buy_period_{period_days}'
    )])
    
    # Средние кнопки - по 2 в ряд с ценами
    middle_periods = periods_list[1:-1] if len(periods_list) > 2 else periods_list[1:]
    for i in range(0, len(middle_periods), 2):
        row = []
        for j in range(2):
            if i + j < len(middle_periods):
                period_days, period_name = middle_periods[i + j]
                price = price_per_day * int(period_days)
                row.append(InlineKeyboardButton(
                    f"{period_name} - {price:.0f}₽", 
                    callback_data=f'buy_period_{period_days}'
                ))
        keyboard.append(row)
    
    # Последняя кнопка - длинная с ценой (если есть больше 1 элемента)
    if len(periods_list) > 1:
        period_days, period_name = periods_list[-1]
        price = price_per_day * int(period_days)
        keyboard.append([InlineKeyboardButton(
            f"{period_name} - {price:.0f}₽", 
            callback_data=f'buy_period_{period_days}'
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)


def vpn_periods_keyboard() -> InlineKeyboardMarkup:
    """Выбор периода с ценами для VPN (99₽/месяц)"""
    keyboard = []
    periods_list = list(PERIODS.items())
    
    price_per_day = 99.0 / 30  # VPN: 99₽ за месяц
    
    if len(periods_list) == 0:
        keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data='main_menu')])
        return InlineKeyboardMarkup(keyboard)
    
    # Первая кнопка - длинная с ценой
    period_days, period_name = periods_list[0]
    price = price_per_day * int(period_days)
    keyboard.append([InlineKeyboardButton(
        f"{period_name} - {price:.0f}₽", 
        callback_data=f'buy_period_{period_days}'
    )])
    
    # Средние кнопки - по 2 в ряд с ценами
    middle_periods = periods_list[1:-1] if len(periods_list) > 2 else periods_list[1:]
    for i in range(0, len(middle_periods), 2):
        row = []
        for j in range(2):
            if i + j < len(middle_periods):
                period_days, period_name = middle_periods[i + j]
                price = price_per_day * int(period_days)
                row.append(InlineKeyboardButton(
                    f"{period_name} - {price:.0f}₽", 
                    callback_data=f'buy_period_{period_days}'
                ))
        keyboard.append(row)
    
    # Последняя кнопка - длинная с ценой (если есть больше 1 элемента)
    if len(periods_list) > 1:
        period_days, period_name = periods_list[-1]
        price = price_per_day * int(period_days)
        keyboard.append([InlineKeyboardButton(
            f"{period_name} - {price:.0f}₽", 
            callback_data=f'buy_period_{period_days}'
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
