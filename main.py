from telegrambot import TelegramBot
from typing import List
from artist import Artist
from pixivapi import Client, errors
from pathlib import Path
import logging
import yaml
import time
import os

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.environ.get("LOG_LEVEL", "INFO"))

CONFIG_FILE = Path("config.yaml")
assert CONFIG_FILE.exists()


def login(client: Client, username, password):
    try:
        token = open('.token', 'r', encoding='utf-8').read()
        client.authenticate(token)
    except Exception:
        logging.info(
            "try token login failed, use username and password instead...")
        client.login(username, password)

    # save token
    with open('.token', 'w', encoding='utf-8') as f:
        f.write(client.refresh_token)
    logging.info("new token saved to ./.token")


def init():
    # load configuration
    config_text = open(CONFIG_FILE, 'r', encoding='utf-8').read()
    config = yaml.load(config_text, Loader=Loader)

    serivce = config['service']
    basedir = serivce.get('basedir', './images')
    username = serivce['username']
    password = serivce['password']

    # set env. only for test
    if (proxy := serivce.get('proxy')) and not os.environ.get('HTTPS_PROXY'):
        os.environ['HTTP_PROXY'] = proxy
        os.environ['HTTPS_PROXY'] = proxy

    # set client
    client = Client()

    login(client, username, password)

    # get common ignored tags
    ignored_tags = serivce.get('ignored-tags', [])

    # set artists list
    artists: List[Artist] = []
    for user in config['artists']:
        ignored_tags_artist = user.get('ignored-tags', [])
        size = user.get('size', 30)

        a = Artist(
            user['id'],
            basedir,
            client,
            size=size,
            subdir=user.get('subdir', None),
            ignored_tags=ignored_tags + ignored_tags_artist,
        )
        artists.append(a)

    # set bot
    bot_config = config['bot']
    tg_bot = TelegramBot(bot_config['token'], bot_config['chatid'])

    return (artists, client, username, password, tg_bot)


def start():
    artists, client, username, password, tg_bot = init()

    for a in artists:
        arts = None

        try:
            arts = a.download()
        except errors.BadApiResponse:
            logging.warning("download failed. wait for 20 seconds, and retry")
            time.sleep(20)
            login(client, username, password)
            arts = a.download()

        if not arts:
            continue

        try:
            tg_bot.push_pics(arts)
        except Exception as e:
            logging.error(e)


if __name__ == '__main__':
    start()
