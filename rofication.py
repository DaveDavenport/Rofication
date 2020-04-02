import os
import threading
from socketserver import ThreadingMixIn, UnixStreamServer, BaseRequestHandler

import jsonpickle

from notification import NotificationQueue, Urgency


class NotificationHandler(BaseRequestHandler):
    def communication_command_send_list(self) -> None:
        with self.server.not_queue.lock:
            for notification in self.server.not_queue.queue:
                self.request.send(bytes(jsonpickle.encode(notification), 'utf-8'))
                self.request.send(b'\n')

    def communication_command_delete(self, nid: int) -> None:
        with self.server.not_queue.lock:
            self.server.not_queue.remove(nid)

    def communication_command_delete_apps(self, application: str) -> None:
        with self.server.not_queue.lock:
            to_remove = [n.id for n in self.server.not_queue.queue
                         if n.application == application]
            self.server.not_queue.remove_all(to_remove)

    def communication_command_saw(self, nid: int) -> None:
        with self.server.not_queue.lock:
            self.server.not_queue.see(nid)

    def communication_command_num(self) -> None:
        with self.server.not_queue.lock:
            urgent = 0
            for n in self.server.not_queue.queue:
                if n.urgency == Urgency.CRITICAL:
                    urgent += 1
            cmd = "{:d}\n{:d}".format(len(self.server.not_queue.queue), urgent)
            self.request.send(bytes(cmd, 'utf-8'))

    def handle(self) -> None:
        with self.server.not_queue.lock:
            self.server.not_queue.cleanup()

        data = self.request.recv(1024).decode('utf-8').strip()
        command = data.split(':')[0]

        # Get number of notifications
        if command == "num":
            self.communication_command_num()
        # Getting a listing.
        elif command == "list":
            self.communication_command_send_list()
        # Dismiss and item.
        elif command == "del":
            nid = int(data.split(':')[1])
            self.communication_command_delete(nid)
        elif command == "dela":
            application = data.split(':')[1]
            self.communication_command_delete_apps(application)
        # Saw an item, this sets the urgency to normal.
        elif command == "saw":
            nid = int(data.split(':')[1])
            self.communication_command_saw(nid)


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
