import os
from dataclasses import dataclass
from subprocess import check_output
from typing import Optional


@dataclass
class Resource:
    default: str
    xres_name: str
    env_name: Optional[str] = None

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
