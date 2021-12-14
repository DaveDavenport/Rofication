import os
from collections.abc import MutableSequence, Callable
from subprocess import check_output
from typing import Optional

class Event:
    def __init__(self) -> None:
        self._observers: MutableSequence[Callable] = []

    def __iadd__(self, observer: Callable) -> 'Event':
        self._observers.append(observer)
        return self

    def notify(self, *args, **kwargs) -> None:
        for observer in self._observers:
            observer(*args, **kwargs)


class Resource:
    def __init__(self, default: str, xres_name: str, env_name: Optional[str] = None):
        self.default: str = default
        self.xres_name: str = xres_name
        self.env_name: Optional[str] = env_name

    def fetch(self) -> str:
        env_val = None
        if self.env_name:
            env_val = os.getenv(self.env_name)

        # avoid calling xrescat if the environment variable is set
        if env_val is None:
            cmd = ('/usr/bin/xrescat', self.xres_name, self.default)
            return check_output(cmd, universal_newlines=True)
        else:
            return env_val
