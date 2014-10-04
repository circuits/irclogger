#!/usr/bin/env python


"""IRC Logger Daemon

For usage type:

   ./irclogger.py --help
"""


from socket import gethostname
from optparse import OptionParser
from collections import defaultdict
from socket import error as SocketError
from re import compile as compile_regex
from datetime import date, datetime, timedelta
from os import environ, getcwd, makedirs, path
from time import asctime, localtime, strftime, time


import circuits

from circuits import handler, Component, Event, Debugger, Timer

from circuits.app import Daemon

from circuits.io import File
from circuits.io.events import close, open, write

from circuits.net.events import connect
from circuits.net.sockets import TCPClient

from circuits.protocols.irc import ERR_NICKNAMEINUSE
from circuits.protocols.irc import IRC, USER, NICK, JOIN
from circuits.protocols.irc import RPL_ENDOFMOTD, ERR_NOMOTD


from . import __name__, __version__


USAGE = "%prog [options] <host> [<port>]"
VERSION = "%prog v" + __version__

LOGFILE_REGEX = compile_regex("^(.*)\.(.*)\.log$")
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
        action="append", default=None, dest="channels",
        help="Channel to join (multiple allowed)"
    )

    parser.add_option(
        "-n", "--nick",
        action="store", default=environ["USER"], dest="nick",
        help="Nickname to use"
    )

    parser.add_option(
        "-o", "--output",
        action="store", default=getcwd(), dest="output",
        help="Path to store log files"
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

    if not opts.channels:
        print("ERROR: Must specify at least one channel")
        parser.print_help()
        raise SystemExit(2)

    if len(args) < 1:
        print("ERROR: Must specify a host to connect to")
        parser.print_help()
        raise SystemExit(1)

    return opts, args


def timestamp():
    return asctime(localtime(time()))


def generate_logfile(channel):
    return path.join(channel, "{0:s}.log".format(
        strftime("%Y-%m-%d", localtime()))
    )


def parse_logfile(filename):
    match = LOGFILE_REGEX.match(filename)
    return match.groups() if match is not None else "", ""


class log(Event):
    """log Event"""


class rotate(Event):
    """rotate Event"""


class Logger(File):

    def init(self, *args, **kwargs):
        super(Logger, self).init(*args, **kwargs)

        interval = datetime.fromordinal((
            date.today() + timedelta(1)
        ).toordinal())
        Timer(interval, rotate(), self.channel).register(self)

    def rotate(self):
        dirname = path.dirname(self.filename)
        filename = path.basename(self.filename)
        channel, _ = parse_logfile(filename)
        logfile = generate_logfile(channel)
        self.fire(close(), self.channel)
        self.fire(open(path.join(dirname, logfile), "a"), self.channel)

        interval = datetime.fromordinal((
            date.today() + timedelta(1)
        ).toordinal())
        Timer(interval, rotate(), self.channel).register(self)

    def log(self, message):
        timestamp = strftime("[%H:%M:%S]", localtime(time()))
        self.fire(
            write(
                u"{0:s} {1:s}\n".format(
                    timestamp, message
                ).encode("utf-8")
            ),
            self.channel
        )


class Bot(Component):

    channel = "bot"

    def init(self, host, port=6667, opts=None):
        self.host = host
        self.port = port
        self.opts = opts
        self.hostname = gethostname()

        self.nick = opts.nick
        self.ircchannels = opts.channels

        # Mapping of IRC Channel -> Set of Nicks
        self.chanmap = defaultdict(set)

        # Mapping of Nick -> Set of IRC Channels
        self.nickmap = defaultdict(set)

        # Debugger
        Debugger(events=opts.verbose).register(self)

        # Add TCPClient and IRC to the system.
        self.transport = TCPClient(channel=self.channel).register(self)
        self.protocol = IRC(channel=self.channel).register(self)

        # Logger(s)
        for ircchannel in self.ircchannels:
            if not path.exists(path.join(opts.output, ircchannel)):
                makedirs(path.join(opts.output, ircchannel))

            Logger(
                path.join(opts.output, generate_logfile(ircchannel)), "a",
                channel="logger.{0:s}".format(ircchannel)
            ).register(self)

        # Daemon?
        if self.opts.daemon:
            Daemon(opts.pidfile).register(self)

        # Keep-Alive Timer
        Timer(60, Event.create("keepalive"), persist=True).register(self)

    def ready(self, component):
        """Ready Event

        This event is triggered by the underlying ``TCPClient`` Component
        when it is ready to start making a new connection.
        """

        self.fire(connect(self.host, self.port))

    def keepalive(self):
        self.fire(write(b"\x00"))

    def error(self, etype, evalue, etraceback, handler=None):
        if isinstance(evalue, SocketError):
            if not self.transport.connected:
                Timer(5, connect(self.host, self.port)).register(self)

    def connected(self, host, port):
        """Connected Event

        This event is triggered by the underlying ``TCPClient`` Component
        when a successfully connection has been made.
        """

        nick = self.nick
        hostname = self.hostname
        name = "{0:s} on {1:s} using circuits/{2:s}".format(
            nick, hostname, circuits.__version__
        )

        self.fire(USER(nick, hostname, host, name))
        self.fire(NICK(nick))

    def disconnected(self):
        """Disconnected Event

        This event is triggered by the underlying ``TCPClient`` Component
        when the active connection has been terminated.
        """

        self.fire(connect(self.host, self.port))

    def numeric(self, source, numeric, target, *args):
        """Numeric Event

        This event is triggered by the ``IRC`` Protocol Component when we have
        received an IRC Numberic Event from server we are connected to.
        """

        if numeric == ERR_NICKNAMEINUSE:
            self.fire(NICK("{0:s}_".format(args[0])))
        elif numeric in (RPL_ENDOFMOTD, ERR_NOMOTD):
            for ircchannels in self.ircchannels:
                for ircchannel in ircchannels.split(","):
                    self.fire(JOIN(ircchannel))

    def join(self, source, channel):
        """Join Event

        This event is triggered by the ``IRC`` Protocol Component when a
        user has joined a channel.
        """

        self.chanmap[channel].add(source[0])
        self.nickmap[source[0]].add(channel)

        self.fire(
            log("*** {0:s} has joined {1:s}".format(source[0], channel)),
            "logger.{0:s}".format(channel)
        )

    def part(self, source, channel, reason=None):
        """Part Event

        This event is triggered by the ``IRC`` Protocol Component when a
        user has left a channel.
        """

        self.chanmap[channel].remove(source[0])
        self.nickmap[source[0]].remove(channel)

        self.fire(
            log(
                "*** {0:s} has left {1:s} ({2:s})".format(
                    source[0], channel, reason or ""
                )
            ),
            "logger.{0:s}".format(channel)
        )

    def quit(self, source, message):
        """Quit Event

        This event is triggered by the ``IRC`` Protocol Component when a
        user has quit the network.
        """

        for ircchannel in self.nickmap[source[0]]:
            self.chanmap[ircchannel].remove(source[0])
            self.fire(
                log("*** {0:s} has quit IRC".format(source[0])),
                "logger.{0:s}".format(ircchannel)
            )

        del self.nickmap[source[0]]

    @handler("privmsg", "notice")
    def message(self, source, target, message):
        """Message Event

        This event is triggered by the ``IRC`` Protocol Component for each
        message we receieve from the server.
        """

        # Only log messages to the channel we're on
        if target[0] == "#":
            self.fire(
                log(
                    u"<{0:s}> {1:s}".format(
                        source[0], message
                    )
                ),
                "logger.{0:s}".format(target)
            )


def main():
    opts, args = parse_options()

    host = args[0]
    port = int(args[1]) if len(args) > 1 else 6667

    opts.output = path.abspath(path.expanduser(opts.output))

    # Configure and run the system.
    Bot(host, port, opts=opts).run()


if __name__ == "__main__":
    main()
