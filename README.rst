.. _Python Programming Language: http://www.python.org/
.. _circuits: http://pypi.python.org/pypi/circuits
.. _irclog2html: http://pypi.python.org/pypi/irclog2html

.. image:: https://badge.imagelayers.io/prologic/irclogger:latest.svg
   :target: https://imagelayers.io/?images=prologic/irclogger:latest
   :alt: Image Layers

irclogger is a simple daemon written in the `Python Programming Language`_ utilizing the `circuits`_ framework for the sole purpose of logging a set of IRC
Channels to disk in the form that something like `irclog2html`_ can understand and parse.


Installation
------------

From PyPi using pip:

::
    
    $ pip install irclogger

from source:

::
    
    $ mkvirtualenv irclogger
    $ hg clone https://bitbucket.org/prologic/irclogger
    $ cd irclogger
    $ pip install -r requirements.txt


Usage
-----

To display help:

::
    
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

::
    
    $ irclogger -c "#mychannel" irc.freenode.net

.. note:: By default irclogger stores logs in the current working directory.
          Use ``-o/--output`` to change the location to store log files.

.. note:: Also note that the default nickname used is your current username
          on your system. i.e: ``$USER``. To change this use the ``-n/--nick``
          option.
