# This file contains options to be configured by the server administrator.

# The JabberID of the transport.
jid = "icq.myserver.org"

# The location of the spool directory.. if relative, relative to the src dir.
# Do not include the jid of the transport.
spooldir = ".."

# The location of the PID file.. if relative, relative to the src dir.
pid = "../PyICQt.pid"

# The IP address of the main Jabberd server
mainServer = "127.0.0.1"

# The TCP port to connect to the Jabber server on (this is the default for Jabberd2)
port = "5347"

# The TCP port that the web admin interface will answer on (leave empty to disable)
webport = "12345"

# The authentication token to use when connecting to the Jabber server
secret = "password"

# The authentication token to use when connection to the web interface
websecret = "webpass"

# The default language to use for informational and error messages
lang = "en"

# The default message encoding to use
encoding = "windows-1251"

# Send greeting on login
sessionGreeting = True

# Allow users of ICQ gateway to chat with AIM users
crossChat = True

# Set this to True to get debugging output
debugOn = False

# Set the debug log file location here, (leave blank to output to the screen)
debugLog = ""
