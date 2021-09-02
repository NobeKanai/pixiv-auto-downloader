import logging
import time
from typing import List

import telegram

from art import Art

DEFAULT_TIMEOUT = 60


class TelegramBot:
    """
    Interface:
        push_pics(arts: List[Art])
        push_msg(msg: str)
    """
    def __init__(self, token, chat_id) -> None:
        self._bot = telegram.Bot(token=token)
        self.chat_id = chat_id

    def push_pics(self, arts: List[Art]):
        # construct all real paths
        for art in arts:
            if art.path.is_dir():
                art.path = sorted([f for f in art.path.iterdir()])

        for art in arts:

            def f():
                if isinstance(art.path, list):
                    self._push_photos(art.path, art.format())
                else:
                    self._push_photo(art.path, art.format())

            self._limit_do(f)

    def push_msg(self, msg: str):
        def f():
            self._bot.send_message(self.chat_id, msg, timeout=DEFAULT_TIMEOUT)

        self._limit_do(f)

    def _push_photos(self, paths, caption):
        try:
            tmp = 0
            media_list = []
            for p in paths:
                if tmp >= 10:
                    self._bot.send_media_group(self.chat_id,
                                               media_list,
                                               timeout=DEFAULT_TIMEOUT)

                    tmp = 0
                    media_list.clear()

                # set caption property only for the first element of an array
                if len(media_list) == 0:
                    media_list.append(
                        telegram.InputMediaPhoto(open(p, "rb"),
                                                 caption=caption))
                else:
                    media_list.append(telegram.InputMediaPhoto(open(p, "rb")))
                tmp += 1

            self._bot.send_media_group(self.chat_id,
                                       media_list,
                                       timeout=DEFAULT_TIMEOUT)

        except telegram.error.BadRequest as e:
            logging.warning("bad requeset with error message: " + e.message)
            for p in paths:
                self._bot.send_document(self.chat_id, open(p, 'rb'))

    def _push_photo(self, path, caption):
        try:
            self._bot.send_photo(self.chat_id,
                                 open(path, 'rb'),
                                 caption=caption,
                                 timeout=DEFAULT_TIMEOUT)
        except telegram.error.BadRequest as e:
            logging.warning("bad requeset with error message: " + e.message)
            self._bot.send_document(self.chat_id,
                                    open(path, 'rb'),
                                    caption=caption,
                                    timeout=DEFAULT_TIMEOUT)

    def _limit_do(self, f):
        trying_times = 0
        while True:
            if trying_times >= 3:
                logging.warning("too much retry times... skipped")
                break

            try:
                f()
            except telegram.error.RetryAfter as e:
                logging.warning(
                    "telegram server: retry after {} seconds".format(
                        e.retry_after))
                time.sleep(e.retry_after)

                trying_times += 1
                continue

            except telegram.error.TimedOut:
                logging.warning("telegram server time out: retry after 20s.")
                time.sleep(20)

                trying_times += 1
                continue
            break
