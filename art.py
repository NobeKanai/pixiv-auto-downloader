from pixivapi import Illustration


class Art:
    def __init__(self, author: str, path, illust: Illustration) -> None:
        self.author = author
        self.path = path
        self.illust = illust

    def format(self) -> str:
        """
        format formats an art to user-friendly format(markdown)
        """
        return "https://www.pixiv.net/artworks/{}\n#{} {}".format(
            self.illust.id, self.author, self.illust.title)
