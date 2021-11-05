import os
from bot.log import LOGGER
from dotenv import load_dotenv

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