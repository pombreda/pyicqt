# Introduction #

You want to set up your own PyICQt installation, but don't know which should be first step? I hope this page can help to make it.


# Details #

1. Installation of the transport requires machine with some software.
Minimal requirements:
  * Python - 2.4
  * Twisted - 2.5
Recommended requirements:
  * OS - Linux
  * Python - 2.5
  * Twisted - 8.1
Work of the transport can be unstable under Python =< 2.3, stable under 2.6 (tested without high loads). For supporting of Python 3.0 changes necessary.

2. Then jabber server is needed. I use [ejabberd](http://ejabberd.im), but you can choose any one from 10+, listed on [this page](http://xmpp.org/software/servers.shtml). Documentation for server comes with it.

3. PyICQt itself can be downloaded from this site (see [Downloads](http://code.google.com/p/pyicqt/downloads/list) section) or pulled from your distribution repository.

4. Configure interaction between server and transport (manual for ejabberd can be found [here](http://www.ejabberd.im/pyicqt))

5. Done? Now restart them and try to connect to your own jabber server with [jabber client](http://www.jabber.org/web/Clients) and make service discovery. If you see transport and it responses on yours requests - configuration was successful

6. No more installation steps. Only documentation [for users](http://code.google.com/p/pyicqt/wiki/UserStartPage)

# Other? #
  * [OnlineDocumentation](OnlineDocumentation.md) - more comprehensive documentation, but partially out-of-date
  * [Monitor](Monitor.md) - monitoring of a transport state
  * [Upgrade](Upgrade.md) - updating from previous PyICQt's version