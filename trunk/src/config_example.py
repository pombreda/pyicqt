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

# The authentication token to use when connecting to the Jabber server
secret = "password"

# The default language to use
lang = "en"

# Send greeting on login
sessionGreeting = False

# Set this to True to get debugging output
debugOn = True

# Set the debug log file location here, (leave blank to output to the screen)
debugLog = ""
