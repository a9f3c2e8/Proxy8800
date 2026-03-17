"""Главный файл запуска бота"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from core.config import BOT_TOKEN
from handlers import (
    start_handler,
    check_sub_handler,
    balance_handler,
    my_proxies_handler,
    view_proxy_handler,
    view_vpn_handler,
    buy_proxy_handler,
    help_handler,
    profile_handler,
    support_handler,
    callback_handler,
    message_handler
)
from handlers.admin import (
    admin_handler,
    admin_callback_handler,
    admin_message_handler,
    is_admin
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Отключаем лишние логи httpx
logging.getLogger('httpx').setLevel(logging.WARNING)


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Роутер для текстовых сообщений"""
    if is_admin(update.effective_user.id) and context.user_data.get('waiting_for', '').startswith('admin_'):
        await admin_message_handler(update, context)
    elif is_admin(update.effective_user.id) and context.user_data.get('waiting_for') == 'broadcast_message':
        await admin_message_handler(update, context)
    else:
        await message_handler(update, context)


def setup_handlers(application: Application) -> None:
    """Регистрация всех обработчиков"""
    
    # Админ команды
    application.add_handler(CommandHandler("admin", admin_handler))
    
    # Команды
    application.add_handler(CommandHandler("start", start_handler))
    
    # Callback обработчики
    application.add_handler(CallbackQueryHandler(check_sub_handler, pattern='^check_sub$'))
    application.add_handler(CallbackQueryHandler(start_handler, pattern='^main_menu$'))
    application.add_handler(CallbackQueryHandler(balance_handler, pattern='^balance$'))
    application.add_handler(CallbackQueryHandler(my_proxies_handler, pattern='^my_proxies$'))
    application.add_handler(CallbackQueryHandler(view_proxy_handler, pattern='^view_proxy$'))
    application.add_handler(CallbackQueryHandler(view_vpn_handler, pattern='^view_vpn$'))
    application.add_handler(CallbackQueryHandler(buy_proxy_handler, pattern='^buy_proxy$'))
    application.add_handler(CallbackQueryHandler(help_handler, pattern='^help$'))
    application.add_handler(CallbackQueryHandler(profile_handler, pattern='^profile$'))
    application.add_handler(CallbackQueryHandler(support_handler, pattern='^support$'))
    
    # Админ callback обработчики
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern='^admin_'))
    
    # Общий callback обработчик для процесса покупки
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))


def main() -> None:
    """Запуск бота"""
    logger.info("Запуск бота 8800.life...")
    
    # Создание приложения с увеличенными таймаутами
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )
    
    # Регистрация обработчиков
    setup_handlers(application)
    
    logger.info("Бот успешно запущен!")
    
    # Запуск polling с увеличенным таймаутом
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30,
        pool_timeout=30
    )


if __name__ == '__main__':
    main()
