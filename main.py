from telegrambot import TelegramBot
from typing import List
from artist import Artist
from pixivapi import Client, errors
from watchgod import run_process
from pathlib import Path
import logging
import traceback
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


def start():
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

    interval = config['service'].get('interval', 600)
    logging.info("start program with interval {} seconds".format(interval))

    while True:
        for a in artists:
            paths = None

            try:
                paths = a.download()
            except errors.BadApiResponse:
                traceback.print_exc()
                logging.info("wait for 20 seconds, and retry")
                time.sleep(20)
                login(client, username, password)
                paths = a.download()

            if not paths:
                continue

            try:
                tg_bot.push_pics(paths)
                tg_bot.push_msg("Artist {} updated {} {}. All saved.".format(
                    a.subdir, len(paths),
                    "works" if len(paths) > 1 else "work"))
            except Exception as e:
                logging.error(e)

        time.sleep(interval)


if __name__ == '__main__':
    run_process(CONFIG_FILE, start)
