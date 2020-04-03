import io
import socket
from typing import TextIO

UNIX_SOCKET = '/tmp/rofi_notification_daemon'


def notification_client(server_address: str) -> socket:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(server_address)
    return client


class NullTextIO(io.TextIOBase, TextIO):
    def write(self, s: str) -> int:
        return 0


nullio: TextIO = NullTextIO()
