import os
import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.utils import helpers
from dotenv import load_dotenv

from ldrive import Lendrive
from log import LOGGER


ANIME_TITLE, SEARCH_RESULT, ANIME_DETAILS, SHOW_SINOPSIS = range(4)

current_sinopsis = {}

"""Load config"""
load_dotenv('config.env')

def getEnv(env:str):
    return os.environ[env]

try:
    BOT_TOKEN = getEnv('BOT_TOKEN')
    PARSE_MODE = getEnv('PARSE_MODE')
except KeyError:
    LOGGER.error("One or more environment variable are not set! Exiting...")
    exit(1)

"""Bot command handler"""
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Bot is running...")

def search_anime(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    search_query = update.message.text.split(" ", 1)[1]
    LOGGER.info("User "+str(user_id)+" in chat "+str(chat_id)+" , Search query : " + search_query)
    lendrive = Lendrive()
    anime_search = lendrive.search(search_query)
    search_status = anime_search['status']
    search_result = anime_search['result']
    kb = []
    for key,ani in search_result.items():
        cb_data = {
            'user_id': user_id,
            'chat_id': chat_id,
            'type': ANIME_TITLE,
            'data': {
                'title': ani['title'],
                'url': ani['url']
            }
        }
        kb.append([InlineKeyboardButton(ani['title'], callback_data=cb_data)])
    update.effective_message.reply_text(f"Hasil pencarian {search_query} :", reply_markup=InlineKeyboardMarkup(kb))

def anime_info(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query_data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    comm_data = query_data['data']
    anime_title = comm_data['title']
    anime_url = comm_data['url']
    lendrive = Lendrive()
    anime_parsed = lendrive.parse_anime_info(anime_url)
    if not anime_parsed['status']:
        query.message.edit_text("Error")
        return
    anime_result = anime_parsed['result']
    reply_text = ""
    reply_text += "<b>"+ anime_result['anime_title'] + "</b>" + '\n\n'
    reply_text += anime_result['anime_details']
    reply_text += anime_result['anime_rating'] + "⭐" 
    anime_sinopsis = f"<b>Sinopsis {anime_result['anime_title']}</b>\n\n" + anime_result['anime_sinopsis']
    anime_url = anime_result['anime_url']
    gen_id = uuid.uuid4().hex[:8]
    current_sinopsis[gen_id] = anime_sinopsis
    bot = context.bot
    url = helpers.create_deep_linked_url(bot.username, 'show=' + gen_id)
    kb = []
    kb.append([InlineKeyboardButton('Lihat Sinopsis', url=url)])
    query.edit_message_text(reply_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='HTML')

def show_sinopsis(update: Update, context: CallbackContext):
    cmd_args = context.args
    show_arg = cmd_args[0]
    sinopsis_id = show_arg.split('=')[1]
    anime_sinopsis = current_sinopsis[sinopsis_id]
    update.message.reply_text(anime_sinopsis, parse_mode='HTML')

def handle_invalid_button(update: Update, context: CallbackContext) -> None:
    """Informs the user that the button is no longer available."""
    update.callback_query.answer()
    update.effective_message.edit_text(
        'Sorry, I could not process this button click 😕 Please send /start to get a new keyboard.'
    )

def process_callback(update: Update, context: CallbackContext) -> None:
    """Informs the user that the button is no longer available."""
    query = update.callback_query
    query_data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    comm_type = query_data['type']
    LOGGER.info(f"Received query from {query_data['user_id']}, type {str(comm_type)}")
    if comm_type == ANIME_TITLE:
        anime_info(update, context)
    elif comm_type == SHOW_SINOPSIS:
        show_sinopsis(update, context)

    # update.effective_message.reply_text(f"Type : {str(query_data['type'])}")

def is_anime_title(callback_data):
    if callback_data['type'] == ANIME_TITLE:
        return True
    else:
        return False