"""Главный файл запуска бота"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config import BOT_TOKEN
from handlers import (
    start_handler,
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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def setup_handlers(application: Application) -> None:
    """Регистрация всех обработчиков"""
    
    # Команды
    application.add_handler(CommandHandler("start", start_handler))
    
    # Callback обработчики
    application.add_handler(CallbackQueryHandler(start_handler, pattern='^main_menu$'))
    application.add_handler(CallbackQueryHandler(balance_handler, pattern='^balance$'))
    application.add_handler(CallbackQueryHandler(my_proxies_handler, pattern='^my_proxies$'))
    application.add_handler(CallbackQueryHandler(view_proxy_handler, pattern='^view_proxy$'))
    application.add_handler(CallbackQueryHandler(view_vpn_handler, pattern='^view_vpn$'))
    application.add_handler(CallbackQueryHandler(buy_proxy_handler, pattern='^buy_proxy$'))
    application.add_handler(CallbackQueryHandler(help_handler, pattern='^help$'))
    application.add_handler(CallbackQueryHandler(profile_handler, pattern='^profile$'))
    application.add_handler(CallbackQueryHandler(support_handler, pattern='^support$'))
    
    # Общий callback обработчик для процесса покупки
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))


def main() -> None:
    """Запуск бота"""
    logger.info("Запуск Proxylin Bot...")
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрация обработчиков
    setup_handlers(application)
    
    logger.info("Бот успешно запущен!")
    
    # Запуск polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
