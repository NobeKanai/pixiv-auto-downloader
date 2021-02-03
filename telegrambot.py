import logging
from pathlib import Path
import time
from typing import List
import telegram


class TelegramBot:
    """
    Interface:
        push_pics(files: List[Path])
        push_msg(msg: str)
    """
    def __init__(self, token, chat_id) -> None:
        self._bot = telegram.Bot(token=token)
        self.chat_id = chat_id

    def push_pics(self, files: List[Path]):
        # construct all real paths
        real_paths = []
        for file in files:
            if file.is_file():
                real_paths.append(file)
            elif file.is_dir():
                real_paths.append(sorted([f for f in file.iterdir()]))
            else:
                logging.warn(
                    "what the fuck happened with this holly shit file: ", file)

        for path in real_paths:

            def f():
                if isinstance(path, list):
                    self._push_photos(path)
                else:
                    self._push_photo(path)

            self._limit_do(f)

    def push_msg(self, msg: str):
        def f():
            self._bot.send_message(self.chat_id, msg)

        self._limit_do(f)

    def _push_photos(self, paths):
        try:
            tmp = 0
            media_list = []
            for p in paths:
                if tmp >= 10:
                    self._bot.send_media_group(self.chat_id, media_list)

                    tmp = 0
                    media_list.clear()

                media_list.append(telegram.InputMediaPhoto(open(p, "rb")))
                tmp += 1

            self._bot.send_media_group(self.chat_id, media_list)

        except telegram.error.BadRequest as e:
            logging.warning("bad requeset with error message: " + e.message)
            for p in paths:
                self._bot.send_document(self.chat_id, open(p, 'rb'))

    def _push_photo(self, path):
        try:
            self._bot.send_photo(self.chat_id, open(path, 'rb'))
        except telegram.error.BadRequest as e:
            logging.warning("bad requeset with error message: " + e.message)
            self._bot.send_document(self.chat_id, open(path, 'rb'))

    def _limit_do(self, f):
        try_times = 0
        while True:
            if try_times >= 3:
                logging.warn("too much retry times... skipped")
                break

            try:
                f()
            except telegram.error.RetryAfter as e:
                logging.warn("telegram server: retry after {} seconds".format(
                    e.retry_after))
                time.sleep(e.retry_after)

                try_times += 1
                continue
            break
