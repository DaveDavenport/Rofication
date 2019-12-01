#!/usr/bin/env python3
import sys
import socket
import os
from subprocess import check_output, Popen

notification_empty = os.getenv('i3xrocks_label_notify_none', check_output(['/usr/bin/xrescat', 'i3xrocks.label.notify.none', 'N'], universal_newlines=True))
notification_some = os.getenv('i3xrocks_label_notify_some', check_output(['/usr/bin/xrescat', 'i3xrocks.label.notify.some', 'N'], universal_newlines=True))
notification_error = os.getenv('i3xrocks_label_notify_error', check_output(['/usr/bin/xrescat', 'i3xrocks.label.notify.error', 'N'], universal_newlines=True))
default_color = os.getenv('color', check_output(['/usr/bin/xrescat', 'i3xrocks.value.color', '#D8DEE9'], universal_newlines=True))
default_label_color = os.getenv('label_color', check_output(['/usr/bin/xrescat', 'i3xrocks.label.color', '#7B8394'], universal_newlines=True))
critical_color = check_output(['/usr/bin/xrescat', 'i3xrocks.critical.color', '#BF616A'], universal_newlines=True)
valuefont = os.getenv('font', check_output(['/usr/bin/xrescat', 'i3xrocks.value.font', 'Source Code Pro Medium 13'], universal_newlines=True))

notification_value = 0
icon = notification_empty
label_color = default_label_color
form = '<span foreground="{}">{}</span><span font_desc="{}" foreground="{}"> {}</span>'

try:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect("/tmp/rofi_notification_daemon")
    client.sendall(bytes("num",'utf-8'))

    val = client.recv(32)
    val = val.decode('utf-8')
    l = val.split('\n',2)
    notification_value = int(l[0])
    if (notification_value > 0):
        icon = notification_some
    if int(l[1]) > 0:
        default_color = critical_color
except (FileNotFoundError, ConnectionRefusedError):
    icon = notification_error
    label_color = critical_color
    notification_value = "?"

print (form.format(label_color, icon, valuefont, default_color, notification_value))

if (os.getenv('button', "")):
    Popen(['/usr/bin/python3', '/usr/share/rofication/rofication-gui.py'])
