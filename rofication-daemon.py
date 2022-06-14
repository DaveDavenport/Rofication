#!/usr/bin/env python3
import jsonpickle
import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GObject, GLib
import os
import subprocess
import sys
import threading
import time
import socket
import json

from msg import Msg,Urgency

event = threading.Event()


"""
    This is a list of applications where only the last notification is relevant.
    Applications like media players fall in this category.
"""
single_notification_app=[ "VLC media player" ]

"""
    A list of applications that are allowed to expire.
"""
allowed_expire_app=[ ]


class Rofication(threading.Thread):

    def __init__(self):
        self.socket_path = "/tmp/rofi_notification_daemon"
        self.notification_queue_lock = threading.Lock()
        self.notification_queue = []
        self.last_id=0
        super().__init__()

    def load(self):
        print("Loading rofication")
        try:
            with open('not.json', 'r') as f:
                     self.notification_queue = jsonpickle.decode(f.read())
        except:
            pass

        for noti in self.notification_queue:
            noti.notid=-1
            if self.last_id < noti.mid:
                self.last_id = int(noti.mid)
        print("Found last id: {nid}".format(nid=nf._id))

    def save(self):
        print("Saving rofication")
        try:
            with open('not.json','w') as f:
                f.write(jsonpickle.encode(self.notification_queue))
        except:
            print("Failed to store queue.")
    """
        This function updates the queue. E.g. removes popups that are expired and allowed to expire
    """
    def update_queue(self):
        with self.notification_queue_lock:
            now = time.time()
            n = [ n for n in self.notification_queue if n.application in allowed_expire_app and n.deadline > 0 and n.deadline < now ];
            for no in n:
                print("{mid} expired.".format(mid=no.mid))
                self.notification_queue.remove(no)

    def remove_notification(self,id):
        printf("Removing: {}".format(id))
        with self.notification_queue_lock:
            n = [ n for n in self.notification_queue_lock if n.notid == id ]
            for no in n:
                print("Closing: {id}:{sum}".format(id=no.mid, sum=no.application))

    def add_notification(self,notif):
        with self.notification_queue_lock:
            if notif.application in  single_notification_app:
                n = [ n for n in self.notification_queue if n.application == notif.application ];
                for no in n:
                    self.notification_queue.remove(no)

            self.notification_queue.append(notif)

    """
        Communication command.
    """
    def communication_command_send_list(self,connection):
        with self.notification_queue_lock:
            i=0
            for noti in self.notification_queue:
                connection.send(bytes(jsonpickle.encode(noti),'utf-8'))
                connection.send(b'\n')
                i+=1
    def communication_command_delete(self, connection, arg):
        with self.notification_queue_lock:
            for noti in self.notification_queue:
                if noti.mid == int(arg):
                    self.notification_queue.remove(noti)
                    break
    def communication_command_delete_apps(self, connection, arg):
        remove_q = []
        with self.notification_queue_lock:
            for noti in self.notification_queue:
                if noti.application == arg:
                    remove_q.append(noti);
            for noti in remove_q:
                self.notification_queue.remove(noti)

    def communication_command_saw(self, connection, arg):
        with self.notification_queue_lock:
            for noti in self.notification_queue:
                if noti.mid == int(arg):
                    noti.urgency = int(Urgency.normal)
                    break

    def communication_command_num(self, connection):
        with self.notification_queue_lock:
            u = [ n for n in self.notification_queue if n.urgency == Urgency.critical ];
            mstr = "{lent}\n{ul}".format(lent=len(self.notification_queue),ul=str(len(u)))
            connection.send(bytes(mstr, 'utf-8'))

    def run(self):
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        server.listen(1)
        server.settimeout(1)
        while 1:
            try:
                connection, client_address = server.accept()
                self.update_queue()
                try:
                    data = connection.recv(1024).decode('utf-8')
                    command = data.split(':')[0]

                    # Get number of notifications
                    if command == "num":
                        self.communication_command_num(connection)
                    # Getting a listing.
                    elif command == "list":
                        self.communication_command_send_list(connection)
                    # Dismiss and item.
                    elif command == "del":
                        self.communication_command_delete(connection,data.split(':')[1])
                    elif command == "dela":
                        self.communication_command_delete_apps(connection,data.split(':')[1])
                    # Saw an item, this sets the urgency to normal.
                    elif command == "saw":
                        self.communication_command_saw(connection, data.split(':')[1])
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
    _rofication = None

    @dbus.service.method("org.freedesktop.Notifications",
                         in_signature='susssasa{ss}i',
                         out_signature='u')
    def Notify(self, app_name, notification_id, app_icon,
               summary, body, actions, hints, expire_timeout):
        msg = Msg()
        # find id.
        self._id += 1
        msg.application  = str(app_name)
        msg.notid        = notification_id
        msg.mid          = self._id
        msg.summary      = str(summary)
        msg.body         = str(body)
        if int(expire_timeout) > 0:
            msg.deadline = time.time()+int(expire_timeout) / 1000.0
        if 'urgency' in hints:
            msg.urgency  = int(hints['urgency'])
        self._rofication.add_notification( msg )
        return notification_id

    @dbus.service.method("org.freedesktop.Notifications", in_signature='', out_signature='as')
    def GetCapabilities(self):
        return ("body")

    @dbus.service.signal('org.freedesktop.Notifications', signature='uu')
    def NotificationClosed(self, id_in, reason_in):
        _rofication.remove_notification(id_in)
        pass

    @dbus.service.method("org.freedesktop.Notifications", in_signature='u', out_signature='')
    def CloseNotification(self, id):
        _rofication.remove_notification(id)
        pass

    @dbus.service.method("org.freedesktop.Notifications", in_signature='', out_signature='ssss')
    def GetServerInformation(self):
      return ("rofication", "http://gmpclient.org/", "0.0.1", "1")

"""
    Main function
"""
if __name__ == '__main__':
    """ Create daemon """
    rofication = Rofication();

    """ Setup DBUS"""
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    name = dbus.service.BusName("org.freedesktop.Notifications", session_bus)
    nf = NotificationFetcher(session_bus, '/org/freedesktop/Notifications')

    nf._rofication = rofication;

    rofication.load();
    nf._id = rofication.last_id

    # Thread handling sockets.
    rofication.start()
    ##
    # Create Glib mainloop, this is needed to make dbus work.
    # GMainLoop also takes care for catching signals.
    ##
    try:
        GLib.MainLoop().run()
    except:
        # Set event telling it to quit.
        event.set()
    # Join unix socket thread.
    rofication.join()
    rofication.save()
