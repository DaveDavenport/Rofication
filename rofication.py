import os
import socket
import threading

import jsonpickle

from notification import Urgency


class Rofication(threading.Thread):

    def __init__(self, queue):
        super().__init__()
        self.socket_path = "/tmp/rofi_notification_daemon"
        self.nq = queue
        self.event = threading.Event()

    """
        Communication command.
    """

    def communication_command_send_list(self, connection):
        with self.nq.lock:
            for notification in self.nq.queue:
                connection.send(bytes(jsonpickle.encode(notification), 'utf-8'))
                connection.send(b'\n')

    def communication_command_delete(self, nid):
        with self.nq.lock:
            self.nq.remove(nid)

    def communication_command_delete_apps(self, application):
        with self.nq.lock:
            to_remove = [n.id for n in self.nq.queue
                         if n.application == application]
            self.nq.remove_all(to_remove)

    def communication_command_saw(self, nid):
        with self.nq.lock:
            self.nq.see(nid)

    def communication_command_num(self, connection):
        with self.nq.lock:
            urgent = 0
            for n in self.nq.queue:
                if n.urgency == Urgency.CRITICAL:
                    n += 1
            cmd = "{:d}\n{:d}".format(len(self.nq.queue), urgent)
            connection.send(bytes(cmd, 'utf-8'))

    def run(self):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(self.socket_path)
            server.listen(1)
            server.settimeout(1)
        except OSError as e:
            print("Failed to open socket: " + str(e))
            exit(1)
        while True:
            try:
                connection, client_address = server.accept()
                self.nq.cleanup()
                try:
                    data = connection.recv(1024).decode('utf-8')
                    command = data.split(':')[0]

                    # Get number of notifications
                    if command == "num":
                        self.communication_command_num(connection)
                    # Getting a listing.
                    elif command == "list":
                        self.communication_command_send_list(connection)
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
                finally:
                    # Clean up the connection
                    connection.close()
            except:
                if self.event.is_set():
                    break

        server.close()
        os.unlink("/tmp/rofi_notification_daemon")
