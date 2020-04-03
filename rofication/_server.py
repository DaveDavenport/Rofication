import json
import os
import threading
from io import TextIOBase
from socketserver import ThreadingMixIn, UnixStreamServer, BaseRequestHandler

from ._notification import Urgency, Notification
from ._queue import NotificationQueue


class NotificationHandler(BaseRequestHandler):
    def communication_command_send_list(self, fp: TextIOBase) -> None:
        with self.server.not_queue.lock:
            json.dump(list(self.server.not_queue), fp, default=Notification.asdict)

    def communication_command_delete(self, nid: int) -> None:
        with self.server.not_queue.lock:
            self.server.not_queue.remove(nid)

    def communication_command_delete_apps(self, application: str) -> None:
        with self.server.not_queue.lock:
            to_remove = [n.id for n in self.server.not_queue
                         if n.application == application]
            self.server.not_queue.remove_all(to_remove)

    def communication_command_saw(self, nid: int) -> None:
        with self.server.not_queue.lock:
            self.server.not_queue.see(nid)

    def communication_command_num(self, fp: TextIOBase) -> None:
        with self.server.not_queue.lock:
            urgent = 0
            for n in self.server.not_queue:
                if n.urgency == Urgency.CRITICAL:
                    urgent += 1
            fp.write("{:d},{:d}".format(len(self.server.not_queue), urgent))
            fp.flush()

    def handle(self) -> None:
        with self.server.not_queue.lock:
            self.server.not_queue.cleanup()

        with self.request.makefile(mode='rw', encoding='utf-8') as fp:
            data = fp.readline().strip()
            cmd, *args = data.split(':')
            # Get number of notifications
            if cmd == "num":
                self.communication_command_num(fp)
            # Getting a listing.
            elif cmd == "list":
                self.communication_command_send_list(fp)
            # Dismiss and item.
            elif cmd == "del":
                self.communication_command_delete(nid=int(args[0]))
            elif cmd == "dela":
                self.communication_command_delete_apps(application=args[0])
            # Saw an item, this sets the urgency to normal.
            elif cmd == "saw":
                self.communication_command_saw(nid=int(args[0]))


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    def start(self) -> threading.Thread:
        thread = threading.Thread(target=self.serve_forever)
        thread.setDaemon(True)
        thread.start()
        return thread


class NotificationServer(ThreadedUnixStreamServer):
    def __init__(self, server_address: str, not_queue: NotificationQueue) -> None:
        # Pre-start cleanup
        if os.path.exists(server_address):
            os.remove(server_address)
        super().__init__(server_address, NotificationHandler)
        self.not_queue: NotificationQueue = not_queue

    def __exit__(self, *args) -> None:
        super().__exit__(*args)
        # removes the UNIX socket after use
        os.remove(self.server_address)
