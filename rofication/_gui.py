import re
import struct
import subprocess
from typing import Iterable, List
from datetime import datetime

from gi.repository import GLib

from ._client import RoficationClient
from ._notification import Urgency, Notification
from ._util import Resource

HTML_TAGS_PATTERN = re.compile(r'<[^>]*?>')

ROFI_COMMAND = ('rofi',
                '-dmenu',
                '-p', 'Notifications',
                '-markup',
                '-kb-accept-entry', 'Control+j,Control+m,KP_Enter',
                '-kb-remove-char-forward', 'Control+d',
                '-kb-delete-entry', '',
                '-kb-custom-1', 'Delete',
                '-kb-custom-2', 'Return',
                '-kb-custom-3', 'Alt+r',
                '-kb-custom-4', 'Shift+Delete',
                '-markup-rows',
                '-sep', '\\0',
                '-format', 'i',
                '-eh', '2',
                '-lines', '10')


def strip_tags(value: str) -> str:
    return GLib.markup_escape_text(HTML_TAGS_PATTERN.sub('', value))


def rofi_entry(notification: Notification, tsformat: str) -> str:
    stripped_summ = strip_tags(notification.summary)
    stripped_app = strip_tags(notification.application)
    stripped_body = strip_tags(' '.join(notification.body.split()))
    formatted_ts = f"{datetime.fromtimestamp(notification.timestamp).strftime(tsformat)} " if tsformat else ""
    return f'<b>{formatted_ts}{stripped_summ}</b> <small>({stripped_app})</small>\n<small>{stripped_body}</small>'

def call_rofi(entries: Iterable[str], additional_args: List[str] = None) -> (int, int):
    command = ROFI_COMMAND
    if additional_args is not None:
        command = list(command) + additional_args

    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    with proc.stdin as stdin:
        for e in entries:
            stdin.write(e.encode('utf-8'))
            stdin.write(struct.pack('B', 0))

    selected = proc.stdout.read().decode('utf-8')
    exit_code = proc.wait()

    if selected:
        return int(selected), exit_code
    else:
        return -1, exit_code


class RoficationGui():
    def __init__(self, client: RoficationClient = None):
        self._client: RoficationClient = RoficationClient() if client is None else client
        self._tsformat = Resource(env_name='i3xrocks_notify_timestamp_format', xres_name='i3xrocks.notify.timestamp.format', default='').fetch()

    def run(self) -> None:
        selected = 0
        while selected >= 0:
            notifications = []
            entries = []
            urgent = []
            low = []
            args = []

            # reassigns indices of notifications
            for index, notification in enumerate(self._client.list()):
                notifications.append(notification)
                entries.append(rofi_entry(notification, self._tsformat))
                if notification.urgency == Urgency.CRITICAL:
                    urgent.append(str(index))
                if notification.urgency == Urgency.LOW:
                    low.append(str(index))

            if urgent:
                args.append('-u')
                args.append(','.join(urgent))

            if low:
                args.append('-a')
                args.append(','.join(low))

            if selected >= 0:
                args.append('-selected-row')
                args.append(str(selected))

            # Show rofi
            selected, exit_code = call_rofi(entries, args)

            if selected >= 0:
                # Dismiss notification
                if exit_code == 10:
                    self._client.delete(notifications[selected].id)
                    # This was the last notification
                    if len(notifications) == 1:
                        break
                # Seen notification
                elif exit_code == 11:
                    self._client.see(notifications[selected].id)
                # Dismiss all notifications for application
                elif exit_code == 13:
                    self._client.delete_all(notifications[selected].application)
                    # This was the last group of notifications
                    if len(notifications) == 1:
                        break
                elif exit_code != 12:
                    break
