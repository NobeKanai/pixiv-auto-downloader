import logging
from pathlib import Path
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
                real_paths.append([f for f in file.iterdir()])
            else:
                logging.warn(
                    "what the fuck happened with this holly shit file: ", file)

        for path in real_paths:
            if isinstance(path, list):
                self._push_photos(path)
            else:
                self._push_photo(path)

    def push_msg(self, msg: str):
        self._bot.send_message(self.chat_id, msg)

    def _push_photos(self, paths):
        media_list = []
        for p in paths:
            media_list.append(telegram.InputMediaPhoto(open(p, "rb")))
        self._bot.send_media_group(self.chat_id, media_list)

    def _push_photo(self, path):
        self._bot.send_photo(self.chat_id, open(path, 'rb'))
