from enum import IntEnum
from typing import Sequence, Optional, Mapping


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
    def __init__(self) -> None:
        self.id: Optional[int] = None
        self.deadline: Optional[float] = None
        self.summary: Optional[str] = None
        self.body: Optional[str] = None
        self.application: Optional[str] = None
        self.urgency: Urgency = Urgency.NORMAL
        self.actions: Sequence[str] = ()

    def asdict(self) -> Mapping[str, any]:
        return {field: value for field, value in vars(self).items() if value is not None}

    @classmethod
    def make(cls, dct: Mapping[str, any]) -> 'Notification':
        notification: 'Notification' = cls()
        notification.id = dct.get('id')
        notification.deadline = dct.get('deadline')
        notification.summary = dct.get('summary')
        notification.body = dct.get('body')
        notification.application = dct.get('application')
        notification.urgency = Urgency(dct.get('urgency', Urgency.NORMAL))
        notification.actions = tuple(dct.get('actions', ()))
        return notification
