import json
import os
import threading
from socketserver import ThreadingMixIn, UnixStreamServer, BaseRequestHandler
from typing import TextIO

from ._notification import Urgency, Notification
from ._queue import NotificationQueue
from ._static import ROFICATION_UNIX_SOCK


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    def start(self) -> threading.Thread:
        thread = threading.Thread(target=self.serve_forever)
        thread.setDaemon(True)
        thread.start()
        return thread


class RoficationRequestHandler(BaseRequestHandler):
    def count(self, fp: TextIO) -> None:
        with self.server.queue.lock:
            crit = 0
            for n in self.server.queue:
                if n.urgency == Urgency.CRITICAL:
                    crit += 1
            fp.write(f'{len(self.server.queue)},{crit}')
            fp.flush()

    def delete(self, nid: int) -> None:
        with self.server.queue.lock:
            self.server.queue.remove(nid)

    def delete_multi(self, ids: str) -> None:
        with self.server.queue.lock:
            to_remove = [int(i) for i in ids.split(',')]
            self.server.queue.remove_all(to_remove)

    def delete_all(self, application: str) -> None:
        with self.server.queue.lock:
            to_remove = [n.id for n in self.server.queue
                         if n.application == application]
            self.server.queue.remove_all(to_remove)

    def list(self, fp: TextIO) -> None:
        with self.server.queue.lock:
            json.dump(list(self.server.queue), fp, default=Notification.asdict)

    def see(self, nid: int) -> None:
        with self.server.queue.lock:
            self.server.queue.see(nid)

    def handle(self) -> None:
        with self.server.queue.lock:
            self.server.queue.cleanup()

        with self.request.makefile(mode='rw', encoding='utf-8') as fp:
            cmd, *args = fp.readline().strip().split(':')
            if cmd == 'num':
                # get number of notifications
                self.count(fp)
            elif cmd == 'del':
                # dismiss an item.
                self.delete(nid=int(args[0]))
            elif cmd == 'delm':
                # dismiss list of notifications.
                self.delete_multi(ids=args[0])
            elif cmd == 'dela':
                # dismiss all items from an application.
                self.delete_all(application=args[0])
            elif cmd == 'list':
                # getting a listing.
                self.list(fp)
            elif cmd == 'see':
                # see an item, set the urgency to normal and activate
                self.see(nid=int(args[0]))


class RoficationServer(ThreadedUnixStreamServer):
    def __init__(self, queue: NotificationQueue, server_address: str = ROFICATION_UNIX_SOCK) -> None:
        # pre-start cleanup
        if os.path.exists(server_address):
            os.remove(server_address)
        super().__init__(server_address, RoficationRequestHandler)
        self.queue: NotificationQueue = queue

    def __exit__(self, *args) -> None:
        super().__exit__(*args)
        # removes the UNIX socket after use
        os.remove(self.server_address)
