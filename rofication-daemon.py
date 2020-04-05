#!/usr/bin/env python3

from rofication import RoficationServer, NotificationQueue, RoficationDbusService


def main() -> None:
    not_queue = NotificationQueue.load("not.json")
    service = RoficationDbusService(not_queue)
    with RoficationServer(not_queue) as server:
        server.start()
        try:
            service.run()
        except:
            server.shutdown()
    not_queue.save("not.json")


if __name__ == '__main__':
    main()
