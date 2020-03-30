#!/usr/bin/env python3
import os

import dbus
from dbus.mainloop import glib
from gi.repository import GObject

import handler
import notification
import rofication

"""
    Main function
"""
if __name__ == '__main__':
    """ Pre-start cleanup """
    if os.path.exists("/tmp/rofi_notification_daemon"):
        os.remove("/tmp/rofi_notification_daemon")

    """ Create notification queue """
    nq = notification.NotificationQueue.load("not.json")

    """ Create daemon """
    rofication = rofication.Rofication(nq)

    """ Setup DBUS"""
    glib.DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    name = dbus.service.BusName("org.freedesktop.Notifications", session_bus)
    nh = handler.NotificationHandler(session_bus, '/org/freedesktop/Notifications', nq)

    # Thread handling sockets.
    rofication.start()
    ##
    # Create Glib mainloop, this is needed to make dbus work.
    # GMainLoop also takes care for catching signals.
    ##
    try:
        GObject.MainLoop().run()
    except:
        # Set event telling it to quit.
        rofication.event.set()
    # Join unix socket thread.
    rofication.join()
    nq.save("not.json")
