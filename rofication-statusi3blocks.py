#!/usr/bin/env python3

import os
import socket
from dataclasses import dataclass
from subprocess import check_output
from typing import Optional

from rofication import Rofication


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


def main() -> None:
    if os.getenv('button'):
        Rofication().run()

    value_font = Resource('Source Code Pro Medium 13', 'i3xrocks.value.font', 'font')

    notify_none = Resource('N', 'i3xrocks.label.notify.none', 'i3xrocks_label_notify_none')
    notify_some = Resource('N', 'i3xrocks.label.notify.some', 'i3xrocks_label_notify_some')
    notify_error = Resource('N', 'i3xrocks.label.notify.error', 'i3xrocks_label_notify_error')

    value_color = Resource('#D8DEE9', 'i3xrocks.value.color', 'color')
    nominal_color = Resource('#D8DEE9', 'i3xrocks.nominal', 'background_color')
    label_color = Resource('#7B8394', 'i3xrocks.label.color', 'label_color')
    critical_color = Resource('#BF616A', 'i3xrocks.critical.color')

    num: str
    label_icon = notify_none
    try:
        data: str
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect('/tmp/rofi_notification_daemon')
            client.send(b'num\n')
            data = client.recv(32).decode('utf-8')
        num, crit = data.split(',', 2)
        if int(num) > 0:
            label_icon = notify_some
        else:
            label_color = nominal_color
        if int(crit) > 0:
            value_color = critical_color
    except (FileNotFoundError, ConnectionRefusedError):
        label_icon = notify_error
        label_color = critical_color
        num = '?'

    # only fetch resources if needed
    label = f'<span foreground="{label_color.fetch()}">{label_icon.fetch()}</span>'
    value = f'<span font_desc="{value_font.fetch()}" foreground="{value_color.fetch()}"> {num}</span>'
    print(label + value)


if __name__ == '__main__':
    main()
