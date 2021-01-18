from telegrambot import TelegramBot
from typing import List
from artist import Artist
import yaml, time, os
from pixivapi import Client
import logging

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

if __name__ == "__main__":
    # load configuration
    config_text = open('config.yaml', 'r', encoding='utf-8').read()
    config = yaml.load(config_text, Loader=Loader)

    serivce = config['service']
    basedir = serivce.get('basedir', './images')
    username = serivce['username']
    password = serivce['password']

    # set env
    if proxy := serivce.get('proxy', None):
        os.environ['HTTP_PROXY'] = proxy
        os.environ['HTTPS_PROXY'] = proxy

    # set client
    client = Client()
    try:
        token = serivce.get('token', None)
        if not token:
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

    # set artists list
    artists: List[Artist] = []
    for user in config['artists']:
        a = Artist(user['id'],
                   basedir,
                   client,
                   subdir=user.get('subdir', None))
        artists.append(a)

    # set bot
    bot_config = config['bot']
    tg_bot = TelegramBot(bot_config['token'], bot_config['chatid'])

    interval = config['service'].get('interval', 600)
    logging.info("start program with interval {} seconds".format(interval))

    while True:
        for a in artists:
            paths = a.download()

            if not paths:
                continue

            try:
                tg_bot.push_pics(paths)
                tg_bot.push_msg(
                    "Artist: {} updates {} arts. All Saved.".format(
                        a.subdir, len(paths)))
            except Exception as e:
                logging.error(e)

        time.sleep(interval)
