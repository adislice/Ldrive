from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, InvalidCallbackData, Filters
from log import LOGGER
from bot_commands import show_sinopsis, start, handle_invalid_button, process_callback, search_anime, is_anime_title

def main() -> None:
    updater = Updater(token=BOT_TOKEN, use_context=True, arbitrary_callback_data=True)
    updater.dispatcher.add_handler(
        CommandHandler("start", show_sinopsis, Filters.regex('show'))
    )
    
    updater.dispatcher.add_handler(CommandHandler('lendrive', search_anime))
    updater.dispatcher.add_handler(
        CallbackQueryHandler(handle_invalid_button, pattern=InvalidCallbackData)
    )
    updater.dispatcher.add_handler(CallbackQueryHandler(process_callback))

    updater.dispatcher.add_handler(CommandHandler('start', start))
    

    updater.start_polling()
    LOGGER.info("BOT STARTED")
    updater.idle()

if __name__ == '__main__':
    main()
