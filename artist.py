import logging
import os
from typing import List
from pixivapi.client import Client
from pixivapi.enums import Size
from pathlib import Path


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

        # init pic list if not
        if len(self.pic_list) == 0:
            self._init_pic_list(directory)

        paths = []  # for return

        response = self.client.fetch_user_illustrations(self.artist_id)
        for illust in response['illustrations']:
            if illust.id in self.pic_list:
                logging.info("Artist {} ID {} skipped".format(
                    self.subdir, illust.id))
                continue

            illust.download(directory=directory, size=Size.ORIGINAL)
            # add to path
            paths.append([
                i for i in directory.iterdir()
                if i.match(str(illust.id) + '*')
            ][0])

            # update pic list
            self.pic_list.append(illust.id)
            if (length := len(self.pic_list)) > 30:
                self.pic_list = self.pic_list[length - 30:]

        return paths

    def _init_pic_list(self, dirpath: Path):
        paths = sorted(dirpath.iterdir(), key=os.path.getmtime, reverse=True)
        if len(paths) > 30:
            paths = paths[:30]

        for p in paths:
            if p.is_file():
                self.pic_list.insert(0, int(p.name.split('.')[0]))
            else:
                self.pic_list.insert(0, int(p.name))
