[![Stories in Ready](https://badge.waffle.io/circuits/irclogger.png?label=ready&title=Ready)](https://waffle.io/circuits/irclogger?utm_source=badge)
[![Image Layers](https://badge.imagelayers.io/circuits/irclogger:latest.svg)](https://imagelayers.io/?images=circuits/irclogger:latest)

irclogger is a simple daemon written in the [Python Programming Language](http://www.python.org/) utilizing the [circuits](http://pypi.python.org/pypi/circuits) framework for the sole purpose of logging a set of IRC Channels to disk in the form that something like [irclog2html](http://pypi.python.org/pypi/irclog2html) can understand and parse.

Installation
============

From PyPi using pip:

    $ pip install irclogger

from source:

    $ mkvirtualenv irclogger
    $ hg clone https://bitbucket.org/prologic/irclogger
    $ cd irclogger
    $ pip install -r requirements.txt

Usage
=====

To display help:

    $ irclogger --help

    Usage: irclogger [options] <host> [<port>]

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -d, --daemon          Enable daemon mode
      -c CHANNELS, --channel=CHANNELS
                            Channel to join (multiple allowed)
      -n NICK, --nick=NICK  Nickname to use
      -o OUTPUT, --output=OUTPUT
                            Path to store log files
      -p PIDFILE, --pidfile=PIDFILE
                            Path to store PID file
      -v, --verbose         Enable verbose debugging mode

To log a single channel:

    $ irclogger -c "#mychannel" irc.freenode.net

> **note**
>
> By default irclogger stores logs in the current working directory.  
> Use `-o/--output` to change the location to store log files.
>
> **note**
>
> Also note that the default nickname used is your current username  
> on your system. i.e: `$USER`. To change this use the `-n/--nick` option.
>

