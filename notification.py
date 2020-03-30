import os
import threading
import time
from enum import IntEnum
from warnings import warn

import jsonpickle


class Urgency(IntEnum):
    LOW = 0
    NORMAL = 1
    CRITICAL = 2


class CloseReason(IntEnum):
    EXPIRED = 1
    DISMISSED = 2
    CLOSED = 3
    RESERVED = 4


class Notification:
    def __init__(self):
        self.id = None
        self.deadline = None
        self.summary = None
        self.body = None
        self.application = None
        self.urgency = int(Urgency.NORMAL)
        self.actions = []

    def __str__(self):
        return jsonpickle.encode(self)


# TODO: make it iterable
class NotificationQueue:
    def __init__(self, queue=None, last_id=1):
        self.lock = threading.RLock()
        self.queue = [] if queue is None else queue
        self.last_id = last_id
        self.allowed_to_expire = []
        self.single_notification_apps = ["VLC media player"]
        self.observers = []

    def save(self, filename):
        print("Saving notification queue")
        try:
            with open(filename, 'w') as f:
                f.write(jsonpickle.encode(self.queue))
        except:
            warn("Failed to store notification queue")

    def see(self, nid):
        with self.lock:
            for notification in self.queue:
                if notification.id == nid:
                    notification.urgency = int(Urgency.NORMAL)
                    for observer in self.observers:
                        observer.activate(notification)
                    break
        warn("Unable to find notification {:d}", nid)

    def remove(self, nid):
        with self.lock:
            for notification in self.queue:
                if notification.id == nid:
                    print("Removing: {:d}".format(nid))
                    self.queue.remove(notification)
                    break
        warn("Unable to find notification {:d}", nid)

    def remove_all(self, nids):
        with self.lock:
            to_remove = [n for n in self.queue if n.id in nids]
            for notification in to_remove:
                print("Removing: {:d}".format(notification.id))
                self.queue.remove(notification)

    def put(self, notification):
        with self.lock:
            if notification.application in self.single_notification_apps:
                to_replace = next((n for n in self.queue
                                   if n.application == notification.application), None)
            else:
                # cannot have two notifications with the same ID
                to_replace = next((n for n in self.queue if n.id == notification.id), None)
            if to_replace:
                print("Replacing {:d}", to_replace.id)
                self.queue.remove(to_replace)
            else:
                # new notification, increase progressive ID
                notification.id = self.last_id
                self.last_id += 1
            print("Adding: {:d}".format(notification.id))
            self.queue.append(notification)

    def cleanup(self):
        with self.lock:
            now = time.time()
            to_remove = [n.id for n in self.queue
                         if n.deadline and n.deadline < now
                         and n.application in self.allowed_to_expire]
            if to_remove:
                print("Expired: {}".format(to_remove))
                self.remove_all(to_remove)
                for observer in self.observers:
                    for nid in to_remove:
                        observer.close(nid, CloseReason.EXPIRED)

    @classmethod
    def load(cls, filename):
        if not os.path.exists(filename):
            print("Creating empty notification queue")
            return cls([], 1)

        print("Loading notification queue from file")
        with open(filename, 'r') as f:
            queue = jsonpickle.decode(f.read())
        last_id = 1
        for notification in queue:
            if last_id < notification.id:
                last_id = int(notification.id)
        print("Found last id: {:d}".format(last_id))
        return cls(queue, last_id)
