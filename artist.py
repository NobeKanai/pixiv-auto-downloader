import logging
from typing import List
from pixivapi.client import Client
from pixivapi.enums import Size
from pathlib import Path
from requests.exceptions import ProxyError


class Artist:
    """
    Interface
        download(): List[Path]
    """
    def __init__(self,
                 artist_id: str,
                 basedir: str,
                 client: Client,
                 subdir: str = None,
                 ignored_tags: List[str] = []) -> None:
        self.artist_id = artist_id
        self.basedir = basedir
        self.subdir = subdir
        self.client = client
        self.ignored_tags = set(ignored_tags)

        self.pic_list = []  # store recent pics for futher usage

    def download(self) -> List[Path]:
        """ download start fetch recently updated arts from artist.
        for first time running, it will fetch all pics and compare
        to local folder to find the difference
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

        try:
            response = self.client.fetch_user_illustrations(self.artist_id)
            for illust in response['illustrations']:
                # if exists in directory, skip
                if self._exists(illust.id, directory):
                    logging.debug("Artist {} ID {} skipped".format(
                        self.subdir,
                        illust.id,
                    ))
                    continue

                # if one of tags in ignored tags, skip
                for tag in illust.tags:
                    if tag['name'] in self.ignored_tags:
                        logging.debug(
                            "Artist {} ID {} includes tag '{}', skipped".
                            format(
                                self.subdir,
                                self.artist_id,
                                tag['name'],
                            ))
                        continue

                illust.download(directory=directory, size=Size.ORIGINAL)
                # add to path
                if illust.image_urls[Size.ORIGINAL]:
                    suffix = illust.image_urls[Size.ORIGINAL].split('.')[-1]
                    paths.insert(0,
                                 directory / (str(illust.id) + '.' + suffix))
                else:
                    paths.insert(0, directory / str(illust.id))

                # update pic list
                self._update_pic_list(illust.id)
        except ProxyError as e:
            logging.error(
                f"ProxyError when fetch user '{self.subdir}' illustrations:{e}"
            )

        return paths

    def _exists(self, illust_id: int, directory: Path) -> bool:
        if illust_id in self.pic_list:
            return True

        if list(directory.glob(str(illust_id) + '*')):
            return True

        return False

    def _init_pic_list(self, dirpath: Path):
        paths = []

        for p in dirpath.iterdir():
            if p.is_file():
                paths.append(int(p.name.split('.')[0]))
            else:
                paths.append(int(p.name))

        # sort by desc
        paths.sort(reverse=True)

        if len(paths) > 30:
            paths = paths[:30]

        self.pic_list = paths

    def _update_pic_list(self, pid: int):
        pl = self.pic_list

        pl.insert(0, pid)

        if len(pl) > 30:
            pl.pop()

        i = 0  # bubble sort
        while i < len(pl) - 1 and pl[i] < pl[i + 1]:
            pl[i], pl[i + 1] = pl[i + 1], pl[i]  # exchange value
            i += 1
