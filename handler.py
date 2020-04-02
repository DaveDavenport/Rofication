import time
from typing import Tuple, Sequence, Mapping

from dbus import service, connection

from notification import Notification, NotificationQueue, NotificationObserver, CloseReason


class NotificationHandler(service.Object):
    def __init__(self, conn: connection.Connection, object_path: str, queue: NotificationQueue) -> None:
        super().__init__(conn, object_path)
        self.nq: NotificationQueue = queue
        self.nq.observers.append(NotificationHandlerObserver(self))

    @service.method("org.freedesktop.Notifications", in_signature='susssasa{ss}i', out_signature='u')
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
            notification.urgency = int(hints['urgency'])
        with self.nq.lock:
            self.nq.put(notification)
        return notification.id

    @service.signal("org.freedesktop.Notifications", signature='us')
    def ActionInvoked(self, id_in, action_key_in):
        pass

    @service.signal('org.freedesktop.Notifications', signature='uu')
    def NotificationClosed(self, id_in, reason_in):
        pass

    @service.method("org.freedesktop.Notifications", in_signature='', out_signature='as')
    def GetCapabilities(self) -> Sequence[str]:
        return "actions", "body"

    @service.method("org.freedesktop.Notifications", in_signature='u', out_signature='')
    def CloseNotification(self, id: int) -> None:
        with self.nq.lock:
            self.nq.remove(id)

    @service.method("org.freedesktop.Notifications", in_signature='', out_signature='ssss')
    def GetServerInformation(self) -> Tuple[str, str, str, str]:
        return "rofication", "http://gmpclient.org/", "0.0.1", "1"


class NotificationHandlerObserver(NotificationObserver):
    def __init__(self, handler: NotificationHandler) -> None:
        self.handler: NotificationHandler = handler

    def activate(self, notification: Notification) -> None:
        if "default" in notification.actions:
            self.handler.ActionInvoked(notification.id, "default")

    def close(self, nid: int, reason: CloseReason):
        self.handler.NotificationClosed(nid, reason)
