#!/usr/bin/env python

"""IRC Logger Daemon

For usage type:

   ./irclogger.py --help
"""


import os
from os import path
from socket import gethostname
from optparse import OptionParser
from time import asctime, localtime, strftime, time

import circuits
from circuits.app import Daemon
from circuits.io import File, Write
from circuits import Component, Event, Debugger
from circuits.net.sockets import TCPClient, Connect
from circuits.net.protocols.irc import IRC, USER, NICK, JOIN

from . import __name__, __version__

USAGE = "%prog [options] <host> [<port>]"
VERSION = "%prog v" + __version__

FILENAME = path.join(path.dirname(__file__), "{0:s}.log".format(__name__))
PIDFILE = path.join(path.dirname(__file__), "{0:s}.pid".format(__name__))


def parse_options():
    parser = OptionParser(usage=USAGE, version=VERSION)

    parser.add_option(
        "-d", "--daemon",
        action="store_true", default=False, dest="daemon",
        help="Enable daemon mode"
    )

    parser.add_option(
        "-c", "--channel",
        action="store", default="#circuits", dest="channel",
        help="Channel to join"
    )

    parser.add_option(
        "-f", "--filename",
        action="store", default=FILENAME, dest="filename",
        help="Filename to log to"
    )

    parser.add_option(
        "-n", "--nick",
        action="store", default=os.environ["USER"], dest="nick",
        help="Nickname to use"
    )

    parser.add_option(
        "-p", "--pidfile",
        action="store", default=PIDFILE, dest="pidfile",
        help="Path to store PID file"
    )

    parser.add_option(
        "-v", "--verbose",
        action="store_true", default=False, dest="verbose",
        help="Enable verbose debugging mode"
    )

    opts, args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        raise SystemExit(1)

    return opts, args


def timestamp():
    return asctime(localtime(time()))


class Log(Event):
    """Log Event"""

    channels = ("logger",)


class Logger(File):

    channel = "logger"

    def log(self, message):
        timestamp = strftime("[%H:%M:%S]", localtime(time()))
        self.fire(Write("{0:s} {1:s}\n".format(timestamp, message)), self.channel)


class Bot(Component):

    channel = "bot"

    def init(self, host, port=6667, opts=None):
        self.host = host
        self.port = port
        self.opts = opts
        self.hostname = gethostname()

        self.nick = opts.nick
        self.ircchannel = opts.channel

        # Debugger
        Debugger(events=opts.verbose).register(self)

        # Add TCPClient and IRC to the system.
        self += (TCPClient(channel=self.channel) + IRC(channel=self.channel))

        # Logger
        Logger(opts.filename, "a").register(self)

        # Daemon?
        if self.opts.daemon:
            Daemon(opts.pidfile).register(self)

    def ready(self, component):
        """Ready Event

        This event is triggered by the underlying ``TCPClient`` Component
        when it is ready to start making a new connection.
        """

        self.fire(Connect(self.host, self.port))

    def connected(self, host, port):
        """Connected Event

        This event is triggered by the underlying ``TCPClient`` Component
        when a successfully connection has been made.
        """

        self.fire(Log("[connected at {0:s}]".format(timestamp())))

        nick = self.nick
        hostname = self.hostname
        name = "%s on %s using circuits/%s" % (nick, hostname, circuits.__version__)

        self.fire(USER(nick, hostname, host, name))
        self.fire(NICK(nick))

    def disconnected(self):
        """Disconnected Event

        This event is triggered by the underlying ``TCPClient`` Component
        when the active connection has been terminated.
        """

        self.fire(Log("[disconnected at {0:s}]".format(timestamp())))

        self.fire(Connect(self.host, self.port))

    def numeric(self, source, target, numeric, args, message):
        """Numeric Event

        This event is triggered by the ``IRC`` Protocol Component when we have
        received an IRC Numberic Event from server we are connected to.
        """

        if numeric == 1:
            self.fire(JOIN(self.ircchannel))
        elif numeric == 433:
            self.nick = newnick = "%s_" % self.nick
            self.fire(NICK(newnick))

    def join(self, source, channel):
        """Join Event

        This event is triggered by the ``IRC`` Protocol Component when a
        user has joined a channel.
        """

        if source[0].lower() == self.nick.lower():
            self.fire(Log("[I have joined {0:s}]".format(channel)))
        else:
            self.fire(Log("[{0:s} has joined {1:s}]".format(source, channel)))

    def message(self, source, target, message):
        """Message Event

        This event is triggered by the ``IRC`` Protocol Component for each
        message we receieve from the server.
        """

        if target[0] == "#":
            self.fire(Log("<{0:s}> {1:s}".format(target, message)))
        else:
            self.fire(Log("<{0:s}> {1:s}".format(source, message)))


def main():
    opts, args = parse_options()

    host = args[0]
    port = int(args[1]) if len(args) > 1 else 6667

    # Configure and run the system.
    Bot(host, port, opts=opts).run()


if __name__ == "__main__":
    main()
