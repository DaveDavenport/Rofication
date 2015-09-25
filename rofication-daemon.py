#!/usr/bin/env python3
import jsonpickle
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GObject
import os
import subprocess
import sys
import threading
import time
import socket
import json

from msg import Msg,Urgency

event = threading.Event()
notification_queue = []
notification_queue_lock = threading.Lock()

"""
    This is a list of applications where only the last notification is relevant.
    Applications like media players fall in this category.
"""
single_notification_app=[ "VLC media player" ]

"""
    A list of applications that are allowed to expire.
"""
allowed_expire_app=[ ]


"""
    This function updates the queue. E.g. removes popups that are expired and allowed to expire
"""
def update_queue():
    with notification_queue_lock:
        now = time.time()
        n = [ n for n in notification_queue if n.application in allowed_expire_app and n.deadline > 0 and n.deadline < now ];
        for no in n:
            print("{mid} expired.".format(mid=no.mid))
            notification_queue.remove(no)

def add_notification(notif):
    with notification_queue_lock:
        if notif.application in  single_notification_app:
            n = [ n for n in notification_queue if n.application == notif.application ];
            for no in n:
                notification_queue.remove(no)

        notification_queue.append(notif)

def message_thread(dummy):
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind("/tmp/rofi_notification_daemon")
    server.listen(1)
    server.settimeout(1)
    while 1:
        try:
            connection, client_address = server.accept()
            update_queue()
            try:
                data = connection.recv(4)
                data = data.decode('utf-8')
                if data == "numn":
                    with notification_queue_lock:
                        u = [ n for n in notification_queue if n.urgency == Urgency.critical ];
                        mstr = "{lent}\n{ul}".format(lent=len(notification_queue),ul=str(len(u)))
                        connection.send(bytes(mstr, 'utf-8'))
                if data == "list":
                    with notification_queue_lock:
                        i=0
                        for noti in notification_queue:
                            connection.send(bytes(jsonpickle.encode(noti),'utf-8'))
                            connection.send(b'\n')
                            i+=1
                # Dismiss and item.
                elif data == "del:":
                    data = connection.recv(4).decode('utf-8')
                    print("Delete: {0}".format(data))
                    for noti in notification_queue:
                        if noti.mid == int(data):
                            notification_queue.remove(noti)
                            break
                # Saw an item, this sets the urgency to normal.
                elif data == "saw:":
                    data = connection.recv(4).decode('utf-8')
                    for noti in notification_queue:
                        if noti.mid == int(data):
                            noti.urgency = int(Urgency.normal)
            finally:
                # Clean up the connection
                connection.close()
        except:
            if event.is_set():
                break;
    server.close()
    os.unlink("/tmp/rofi_notification_daemon")

"""
    DBUS Notification Listener and Fetcher.
"""
class NotificationFetcher(dbus.service.Object):
    _id = 0

    @dbus.service.method("org.freedesktop.Notifications",
                         in_signature='susssasa{ss}i',
                         out_signature='u')
    def Notify(self, app_name, notification_id, app_icon,
               summary, body, actions, hints, expire_timeout):
        msg = Msg()
        # find id.
        self._id += 1
        notification_id = self._id
        msg.application = str(app_name)
        msg.mid     = notification_id
        msg.summary = str(summary)
        msg.body    = str(body)
        if int(expire_timeout) > 0:
            msg.deadline= time.time()+int(expire_timeout) / 1000.0
        if 'urgency' in hints:
            msg.urgency = int(hints['urgency'])
        add_notification( msg )
        return notification_id

    @dbus.service.method("org.freedesktop.Notifications", in_signature='', out_signature='as')
    def GetCapabilities(self):
        return ("body")

    @dbus.service.signal('org.freedesktop.Notifications', signature='uu')
    def NotificationClosed(self, id_in, reason_in):
        pass

    @dbus.service.method("org.freedesktop.Notifications", in_signature='u', out_signature='')
    def CloseNotification(self, id):
        pass

    @dbus.service.method("org.freedesktop.Notifications", in_signature='', out_signature='ssss')
    def GetServerInformation(self):
      return ("rofication", "http://gmpclient.org/", "0.0.1", "1")

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    name = dbus.service.BusName("org.freedesktop.Notifications", session_bus)
    nf = NotificationFetcher(session_bus, '/org/freedesktop/Notifications')

    try:
        with open('not.json', 'r') as f:
            notification_queue = jsonpickle.decode(f.read())
    except:
        pass

    for noti in notification_queue:
        if nf._id < noti.mid:
            nf._id = int(noti.mid)
    print("Found last id: {nid}".format(nid=nf._id))
    # Thread handling sockets.
    t1 = threading.Thread(target=message_thread, args=[None])
    t1.start()
    ##
    # Create Glib mainloop, this is needed to make dbus work.
    # GMainLoop also takes care for catching signals.
    ##
    try:
        GObject.MainLoop().run()
    except:
        # Set event telling it to quit.
        event.set()
    # Join unix socket thread.
    t1.join()
    try:
        with open('not.json','w') as f:
            f.write(jsonpickle.encode(notification_queue))
    except:
        print("Failed to store queue.")
