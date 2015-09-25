from enum import Enum,IntEnum

class Urgency(IntEnum):
    low = 0
    normal = 1
    critical = 2

class Msg():
    def __init__(self):
        self.mid=0
        self.notid=-1
        self.message=""
        self.deadline=-1
        self.summary=""
        self.body=""
        self.application="n/a"
        self.urgency=int(Urgency.normal)
        pass

