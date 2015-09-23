# Rofication

**Rofication** is a minimalistic notification system. It is loosely modeled after notification
centers on android and windows 10.

To summarize:

 * 1 point to see if there are notifications.
![Notification Bar](https://raw.githubusercontent.com/DaveDavenport/Rofication/master/Picture/bar.png)
 * An application to view all open notifications.
![Notification Bar](https://raw.githubusercontent.com/DaveDavenport/Rofication/master/Picture/client.png)
 * Notifications are persistent, until dismissed. Even over reboots.

# Techniques used

**Rofication** implements a notification daemon following the [Galago Desktop Notification
standard](http://www.galago-project.org/specs/notification/).  This is used by most linux desktop
environments and most relevant application support this. It is easily scriptable using
`notify-send`.  **Rofication** aims to be a drop-in replacement for existing notification daemons.

**Rofication** tries to re-use as much existing as possible. It uses **Rofi** for displaying, 
i3blocks for notification and python for `d-bus`.

# Structure

```
┌─────────────┐           ┌───────────────────┐                      ┌────────────────┐
│ application │ --dbus--> │ rofication-daemon │ <--- unix-socket --> │ rofication-gui │
└─────────────┘           └───────────────────┘       │              └────────────────┘
                                |                     │             ┌──────────────────────────┐
                                |                     \-----------> │ rofication-statusi3blocks│
                            <hdd:json-db>                           └──────────────────────────┘
```

## Daemon

**Rofication** daemon is a small python script that listens for notification messages on the local
dbus. Notifications are internally queue'd (an preserved) and can be viewed by a client via a
unix-socket.

## Notification 

**Rofication** does not implement it own 'widget' to display this notification. Instead it can be
easily integrated into existing tools.  Currently we ship a small script to integrate into
`i3-blocks`. This shows the number of notifications and signals when there are cirtical
notifications.

## GUI

The **Rofication** gui consists of a small python script wrapping **Rofi**. The GUI allows the user
to view notification, mark them seen and dismiss them.

## CLI

*This still needs to be written*
	 
