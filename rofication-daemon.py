#!/usr/bin/env python3

import dbus
from dbus.mainloop import glib
from gi.repository import GLib

import handler
import notification
from rofication import NotificationServer

"""
    Main function
"""
if __name__ == '__main__':
    """ Create notification queue """
    not_queue = notification.NotificationQueue.load("not.json")

    """ Setup DBUS"""
    glib.DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("org.freedesktop.Notifications", session_bus)
    not_handler = handler.NotificationHandler(session_bus, '/org/freedesktop/Notifications', not_queue)

    with NotificationServer("/tmp/rofi_notification_daemon", not_queue) as server:
        server.start()
        try:
            ##
            # Create Glib mainloop, this is needed to make dbus work.
            # GMainLoop also takes care for catching signals.
            ##
            GLib.MainLoop().run()
        except:
            server.shutdown()

    not_queue.save("not.json")
