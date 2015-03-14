## Introduction ##

Welcome to the online documentation for PyICQt!  This will always be the most up to date documentation available for the transport and, at some point, may replace that which is distributed with the transport altogether.  Multiple authors help to keep this documentation up to date and I expect it to continue improving as time goes on.  If you have external documentation related to the transport, please let us know and we will add a link!  Also do not be afraid to let us know what could be improved!  See BlatherWiki for information on how to contact us.

## Related Links ##
**[Main site](http://pyicq-t.blathersource.org)**

**[Project site](http://www.blathersource.org/project.php?projid=pyicq-t)**

**[ICQ.com](http://www.icq.com/)**

## Features ##

In my neverending quest to make PyICQt feature rich, I'm attempting to put
up a list of currently supported features, and planned features.  Drop me
a note if there is something you would like to have and that is not listed here:

| Feature | Description | Status |
|:--------|:------------|:-------|
| Messaging | Ability to message users on ICQ, and receive messages. | Complete |
| Presence | Ability to see others online, and others to see you. | Complete |
| Group Chat | Ability to join and talk in chat rooms. (IRC based) | Incomplete |
| VCard Support | Ability to request a VCard of an ICQ user. | Complete |
| HTML Messages | Color and fonts in messages. | Complete |
| Buddy Icons | Buddy Icons/Avatars displayed and set. | Complete |
| Typing Notifications | Notifications when typing starts on either end. | Complete |
| New E-mail notifications | Receive notifications when your ICQmail address has new mail. |Incomplete |
| Change ICQ password | Change the password you use to log on to your ICQ account | Incomplete |
| Invisible Presence | Ability to be hidden, but still logged in. | Incomplete<sup>2</sup> |
| Confirm ICQ account | Confirm the number you've entered is actually an ICQ number | Complete |
| Crosschat support | Exchange messages, presence, etc. with AIM users. |Complete |
| File Transfer | Ability to send files between ICQ and Jabber | Incomplete<sup>1</sup> |
| New account registration | Ability to create a new ICQ account | Incomplete<sup>3</sup> |
| Voice chat | Talk with ICQ users using ICQphone or ICQ Voice Chat | Incomplete<sup>4</sup> |
| Video/Voice Messaging | See and talk to other ICQ users | Incomplete<sup>4</sup> |

**1** - [JEP 96](http://www.jabber.org/jeps/jep-0096.html) on file transfers is not finalized yet.

**2** - This may never happen because invisibility in jabber means invisibility from the transport too.

**3** - You can sign up for an ICQ account [here](https://www.icq.com/register/).

**4** - It will probably be difficult to support these. The idea of proxying voice & video using Jingle on the Jabber side also doesn't sound nice.

## Installation ##

### Before You Start ###

Before you install, you need to make sure you have the following things:

**A [Jabber](http://www.jabber.org/) server; Known to work with:**

 [Jabberd 1.\*](http://jabberd.jabberstudio.org/)

 [Jabberd 2.\*](http://jabberd.jabberstudio.org/)

 [Wildfire](http://www.jivesoftware.org/wildfire/)

 [ejabberd](http://ejabberd.jabber.ru/)

**[Python](http://www.python.org/) 2.2.0 or later**

**[Twisted](http://www.twistedmatrix.com/) framework (both 1.** and 2.**series should be fine)**

**Optional: [Nevow](http://www.nevow.org/) for web interface**

**Optional: [epoll](http://msn-transport.jabberstudio.org/?page=downloads) for epoll reactor (Linux 2.6 kernel required)**

**Optional: [mysql-python](http://sourceforge.net/projects/mysql-python) for [mysql](http://www.mysql.org) database backend**

**Optional: [Python Imaging Library (PIL)](http://www.pythonware.com/products/pil/) for avatar support (note _disableAvatars_ option if you don't want them)**

**Optional: [LDAP client API](http://python-ldap.sourceforge.net/) for LDAP authenticated registration support (see _authRegister_ option)**

Also note that there may be tutorials to guide
you through installation and configuration.

If you are planning to use the subversion repository, please note that the Repository is reachable via the subversion protocol, not via http. Make sure that port 3690 is not firewalled.  Alternatively, you can download a tarball of the current repository.

### Transport Configuration ###

After unpacking the distribution, your first task is to create the transport
configuration file.  The easiest way to do this is to copy _config\_example.xml_
from the root of the distribution to _config.xml_ and edit it.
The configuration options should be fairly self explanatory.  However, if you
need some assistance, check out the Configuration section.
If you are upgrading from a previous version, you should always look over _config\_example.xml_ to see added, removed and changed options.

### Spool Setup ###

There are multiple `drivers` for the transport's spool.  The default and most basic is called _xmlfiles_, and it is capable of automatically converting the spool that [JIT](http://jit.jabberstudio.org/) uses.  If you are migrating from an earlier version of the c-based aim transport, you can either point the _spooldir_ variable at the location of the old spool (and make sure to also set _jid_ to the same jid the old transport used), or you can copy of JIT's spool directory to a new location pointed to by _spooldir_/_jid_.  There is also a tool to convert between different spool drivers, including the ability to convert a PyAIMt spool into one compatible with the [c-based aim transport](http://aim-transport.jabberstudio.org) or JIT.  If you are not migrating, simply `mkdir` the spool directory at _spooldir_/_jid_ and make sure the transport will have access to write to it.

The available spool drivers are described as follows:

#### xmlfiles ####

This is the default driver. It stores the spool files in a "hashed directory structure".  The layout is designed to provide fairly good performance.  All files are in XML format and are stored as plain text.  The driver has one option, _format_, which can be set to _encrypted_ to shroud passwords.  See _config\_example.xml_ for an example of how to enable this option.

#### mysql ####

This driver stores the spool inside of a MySQL database.  There is a MySQL Tutorial available that explains how to set up the MySQL database.

#### legacyjittransport ####

This driver stores the spool in the same format [JIT](http://jit.jabberstudio.org/) uses.  _Please note:_ This driver is not intended to be used regularly.  It exists only to allow the Migration Tool to convert between newer spool formats and this spool format at will. If you use this as your driver, a lot of functionality will be lost (e.g. caching of known avatars).

#### legacyaimtransport ####

This driver stores the spool in the same format the [c-based aim transport](http://aim-transport.jabberstudio.org/) does.  _Please note:_ This driver is not intended to be used regularly.  It exists only to allow the Migration Tool to convert between newer spool formats and this spool format at will.  If you use this as your driver, a lot of functionality will be lost (e.g. caching of known avatars).

#### template ####

This driver is not a real driver.  It is a stub that is intended to provide a starting point for anyone wanting to write their own driver for another spool file database format.  If you write such a driver, please submit it back to upstream, it will be included in the main distribution.

If you are migrating from JIT, you can either point the
_spooldir_ variable to the location of JIT's spool
(make sure you also set _jid_ to the same jid that JIT
used), or copy the JIT spool directory to a new location pointed to by
_spooldir_/_jid_.  If you are
migrating from the c-based aim transport, there is a migration script
in tools that can handle reading the old spool format and creating the
new spool format.  Read over the top of the script for instructions.

### Jabberd 2 Setup ###

You can set up the transport for Jabberd 2 in two different ways.  One involves using Jabberd 2's own component protocol and SASL, and the other involves doing very little, but will involve more when chatroom support is added to the transport.

#### Setup using component protocol and SASL ####

To use this setup method, you will need to add a user (or use an existing one) to Jabberd 2's router-users.xml config file.  By default, this file has one use in it named _jabberd_.  While I do not believe you have to, I would recommend that you create a separate user for the transports, like:
```
<user>
  <name>pytransport</name>
  <secret>mysecret</secret>
<user>
```
You will likely need to restart Jabberd 2 at this point.  However, afterwards, you can add _useJ2Component_, set _saslUsername_ to the same _name_ you put in router-users.xml above, and set _secret_ to match _secret_ from router-users.xml in your config.xml file.  The transport should connect to Jabberd 2 and bind as every jid it wishes to be.  (ie, it will bind as _jid_ and _confjid_ from your config.xml file)

#### Setup without component protocol or SASL ####

There is little or nothing you have to do.  Just make sure that the _secret_ is set to something your server is expecting.  Note that this will change at some point when chatroom support is added to the transport.

#### Sample Configuration Files ####

**TODO**:Create sample config files

### Jabberd 1 Setup ###
With Jabberd 1, you need to have something along these lines in your
_jabber.xml_ configuration file, within the _jabber_ section.
```
<service id="icq.myserver.org">
	<accept>
		<ip>127.0.0.1</ip>
		<port>XXXX</port>
		<secret>secret</secret>
	</accept>
</service>
```
Also make sure you have something like this in the _browse_
section:
```
<service type="icq" jid="icq.myserver.org" name="ICQ Transport">
	<ns>jabber:iq:register</ns>
</service>
```

The entry in the browse section is optional - the gateway will work without it, but the users wont be able to see the gateway in the service discovery of your jabber server - the browse section specifies the content of the Service Discovery of your jabber-server.

_Hint:_ The tool "xmllint" (Debian Users: It is contained in the package libxml2-utils) may be used to check the syntax of your xml config file (and even to format it nice, using the --format option).

Make sure that the following configuration options are synced up in both
entries:

| config.xml | <=> | jabber.xml |
|:-----------|:----|:-----------|
| jid | = | id |
| jid | = | host |
| secret | = | secret |
| port | = | port |
After doing all those changes, restart your Jabber server, and start
up PyICQt and you should be good to go.

#### Sample Configuration Files ####

**TODO**: Create sample config files

### Jive Wildfire Setup ###

The first thing you will need to do is to configure Wildfire to accept connections from external components.  To set this up, go into Wildfire's admin (web) console and look for _External Components_.  Once you have opened this category, make sure that _Service Enabled_ is set to _Enabled_.  Make note of the _Port_ and _Default shared secret_ (and maybe change them if you want).  You will use those in the transport _config.xml_ file.  There are more advanced things you can do here as well, but I am not getting into them here.  Once you have everything you want, click _Save Settings_.

After saving your Wildfire settings, edit your transport _config.xml_ (you may need to copy _config\_example.xml_ to _config.xml_ first) and make sure that the _jid_ is set to whatever jid you want the transport to answer as, make sure that the port is set to the same thing you noted from the Wildfire admin console, and make sure _secret_ is the same as the _Default shared secret_ from the Wildfire admin console.  There are plenty of other options in   the transport config file.  I would recommend looking over the entire file and adjusting variables as they seem appropriate.  They should all be explained in the config file, but also here in the online documentation.

After you finish with the config file, you should be able to fire up the transport and after it connects you should see it listed in Wildfire's _Sessions_ tab, under _Component Sessions_.

#### Sample Configuration Files ####

**TODO**: Create sample config files

### Ejabberd Setup ###

Configuring the transport for Ejabberd is similar to Jabberd 1, except that you most likely will not have to restart your jabber server to add the transport.  A detailed tutorial for setting up the transport with Ejabberd is provided [here](http://ejabberd.jabber.ru/pyicqt).  Instead of maintaining similar documentation in two places, we are simply deferring to their documentation.

#### Sample Configuration Files ####

**TODO**: Create sample config files

## Configuration ##

Most of the configuration options available are strictly to configure
interaction between the transport and your Jabber server.  There is a
_config\_example.xml_ file that exists in the
root of the distribution that you can start with.  You
should end up with a _config.xml_ file in the
root of the distribution.  In other words, copy
_config\_example.xml_ to _config.xml_
to get started.  Below are explanations of all of the current configuration
options.

### Options ###

| _jid_ | This is the Jabber ID that you would like to associate with this transport. |
|:------|:----------------------------------------------------------------------------|
| _compjid_ | This is the component Jabber ID of the transport, for XCP clustering. |
| _spooldir_ | This is the location of the spool directory associated with this transport.  This should -not- include the JID as the actual spool used is this config option + "/" + jid. |
| _pid_ | This is the full path to a file you would like to store the transport's PID in. |
| _mainServer_ | This is the hostname/ip address of the Jabber server this transport is to connect to. |
| _mainServerJID_ | This is the jabber id of the Jabber server this transport is to connect to. |
| _website_ | This is the web site that an end user can visit to find informamtion on your Jabber server. |
| _port_ | This is the port over which this transport is to communicate with the Jabber server. |
| _icqServer_ | This is the OSCAR server the transport will connect to. |
| _icqPort_ | This is the port over which the transport will connect with the ICQ/OSCAR servers. |
| _webport_ | This is the port over which the web admin interface is to respond. |
| _secret_ | This is a shared secret between your Jabber server and this transport. |
| _encoding_ | This is the default encoding you want messages to be treated as.  Note that Unicode support nullifies this, but not all ICQ clients support that. |
| _lang_ | This is the default language you would like this transport to us when sending transport-initiated messages back to the user. |
| _socksProxyServer_ | This is the hostname/ip address of a socks5 proxy server that the transport is to connect to AOL's OSCAR servers through. |
| _socksProxyPort_ | This is the port of a socks5 proxy server that the transport is to connect to AOL's OSCAR servers through. |
| _sessionGreeting_ | Set this to a welcome message you want your users to see upon logging in.  Leave blank/unset if you want no welcome message. |
| _registerMessage_ | Set this to a welcome message you want your users to see upon registering with the transport.  Leave blank/unset if you want no welcome message. |
| _crossChat_ | Enable this to permit chatting with ICQ users as well as AIM users. |
| _disableRegister_ | Enable this to disable registration with the transport. |
| _disableAvatars_ | Enable this to disable all avatar support in the transport. |
| _disableDefaultAvatar_ | Enable this to disable use of the default avatars.  (ie, only show avatars if the person actually has one set) |
| _avatarsOnlyOnChat_ | Enable this to only retrieve avatars during a chat session. |
| _~~disableWebPresence~~_ | ~~Enable this to disable web presence indicator.~~ |
| _enableWebPresence_ | Enable web presence indicator.  WARNING: This tends to trigger a lot of ICQ spam. |
| _disableXHTML_ | Enable this to disable all XHTML support. |
| _disableMailNotifications_ | Enable this to disable e-mail notification support. |
| _enableAutoInvite_ | Enable this to trigger the transport to ping all known users upon startup, triggering them to log in if they're available. |
| _admins_ | JIDs listed within this tag will have access to restricted ad-hoc command functionality. |
| _reactor_ | Choose between version low-level reactors that drive the base functionality of the transport.  Choices are: poll, select, kqueue, epoll, and default.   For Linux 2.6, epoll is recommended because it is way faster. Follow [this link](http://www.kegel.com/c10k.html) for (very) verbose information about this subject.  For FreeBSD, kqueue is recommended.  If you explicitly choose default, you will get the default reactor for that OS.  (this is important for Windows)  If you do not specify this variable, the transport will attempt to detect the best option you have available.  Under Windows, this detects the wrong thing, unfortunately. |
| _xdbDriver_ | Choose between various methods of storing the transport's database.  Current choices are: xmlfiles (default), mysql, legacyjittransport (backwards compatibility with JIT), and legacyaimtransport (backwards compatibility with c-based aim-transport).  Note that some drivers have associated configuration options explained in config\_example.xml. |
| _useXCP_ | This enables protocol extensions that Jabber.com's server contains. |
| _saslUsername_ | This, combined with secret, are the credentials that will be used when doing a SASL bind with a Jabber server. |
| _~~useJ2Component~~_ | ~~This enables protocol extensions that the JabberD2 server uses to allow binding as one or more JIDs.~~ |
| _useComponentBinding_ | This causes the transport to bind to whatever JIDs the transport intends to answer as.  This process is explained via [Jabberd2's component protocol](http://jabberd.jabberstudio.org/dev/docs/component.shtml) and will be formed into a forthcoming JEP submission.  Wildfire supports this without SASL whereas Jabberd2 requires SASL (and hence, saslUsername to be set). |
| _messageArchiveJID_ | This enables message archiving ([JEP-0138](http://www.jabber.org/jeps/jep-0136.html)).  Set to the JID of something that implements this protocol. |
| _authRegister_ | This causes the transport to require external authentication before being permitted to register.  Right now, only LDAP is supposed for this functionality.  All of the related fields specified in config\_example.xml are required to be filled out for this functionality to work.  Please note that, to the end user, this will look like they are having to register twice. |

## Tutorials ##

Sometimes helpful folks provide tutorials how to set up PyICQt for
specific situations.  Any tutorials I am made aware of, or that we write up, are
listed below.

**[Configuring PyICQt to work with ejabberd](http://ejabberd.jabber.ru/pyicqt)**

**Configuring PyICQt to use the MySQL XDB backend**

**Configuring PyICQt to be accessible from remote servers**


## Prepackaged versions ##

There is an apt repository which contains all the Python transports for Debian users.
Add this to your /etc/apt/sources.list to use it:

deb http://www.spectron-msim.com/debian/ transports main

deb-src http://www.spectron-msim.com/debian/ transports main

The version of PyICQt there is outdated, a more recent version can be found here:

deb http://vontaene.de/apt/ ./
deb-src http://vontaene.de/apt/ ./

The configuration files will be in /etc/jabber-transports. You'll also need to edit /etc/default/jabber-pyaim to enable the transport.