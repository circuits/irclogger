#!/usr/bin/env python

"""IRC Logger Daemon

For usage type:

   ./irclogger.py --help
"""


from socket import gethostname
from optparse import OptionParser
from re import compile as compile_regex
from datetime import date, datetime, timedelta
from os import environ, getcwd, makedirs, path
from time import asctime, localtime, strftime, time

import circuits
from circuits.app import Daemon
from circuits.io import Close, File, Open, Write
from circuits.net.sockets import TCPClient, Connect
from circuits import Component, Event, Debugger, Timer
from circuits.net.protocols.irc import IRC, USER, NICK, JOIN

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
    return path.join(channel, "{0:s}.log".format(channel, strftime("%Y-%m-%d", localtime())))


def parse_logfile(filename):
    match = LOGFILE_REGEX.match(filename)
    return match.groups() if match is not None else "", ""


class Log(Event):
    """Log Event"""


class Rotate(Event):
    """Rotate Event"""


class Logger(File):

    def init(self, *args, **kwargs):
        super(Logger, self).init(*args, **kwargs)

        interval = datetime.fromordinal((date.today() + timedelta(1)).toordinal())
        Timer(interval, Rotate(), self.channel).register(self)

    def rotate(self):
        dirname = path.dirname(self.filename)
        filename = path.basename(self.filename)
        channel, _ = parse_logfile(filename)
        logfile = generate_logfile(channel)
        self.fire(Close(), self.channel)
        self.fire(Open(path.join(dirname, logfile), "a"), self.channel)

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
        self.ircchannels = opts.channels

        # Debugger
        Debugger(events=opts.verbose).register(self)

        # Add TCPClient and IRC to the system.
        self += (TCPClient(channel=self.channel) + IRC(channel=self.channel))

        # Logger(s)
        for ircchannel in self.ircchannels:
            if not path.exists(path.join(opts.output, ircchannel)):
                makedirs(path.join(opts.output, ircchannel))
            Logger(path.join(opts.output, generate_logfile(ircchannel)), "a", channel="logger.{0:s}".format(ircchannel)).register(self)

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

        self.fire(Connect(self.host, self.port))

    def numeric(self, source, target, numeric, args, message):
        """Numeric Event

        This event is triggered by the ``IRC`` Protocol Component when we have
        received an IRC Numberic Event from server we are connected to.
        """

        if numeric == 1:
            for ircchannel in self.ircchannels:
                self.fire(JOIN(ircchannel))
        elif numeric == 433:
            self.nick = newnick = "%s_" % self.nick
            self.fire(NICK(newnick))

    def join(self, source, channel):
        """Join Event

        This event is triggered by the ``IRC`` Protocol Component when a
        user has joined a channel.
        """

        self.fire(Log("[{0:s} has joined {1:s}]".format(source[0], channel)), "logger.{0:s}".format(channel))

    def message(self, source, target, message):
        """Message Event

        This event is triggered by the ``IRC`` Protocol Component for each
        message we receieve from the server.
        """

        # Only log messages to the channel we're on
        if target[0] == "#":
            self.fire(Log("<{0:s}> {1:s}".format(source[0], message)), "logger.{0:s}".format(target))


def main():
    opts, args = parse_options()

    host = args[0]
    port = int(args[1]) if len(args) > 1 else 6667

    opts.output = path.abspath(path.expanduser(opts.output))

    # Configure and run the system.
    Bot(host, port, opts=opts).run()


if __name__ == "__main__":
    main()
