#!/usr/bin/env python3

import dbus
from dbus.mainloop import glib
from gi.repository import GLib

from rofication import RoficationServer, NotificationQueue, NotificationHandler


def main() -> None:
    not_queue = NotificationQueue.load("not.json")

    # Setup DBUS
    glib.DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    bus_name = dbus.service.BusName("org.freedesktop.Notifications", session_bus)
    not_handler = NotificationHandler(session_bus, '/org/freedesktop/Notifications', not_queue)

    with RoficationServer(not_queue) as server:
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


if __name__ == '__main__':
    main()
