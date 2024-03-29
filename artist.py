import logging
from pathlib import Path
from typing import List

from pixivapi.client import Client
from pixivapi.enums import Size
from pixivapi.models import Illustration
from requests.exceptions import ProxyError, RequestException

from art import Art


class Artist:
    """
    Interface
        download(): List[Art]
    """
    def __init__(self,
                 artist_id: str,
                 basedir: str,
                 client: Client,
                 size: int = 30,
                 subdir: str = None,
                 ignored_tags: List[str] = []) -> None:
        self.artist_id = artist_id
        self.basedir = basedir
        self.subdir = subdir
        self.client = client
        self.size = size
        self.ignored_tags = set(ignored_tags)

        self.pic_list = []  # store recent pics for futher usage

        # private attributes for private methods
        self._initialized = False

    def download(self) -> List[Art]:
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

        # prevent redundant requests
        if len(self.pic_list) >= self.size:
            self._initialized = True

        arts = []  # for return

        try:
            illustrations = self._fetch_user_illustrations()
            for illust in illustrations:
                # if exists in directory, skip
                if self._exists(illust.id, directory):
                    logging.debug("Artist {} ID {} skipped".format(
                        self.subdir,
                        illust.id,
                    ))
                    continue

                if not self._is_valid(illust):
                    logging.debug("Artist {} ID {} is invalid, skipped".format(
                        self.subdir,
                        self.artist_id,
                    ))

                    self._update_pic_list(illust.id)
                    continue

                try:
                    illust.download(directory=directory, size=Size.ORIGINAL)
                except RequestException as e:
                    logging.error(
                        f"Download illustration '{illust}' error:{e}")
                    continue

                # add to path
                if illust.image_urls[Size.ORIGINAL]:
                    suffix = illust.image_urls[Size.ORIGINAL].split('.')[-1]
                    arts.insert(
                        0,
                        Art(self.subdir,
                            directory / (str(illust.id) + '.' + suffix),
                            illust))
                else:
                    arts.insert(
                        0, Art(self.subdir, directory / str(illust.id),
                               illust))

                # update pic list
                self._update_pic_list(illust.id)
        except ProxyError as e:
            logging.error(
                f"ProxyError when fetch user '{self.subdir}' illustrations:{e}"
            )

        return arts

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

        if len(paths) > self.size:
            paths = paths[:self.size]

        self.pic_list = paths

    def _update_pic_list(self, pid: int):
        pl = self.pic_list

        pl.insert(0, pid)

        if len(pl) > self.size:
            pl.pop()

        i = 0  # bubble sort
        while i < len(pl) - 1 and pl[i] < pl[i + 1]:
            pl[i], pl[i + 1] = pl[i + 1], pl[i]  # exchange value
            i += 1

    def _is_valid(self, illust: Illustration) -> bool:
        for tag in illust.tags:
            if tag['name'] in self.ignored_tags:
                return False
        return True

    def _fetch_user_illustrations(self) -> List[Illustration]:
        illustrations: List[Illustration] = []

        # if not initalized fetching, fetch once
        if self._initialized:
            illustrations = self.client.fetch_user_illustrations(
                self.artist_id)['illustrations']
            if len(illustrations) > self.size:
                return illustrations[:self.size]
            return illustrations

        offset = 0
        while True:
            response = self.client.fetch_user_illustrations(
                self.artist_id,
                offset=offset,
            )

            ils = response['illustrations']

            if len(illustrations) + len(ils) >= self.size:
                ends = self.size - len(illustrations) or None
                illustrations.extend(ils[:ends])
                break

            illustrations.extend(ils)

            offset = response['next']
            if not offset:
                break

        # initialized
        self._initialized = True

        return illustrations
