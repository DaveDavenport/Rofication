#!/usr/bin/env python3

import json
import re
import socket
import struct
import subprocess
from typing import Iterable, List

from gi.repository import GLib

from notification import Urgency, Notification

UNIX_SOCKET = '/tmp/rofi_notification_daemon'

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


def rofi_entry(notification: Notification) -> str:
    stripped_summ = strip_tags(notification.summary)
    stripped_app = strip_tags(notification.application)
    stripped_body = strip_tags(' '.join(notification.body.split()))
    return f"<b>{stripped_summ}</b> <small>({stripped_app})</small>\n<small>{stripped_body}</small>"


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


def send_command(command: str) -> None:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(UNIX_SOCKET)
        print(f'Send: {command}')
        client.send(bytes(f'{command}\n', encoding='utf-8'))


def main() -> None:
    selected = 0
    while selected >= 0:
        notifications = []
        entries = []
        urgent = []
        low = []
        args = []

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(UNIX_SOCKET)
            client.send(b'list\n')
            with client.makefile(mode='r', encoding='utf-8') as fp:
                not_queue = json.load(fp, object_hook=Notification.make)
                # reassigns indices of notifications
                for index, notification in enumerate(not_queue):
                    notifications.append(notification)
                    entries.append(rofi_entry(notification))
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
                send_command(f'del:{notifications[selected].id}')
            # Seen notification
            elif exit_code == 11:
                send_command(f'saw:{notifications[selected].id}')
            # Dismiss all notifications for application
            elif exit_code == 13:
                send_command(f'dela:{notifications[selected].application}')
            elif exit_code != 12:
                break


if __name__ == '__main__':
    main()
