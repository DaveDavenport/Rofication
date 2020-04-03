from dataclasses import dataclass
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


@dataclass
class Notification:
    id: Optional[int] = None
    deadline: Optional[float] = None
    summary: Optional[str] = None
    body: Optional[str] = None
    application: Optional[str] = None
    urgency: Urgency = Urgency.NORMAL
    actions: Sequence[str] = ()

    def asdict(self) -> Mapping[str, any]:
        return vars(self)

    @classmethod
    def make(cls, dct: Mapping[str, any]) -> 'Notification':
        return cls(**dct)
