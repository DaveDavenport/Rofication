import json
import socket
from typing import TextIO, Sequence

from ._notification import Notification
from ._static import ROFICATION_UNIX_SOCK, nullio


class RoficationClient:
    def __init__(self, out: TextIO = nullio, unix_socket: str = ROFICATION_UNIX_SOCK):
        self._out: TextIO = out
        self._unix_socket: str = unix_socket

    def _client_socket(self) -> socket.socket:
        sck = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sck.connect(self._unix_socket)
        return sck

    def _send(self, command: str, arg: any) -> None:
        with self._client_socket() as sck:
            sck.send(bytes(f'{command}:{arg}\n', encoding='utf-8'))

    def count(self) -> (int, int):
        with self._client_socket() as sck:
            sck.send(b'num\n')
            data = sck.recv(32).decode('utf-8')
            return (int(x) for x in data.split(',', 2))

    def delete(self, nid: int) -> None:
        self._send('del', nid)

    def delete_multi(self, ids: str) -> None:
            self._send('delm', ids)

    def delete_all(self, application: str) -> None:
        self._send('dela', application)

    def list(self) -> Sequence[Notification]:
        with self._client_socket() as sck:
            sck.send(b'list\n')
            with sck.makefile(mode='r', encoding='utf-8') as fp:
                return json.load(fp, object_hook=Notification.make)

    def see(self, nid: int) -> None:
        self._send('see', nid)
