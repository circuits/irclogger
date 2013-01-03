#!/usr/bin/env python

import os
from glob import glob
from distutils.util import convert_path

from setuptools import setup


def find_packages(where=".", exclude=()):
    """Borrowed directly from setuptools"""

    out = []
    stack = [(convert_path(where), "")]
    while stack:
        where, prefix = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if ("." not in name and os.path.isdir(fn) and
                    os.path.isfile(os.path.join(fn, "__init__.py"))):
                out.append(prefix + name)
                stack.append((fn, prefix + name + "."))

    from fnmatch import fnmatchcase
    for pat in list(exclude) + ["ez_setup"]:
        out = [item for item in out if not fnmatchcase(item, pat)]

    return out

path = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(path, "README.rst")).read()
    RELEASE = open(os.path.join(path, "RELEASE.rst")).read()
except IOError:
    README = RELEASE = ""

import irclogger

setup(
    name=irclogger.__name__,
    version=irclogger.__version__,
    description=irclogger.__doc__.split()[0],
    long_description="%s\n\n%s" % (README, RELEASE),
    author="James Mills",
    author_email="James Mills, prologic at shortcircuit dot net dot au",
    url="TBA",
    download_url="TBA",
    classifiers=[],
    license="MIT",
    keywords="Python IRC Logger Daemon",
    platforms="POSIX",
    packages=find_packages("."),
    scripts=glob("scripts/*"),
    install_requires=[
        "circuits",
    ],
    entry_points={
        "console_scripts": [
            "irclogger=irclogger.main:main"
        ]
    },
    zip_safe=False
)
