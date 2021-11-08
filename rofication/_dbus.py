import time
from typing import Tuple, Sequence, Mapping

from dbus import service, SessionBus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository.GLib import MainLoop

from ._metadata import ROFICATION_VERSION, ROFICATION_NAME, ROFICATION_URL
from ._notification import Notification, Urgency
from ._queue import NotificationQueue
from datetime import datetime

NOTIFICATIONS_DBUS_INTERFACE = 'org.freedesktop.Notifications'
NOTIFICATIONS_DBUS_OBJECT_PATH = '/org/freedesktop/Notifications'


class RoficationDbusObject(service.Object):
    def __init__(self, queue: NotificationQueue) -> None:
        super().__init__(
            object_path=NOTIFICATIONS_DBUS_OBJECT_PATH,
            bus_name=service.BusName(
                name=NOTIFICATIONS_DBUS_INTERFACE,
                bus=SessionBus(mainloop=DBusGMainLoop())
            )
        )
        self._queue: NotificationQueue = queue

        def notification_seen(notification):
            if 'default' in notification.actions:
                self.ActionInvoked(notification.id, 'default')

        self._queue.notification_seen += notification_seen

        def notification_closed(notification, reason):
            self.NotificationClosed(notification.id, reason)

        self._queue.notification_closed += notification_closed

    @service.signal(NOTIFICATIONS_DBUS_INTERFACE, signature='us')
    def ActionInvoked(self, id_in, action_key_in):
        pass

    @service.method(NOTIFICATIONS_DBUS_INTERFACE, in_signature='u', out_signature='')
    def CloseNotification(self, id: int) -> None:
        with self._queue.lock:
            self._queue.remove(id)

    @service.method(NOTIFICATIONS_DBUS_INTERFACE, in_signature='', out_signature='as')
    def GetCapabilities(self) -> Sequence[str]:
        return 'actions', 'body'

    @service.method(NOTIFICATIONS_DBUS_INTERFACE, in_signature='', out_signature='ssss')
    def GetServerInformation(self) -> Tuple[str, str, str, str]:
        return ROFICATION_NAME, ROFICATION_URL, ROFICATION_VERSION, '1.2'

    @service.signal(NOTIFICATIONS_DBUS_INTERFACE, signature='uu')
    def NotificationClosed(self, id_in, reason_in):
        pass

    @service.method(NOTIFICATIONS_DBUS_INTERFACE, in_signature='susssasa{ss}i', out_signature='u')
    def Notify(self, app_name: str, replaces_id: int, app_icon: str, summary: str,
               body: str, actions: Sequence[str], hints: Mapping[str, any], expire_timeout: int) -> int:
        notification = Notification()
        notification.id = replaces_id
        notification.application = app_name
        notification.icon = app_icon
        notification.summary = summary
        notification.body = body
        notification.hints = hints
        notification.timestamp = datetime.now().timestamp()
        notification.actions = tuple(actions)
        if int(expire_timeout) > 0:
            notification.deadline = time.time() + expire_timeout / 1000.0
        if 'urgency' in hints:
            notification.urgency = Urgency(int(hints['urgency']))
        with self._queue.lock:
            self._queue.put(notification)
        return notification.id


class RoficationDbusService:
    def __init__(self, queue: NotificationQueue) -> None:
        # preserve D-Bus object reference
        self._object = RoficationDbusObject(queue)
        # create GLib mainloop, this is needed to make D-Bus work and takes care of catching signals.
        self._loop = MainLoop()

    def run(self) -> None:
        self._loop.run()
