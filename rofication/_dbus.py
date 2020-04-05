import time
from typing import Tuple, Sequence, Mapping

from dbus import service, SessionBus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository.GLib import MainLoop

from ._notification import Notification, CloseReason, Urgency
from ._queue import NotificationQueue, NotificationQueueObserver

NOTIFICATIONS_DBUS_INTERFACE = 'org.freedesktop.Notifications'
NOTIFICATIONS_DBUS_OBJECT_PATH = '/org/freedesktop/Notifications'


class DbusObjectNotificationQueueObserver(NotificationQueueObserver):
    def __init__(self, obj: 'RoficationDbusObject') -> None:
        self._object: RoficationDbusObject = obj

    def activate(self, notification: Notification) -> None:
        if "default" in notification.actions:
            self._object.ActionInvoked(notification.id, "default")

    def close(self, notification: Notification, reason: CloseReason) -> None:
        self._object.NotificationClosed(notification.id, reason)


class RoficationDbusObject(service.Object):
    def __init__(self, queue: NotificationQueue) -> None:
        super().__init__(
            object_path=NOTIFICATIONS_DBUS_OBJECT_PATH,
            bus_name=service.BusName(
                name=NOTIFICATIONS_DBUS_INTERFACE,
                bus=SessionBus(mainloop=DBusGMainLoop())
            )
        )
        self._not_queue: NotificationQueue = queue
        self._not_queue.observers.append(DbusObjectNotificationQueueObserver(self))

    @service.signal(NOTIFICATIONS_DBUS_INTERFACE, signature='us')
    def ActionInvoked(self, id_in, action_key_in):
        pass

    @service.method(NOTIFICATIONS_DBUS_INTERFACE, in_signature='u', out_signature='')
    def CloseNotification(self, id: int) -> None:
        with self._not_queue.lock:
            self._not_queue.remove(id)

    @service.method(NOTIFICATIONS_DBUS_INTERFACE, in_signature='', out_signature='as')
    def GetCapabilities(self) -> Sequence[str]:
        return "actions", "body"

    @service.method(NOTIFICATIONS_DBUS_INTERFACE, in_signature='', out_signature='ssss')
    def GetServerInformation(self) -> Tuple[str, str, str, str]:
        return "rofication", "https://github.com/regolith-linux/regolith-rofication", "1.4", "1.2"

    @service.signal(NOTIFICATIONS_DBUS_INTERFACE, signature='uu')
    def NotificationClosed(self, id_in, reason_in):
        pass

    @service.method(NOTIFICATIONS_DBUS_INTERFACE, in_signature='susssasa{ss}i', out_signature='u')
    def Notify(self, app_name: str, replaces_id: int, app_icon: str, summary: str,
               body: str, actions: Sequence[str], hints: Mapping[str, any], expire_timeout: int) -> int:
        notification = Notification()
        notification.id = replaces_id
        notification.application = app_name
        notification.summary = summary
        notification.body = body
        notification.actions = tuple(actions)
        if int(expire_timeout) > 0:
            notification.deadline = time.time() + int(expire_timeout) / 1000.0
        if 'urgency' in hints:
            notification.urgency = Urgency(int(hints['urgency']))
        with self._not_queue.lock:
            self._not_queue.put(notification)
        return notification.id


class RoficationDbusService:
    def __init__(self, queue: NotificationQueue) -> None:
        # preserve D-Bus object reference
        self._object = RoficationDbusObject(queue)
        # create GLib mainloop, this is needed to make D-Bus work and takes care of catching signals.
        self._loop = MainLoop()

    def run(self) -> None:
        self._loop.run()
