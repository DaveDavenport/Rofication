import io
from typing import TextIO

ROFICATION_UNIX_SOCK = '/tmp/rofi_notification_daemon'


class NullTextIO(io.TextIOBase, TextIO):
    def write(self, s: str) -> int:
        return 0


nullio: TextIO = NullTextIO()
