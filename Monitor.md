You have perfect jabber server and transports installed, all stuff works, but you have not enough information about current status of a platform?

This page can make your life a bit better.

How to monitor entire system? Better solution is to choose special product for monitoring. For example, [Munin](http://munin.projects.linpro.no/). It's a monitoring application, accessible via web interface with modular architecture.

If your server is ejabberd, you can get [plugin](http://muninexchange.projects.linpro.no/?search&cid=10&pid=103&phid=144) for it. You already can monitor server.

Transport monitoring. I don't found plugins for this, but in most cases it's not a problem. You run transport under separate user, right? Then we can just view statistics for it!

Since 0.8.1b3 PyICQt contains Munin plugins for monitoring of memory consumption and threads counting "out-of-box". You can get them from /tools directory.

How to use:
  * Install Munin :)
  * Put **memory and _threads_** scripts to /usr/share/munin/plugins directory (check your path)
  * Make them executable
  * Create symlinks in /etc/munin/plugins (if you run PyICQt under pyicqt user, names should be a **memory\_pyicqt** and **threads\_pyicqt**)
  * Add to /etc/munin/plugin-conf.d/munin-node file lines:

```
[memory_*]
user root

[threads_*]
user root
```

That's all. Now you should restart munin-node and look result at http://localhost/munin/ (in basic case):

![http://pyicqt.googlecode.com/svn/wiki/img/monitor/memory_pyicqt-week.png](http://pyicqt.googlecode.com/svn/wiki/img/monitor/memory_pyicqt-week.png)

![http://pyicqt.googlecode.com/svn/wiki/img/monitor/threads_pyicqt-week.png](http://pyicqt.googlecode.com/svn/wiki/img/monitor/threads_pyicqt-week.png)