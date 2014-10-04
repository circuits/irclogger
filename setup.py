#!/usr/bin/env python


from setuptools import setup, find_packages


version = "0.0.2"
url = "https://bitbucket.org/prologic/irclogger"
download_url = "{0:s}/get/{0:s}.zip".format(version)


setup(
    name="irclogger",
    version=version,
    description="Python IRC Logger Daemon",
    long_description="{0:s}\n\n{1:s}".format(
        open("README.rst", "r").read(),
        open("CHANGES.rst", "r").read()
    ),
    author="James Mills",
    author_email="James Mills, prologic at shortcircuit dot net dot au",
    url=url,
    download_url=download_url,
    classifiers=[],
    license="MIT",
    keywords="Python IRC Logger Daemon",
    platforms="POSIX",
    packages=find_packages("."),
    install_requires=[
        "circuits",
    ],
    entry_points={
        "console_scripts": [
            "irclogger=irclogger.main:main"
        ]
    }
)
