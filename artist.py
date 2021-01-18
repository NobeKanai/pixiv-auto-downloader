import logging
from typing import List
from pixivapi.client import Client
from pixivapi.enums import Size
from pathlib import Path

from pixivapi.models import Illustration


class Artist:
    """
    Interface
        download(): List[Path]
    """
    def __init__(self,
                 artist_id: str,
                 basedir: str,
                 client: Client,
                 subdir: str = None) -> None:
        self.artist_id = artist_id
        self.basedir = basedir
        self.subdir = subdir
        self.client = client

        self.pic_list = []  # store recent pics for futher usage

    def _download_all(self, directory):
        """ download all pics which never exists in basepath """
        pass

    def _check_exists(self, illust: Illustration, directory: Path) -> bool:
        for p in directory.iterdir():
            if p.match(str(illust.id) + '*'):
                return True

        return False

    def download(self) -> List[Path]:
        """ download start fetch recently updated arts from artist.
        for first time running, it will fetch all pics and compare to local folder to find the difference
        """
        # pad subfolder
        if not self.subdir:
            user = self.client.fetch_user(self.artist_id)
            self.subdir = user.name

        # basepath
        directory = Path(self.basedir) / self.subdir
        Path.mkdir(directory, parents=True, exist_ok=True)

        paths = []

        response = self.client.fetch_user_illustrations(self.artist_id)
        for illust in response['illustrations']:
            if illust.id in self.pic_list:
                continue

            if not self._check_exists(illust, directory):
                illust.download(directory=directory, size=Size.ORIGINAL)
                # add to path
                paths.append([
                    i for i in directory.iterdir()
                    if i.match(str(illust.id) + '*')
                ][0])
            else:
                logging.info(
                    f"[{self.subdir}]: art <ID:{illust.id}> exists, jumped!")

            # update pic list
            self.pic_list.append(illust.id)
            if (length := len(self.pic_list)) > 30:
                self.pic_list = self.pic_list[length - 30:]

        return paths