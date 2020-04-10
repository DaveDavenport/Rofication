import io
from typing import TextIO

from ._metadata import ROFICATION_VERSION

__version__ = ROFICATION_VERSION

ROFICATION_UNIX_SOCK = '/tmp/rofi_notification_daemon'


class NullTextIO(io.TextIOBase, TextIO):
    def write(self, s: str) -> int:
        return 0


nullio: TextIO = NullTextIO()
