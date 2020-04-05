import json
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Sequence, Iterable, MutableSequence, Iterator, MutableMapping, Mapping, Optional
from warnings import warn

from ._notification import Notification, CloseReason, Urgency


class NotificationQueueObserver(ABC):
    @abstractmethod
    def activate(self, notification: Notification) -> None:
        pass

    @abstractmethod
    def close(self, notification: Notification, reason: CloseReason) -> None:
        pass


class NotificationQueue:
    def __init__(self, mapping: Mapping[int, Notification] = None, last_id: int = 1) -> None:
        self._lock = threading.Lock()
        self._mapping: MutableMapping[int, Notification] = {} if mapping is None else dict(mapping)
        self.last_id: int = last_id
        self.allowed_to_expire: Sequence[str] = []
        self.single_notification_apps: Sequence[str] = ['VLC media player']
        self.observers: MutableSequence[NotificationQueueObserver] = []

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
            for observer in self.observers:
                observer.activate(notification)
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
        if notification.application in self.single_notification_apps:
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

        notification.id = self.last_id
        self.last_id += 1
        print(f'Adding: {notification.id}')
        self._mapping[notification.id] = notification

    def cleanup(self) -> None:
        now = time.time()
        to_remove = [ntf.id for ntf in self._mapping.values()
                     if ntf.deadline and ntf.deadline < now
                     and ntf.application in self.allowed_to_expire]
        if to_remove:
            print(f'Expired: {to_remove}')
            for observer in self.observers:
                for nid in to_remove:
                    observer.close(self._mapping[nid], CloseReason.EXPIRED)
                    del self._mapping[nid]

    @classmethod
    def load(cls, filename: str) -> 'NotificationQueue':
        if not os.path.exists(filename):
            print('Creating empty notification queue')
            return cls({}, 1)

        try:
            print('Loading notification queue from file')
            with open(filename, 'r') as f:
                mapping = {n.id: n for n in json.load(f, object_hook=Notification.make)}
        except:
            warn('Failed to load notification queue')
            mapping = {}

        last_id = max(mapping.keys()) if mapping else 0
        print(f'Found last id: {last_id}')
        return cls(mapping, last_id + 1)
