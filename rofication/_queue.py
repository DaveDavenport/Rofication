import json
import os
import threading
import time
from typing import Iterable, Iterator, MutableMapping, Mapping, Optional
from warnings import warn

from ._notification import Notification, CloseReason, Urgency
from ._util import Event

ALLOWED_TO_EXPIRE = ('notify-send',)
SINGLE_NOTIFICATION_APPS = ('VLC media player',)


class NotificationQueue:
    def __init__(self, mapping: Mapping[int, Notification] = None) -> None:
        self._lock = threading.Lock()
        self._last_id: int = max(mapping.keys()) + 1 if mapping else 1
        self._mapping: MutableMapping[int, Notification] = {} if mapping is None else dict(mapping)
        self.notification_seen = Event()
        self.notification_closed = Event()

    def __len__(self) -> int:
        return len(self._mapping)

    def __iter__(self) -> Iterator[Notification]:
        return iter(self._mapping.values())

    @property
    def lock(self) -> threading.Lock:
        return self._lock

    def save(self, filename: str) -> None:
        try:
            print('Saving notification queue to file')
            with open(filename, 'w') as f:
                json.dump(list(self._mapping.values()), f, default=Notification.asdict)
        except:
            warn('Failed to save notification queue')
            if os.path.exists(filename):
                os.unlink(filename)

    def see(self, nid: int) -> None:
        if nid in self._mapping:
            print(f'Seeing: {nid}')
            notification = self._mapping[nid]
            notification.urgency = Urgency.NORMAL
            self.notification_seen.notify(notification)
            return
        warn(f'Unable to find notification {nid}')

    def remove(self, nid: int) -> None:
        if nid in self._mapping:
            print(f'Removing: {nid}')
            del self._mapping[nid]
            return
        warn(f'Unable to find notification {nid}')

    def remove_all(self, nids: Iterable[int]) -> None:
        for nid in nids:
            self.remove(nid)

    def put(self, notification: Notification) -> None:
        to_replace: Optional[int]
        if notification.application in SINGLE_NOTIFICATION_APPS:
            # replace notification for applications that only allow one
            to_replace = next((ntf.id for ntf in self._mapping.values()
                               if ntf.application == notification.application), None)
        else:
            # cannot have two notifications with the same ID
            to_replace = notification.id if notification.id in self._mapping else None

        if to_replace:
            notification.id = to_replace
            print(f'Replacing: {notification.id}')
            self._mapping[notification.id] = notification
            return

        notification.id = self._last_id
        self._last_id += 1
        print(f'Adding: {notification.id}')
        self._mapping[notification.id] = notification

    def cleanup(self) -> None:
        now = time.time()
        to_remove = [ntf.id for ntf in self._mapping.values()
                     if ntf.deadline and ntf.deadline < now
                     and ntf.application in ALLOWED_TO_EXPIRE]
        if to_remove:
            print(f'Expired: {to_remove}')
            for nid in to_remove:
                self.notification_closed.notify(self._mapping[nid], CloseReason.EXPIRED)
                del self._mapping[nid]

    @classmethod
    def load(cls, filename: str) -> 'NotificationQueue':
        if not os.path.exists(filename):
            print('Creating empty notification queue')
            return cls({})

        try:
            print('Loading notification queue from file')
            with open(filename, 'r') as f:
                mapping = {n.id: n for n in json.load(f, object_hook=Notification.make)}
        except:
            warn('Failed to load notification queue')
            mapping = {}

        return cls(mapping)
