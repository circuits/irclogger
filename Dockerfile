FROM crux/python:onbuild

ENTRYPOINT ["irclogger"]
CMD ["-c", "#circuits", "irc.freenode.net", "6667"]
