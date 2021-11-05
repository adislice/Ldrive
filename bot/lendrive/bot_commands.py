import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from telegram.utils import helpers

import bot.lendrive.utils as lenutils
from bot.lendrive.ldrive import Lendrive
from bot.log import LOGGER
from bot.config import PARSE_MODE


ANIME_TITLE, SEARCH_RESULT, ANIME_DETAILS, SHOW_SINOPSIS, GET_EPISODE = range(5)

current_sinopsis = {}

"""Bot command handler"""
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Bot is running...")

def search_anime(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    search_query = update.message.text.split(" ", 1)[1]
    LOGGER.info("Search query : " + search_query)
    msg = update.effective_message.reply_text(f"🔎 Mencari <code>{search_query}</code>... ", quote=True, parse_mode=PARSE_MODE)
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
    msg.edit_text(f"🔎 Hasil pencarian <code>{search_query}</code> :", reply_markup=InlineKeyboardMarkup(kb), parse_mode=PARSE_MODE)

def anime_info(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query_data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    # Check user
    if user_id != query_data['user_id']:
        query.answer("Who are you?! ")
        return
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
    reply_text += helpers.mention_html(user_id, '​')
    reply_text += "<b>"+ anime_result['anime_title'] + "</b>" + '\n\n'
    reply_text += anime_result['anime_details']
    rating = lenutils.get_rating(anime_result['anime_rating'])
    reply_text += rating+"\n"
    reply_text += f"<b>Genres:</b> {anime_result['anime_genres']}\n"
    anime_sinopsis = f"<b>Sinopsis {anime_result['anime_title']}</b>\n\n" + anime_result['anime_sinopsis']
    anime_url = anime_result['anime_url']
    anime_thumb_url = anime_result['anime_thumbnail_url']
    LOGGER.info(anime_thumb_url)
    gen_id = uuid.uuid4().hex[:8]
    current_sinopsis[gen_id] = anime_sinopsis
    bot = context.bot
    url = helpers.create_deep_linked_url(bot.username, 'show_' + gen_id)
    # Button Lihat sinopsis
    kb_btn = []
    kb_btn.append([InlineKeyboardButton('Lihat Sinopsis', url=url)])
    # Button Episodes
    episodes_dict = anime_result['anime_episodes']
    btn_episodes = []
    for key,val in episodes_dict.items():
        ep_num = val['ep_num']
        ep_url = val['ep_link']
        cb_data = {
            'user_id': user_id,
            'chat_id': chat_id,
            'type': GET_EPISODE,
            'data': {
                'anime_title': anime_result['anime_title'],
                'ep_num': ep_num,
                'ep_url': ep_url
            }
        }
        btn_episodes.append(InlineKeyboardButton(text=str(ep_num), callback_data=cb_data))
    kb_layout = lenutils.create_pages(btn_episodes)
    kb = kb_btn + kb_layout[1]
    # Delete message then send the new one with photo and caption
    reply_msg_id = query.message.reply_to_message.message_id
    kb_markup = InlineKeyboardMarkup(kb)
    query.message.delete()
    query.bot.send_photo(chat_id=chat_id, photo=anime_thumb_url,
            caption=reply_text, reply_markup=kb_markup, 
            reply_to_message_id=reply_msg_id ,parse_mode=PARSE_MODE)

def show_sinopsis(update: Update, context: CallbackContext):
    cmd_args = context.args
    show_arg = cmd_args[0]
    sinopsis_id = show_arg.split('_')[1]
    anime_sinopsis = current_sinopsis[sinopsis_id]
    update.message.reply_text(anime_sinopsis, parse_mode='HTML')

def get_episode(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query_data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    comm_data = query_data['data']
    anime_title = comm_data['anime_title']
    ep_num = comm_data['ep_num']
    ep_url = comm_data['ep_url']
    query.answer("Mengambil link download...")
    LOGGER.info(f"Processing {anime_title} ep {ep_num}")
    lendrive = Lendrive()
    ep_result = lendrive.parse_episode(ep_url)
    post_dl_link = lenutils.dl_links_to_post(ep_result)
    post_dl_link += helpers.mention_html(user_id,'​')
    episode_thumb = ep_result['thumbnail']
    LOGGER.info("Episode thumb : " + str(episode_thumb))
    msg_id = query.message.message_id
    if episode_thumb is None:
        context.bot.send_message(chat_id=chat_id, text=post_dl_link, 
            reply_to_message_id=msg_id, parse_mode=PARSE_MODE
        )
    else:
        context.bot.send_photo(chat_id=chat_id, photo=episode_thumb, caption=post_dl_link,
            reply_to_message_id=msg_id, parse_mode=PARSE_MODE
        )

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
    LOGGER.info(f"Received query : {str(comm_type)}")
    # INFO
    if comm_type == ANIME_TITLE:
        anime_info(update, context)
    elif comm_type == SHOW_SINOPSIS:
        show_sinopsis(update, context)
    elif comm_type == GET_EPISODE:
        get_episode(update, context)


def is_anime_title(callback_data):
    if callback_data['type'] == ANIME_TITLE:
        return True
    else:
        return False