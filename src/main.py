# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import debug
import getopt
import sys
import os
reload(sys)
sys.setdefaultencoding('iso-8859-1')
del sys.setdefaultencoding

name = "PyICQt"
exe = os.path.realpath(sys.executable)
if (exe.find("python") >= 0):
	print("Restarting with process name %s..." % (name))
	os.execv(exe, [name, sys.argv[0]]+sys.argv[1:])

import config
import xmlconfig
conffile = "config.xml"
options = {}
opts, args = getopt.getopt(sys.argv[1:], "c:o:dDl:h", ["config=", "option=", "debug", "Debug", "log=", "help"])
for o, v in opts:
	if o in ("-c", "--config"):
		conffile = v
	elif o in ("-d", "--debug"):
		config.debugOn = True
	elif o in ("-D", "--Debug"):
		config.debugOn = True
		config.extendedDebugOn = True
	elif o in ("-l", "--log"):
		config.debugLog = v
	elif o in ("-o", "--option"):
		var, setting = v.split("=", 2)
		options[var] = setting
	elif o in ("-h", "--help"):
		print "./PyICQt [options]"
		print "   -h                  print this help"
		print "   -c <file>           read configuration from this file"
		print "   -d                  print debugging output"
		print "   -l <file>           write debugging output to file"
		print "   -o <var>=<setting>  set config var to setting"
		os._exit(0)
reload(debug)

if (config.extendedDebugOn):
	from twisted.python import log
	if (debug.debugFile):
		log.startLogging(debug.debugFile, 0)
	else:
		log.startLogging(sys.stdout, 0)
xmlconfig.Import(conffile, options)
 
def reloadConfig(a, b):
	# Reload default config and then process conf file
	reload(config)
	xmlconfig.Import(conffile, None)

# Set SIGHUP to reload the config file
if (os.name == "posix"):
	import signal
	signal.signal(signal.SIGHUP, reloadConfig)

from twisted.internet import reactor
from twisted.web import proxy, server
from tlib.jabber import component, jid
from tlib.domish import Element
from tlib.xmlstream import STREAM_ERROR_EVENT,STREAM_END_EVENT
from twisted.internet import task
import twisted.python.log

import types
import xdb
import session
import jabw
import disco
import register
import misciq
import utils
import legacy
import lang

class PyTransport(component.Service):
	def __init__(self):
		debug.log("PyTransport: Service starting up")
		
		# Discovery, as well as some builtin features
		self.discovery = disco.Discovery(self)
		self.discovery.addIdentity("gateway", legacy.id, legacy.name)

		self.xdb = xdb.XDB(config.jid, legacy.mangle)
		if(not config.disableRegister):
			self.registermanager = register.RegisterManager(self)
		self.gatewayTranslator = misciq.GatewayTranslator(self)
		self.versionTeller = misciq.VersionTeller(self)
		
		self.xmlstream = None
		self.sessions = {}
		
		# Message IDs
		self.messageID = 0
		
		self.loopCheckSessions = task.LoopingCall(self.loopCheckSessionsCall)
		self.loopCheckSessions.start(60.0) # call every ten seconds
		
		# Display active sessions if debug mode is on
		if(config.debugOn):
			self.loop = task.LoopingCall(self.loopCall)
			self.loop.start(60.0) # call every 60 seconds
			twisted.python.log.addObserver(self.exceptionLogger)

	def removeMe(self):
		debug.log("PyTransport: Service shutting down")
		dic = utils.copyDict(self.sessions)
		for session in dic:
			dic[session].removeMe()

	def exceptionLogger(self, *kwargs):
		if(len(config.debugLog) > 0):
			kwargs = kwargs[0]
			if(kwargs.has_key("failure")):
				failure = kwargs["failure"]
				failure.printTraceback(debug) # Pass debug as a pretend file object because it implements the write method
				if(config.debugLog):
					print "Exception occured! Check the log!"

	def makeMessageID(self):
		self.messageID += 1
		return str(self.messageID)
	
	def loopCall(self):
		if(len(self.sessions) > 0):
			debug.log("Sessions:")
			for key in self.sessions:
				debug.log("\t" + self.sessions[key].jabberID)
	
	def loopCheckSessionsCall(self):
		if(len(self.sessions) > 0):
			oldDict = utils.copyDict(self.sessions)
			self.sessions = {}
			for key in oldDict:
				session = oldDict[key]
				if(not session.alive):
					debug.log("Ghost session %s found. This shouldn't happen. Trace" % (session.jabberID))
					# Don't add it to the new dictionary. Effectively removing it
				else:
					self.sessions[key] = session
	
	def componentConnected(self, xmlstream):
		debug.log("PyTransport: Connected to main Jabberd server")
		self.xmlstream = xmlstream
		self.xmlstream.addObserver("/iq", self.discovery.onIq)
		self.xmlstream.addObserver("/presence", self.onPresence)
		self.xmlstream.addObserver("/message", self.onMessage)
		#self.xmlstream.addObserver("/error[@xmlns='http://etherx.jabber.org/streams']", self.streamError)
		self.xmlstream.addObserver(STREAM_ERROR_EVENT, self.streamError)
		self.xmlstream.addObserver(STREAM_END_EVENT, self.streamEnd)

	def componentDisconnected(self):
		debug.log("PyTransport: Disconnected from main Jabberd server")
		# Is this proper?  I mean we were disconnected but we're
		# sending this anyway?  Hrm..  it does work, which is a
		# little odd.
		if (self.sessions):
			sessionkeys = self.sessions.keys()
			for s in sessionkeys:
				self.sessions[s].removeMe()
		self.xmlstream = None

	def streamError(self, errelem):
		debug.log("PyTransport: Received stream error")
		self.xmlstream.streamError(errelem)

	def streamEnd(self, errelem):
		debug.log("PyTransport: Received stream end")
		pass
	
	def onMessage(self, el):
		fro = el.getAttribute("from")
		froj = jid.JID(fro.lower())
		to = el.getAttribute("to")
		#if(to.find('@') < 0): return
		mtype = el.getAttribute("type")
		ulang = utils.getLang(el)
		body = None
		for child in el.elements():
			if(child.name == "body"):
				body = child.__str__()
		if(self.sessions.has_key(froj.userhost())):
			self.sessions[froj.userhost()].onMessage(el)
		elif(mtype != "error"):
			debug.log("PyTrans: Sending error response to a message outside of session.")
			jabw.sendErrorMessage(self, fro, to, "auth", "forbidden", lang.get(ulang).notloggedin, body)
	
	def onPresence(self, el):
		fro = el.getAttribute("from")
		ptype = el.getAttribute("type")
		froj = jid.JID(fro.lower())
		to = el.getAttribute("to")
		toj = jid.JID(to.lower())
		ulang = utils.getLang(el)
		debug.log("PyTransport: onPresence type %s from %s to %s" % (ptype, fro, to))
		if(self.sessions.has_key(froj.userhost())):
			self.sessions[froj.userhost()].onPresence(el)
		else:
			if(to.find('@') < 0):
				# If the presence packet is to the transport (not a user) and there isn't already a session
				if(ptype == "subscribe"):
					debug.log("PyTransport: Answering subscription request")
					el.swapAttributeValues("from", "to")
					el.attributes["type"] = "subscribed"
					self.send(el)
				elif(ptype in [None, ""]): # Don't create a session unless they're sending available presence
					debug.log("PyTransport: Attempting to create a new session \"%s\"" % (froj.userhost()))
					s = session.makeSession(self, froj.userhost(), ulang, toj)
					if(s):
						self.sessions[froj.userhost()] = s
						debug.log("PyTransport: New session created \"%s\"" % (froj.userhost()))
						# Send the first presence
						s.onPresence(el)
					else:
						debug.log("PyTransport: Failed to create session \"%s\"" % (froj.userhost()))
						jabw.sendMessage(self, to=froj.userhost(), fro=config.jid, body=lang.get(ulang).notregistered)
				
				elif(ptype != "error"):
					debug.log("PyTransport: Sending unavailable presence to non-logged in user \"%s\"" % (froj.userhost()))
					#el.swapAttributeValues("from", "to")
					#el.attributes["type"] = "unavailable"
					#self.send(el)
					pres = Element((None, "presence"))
					pres.attributes["from"] = to
					pres.attributes["to"] = fro
					pres.attributes["type"] = "unavailable"
					self.send(pres)
					return
			
			elif(ptype in ["subscribe", "subscribed", "unsubscribe", "unsubscribed"]):
				# They haven't logged in, and are trying to change subscription to a user
				# Lets log them in and then do it
				debug.log("PyTransport: Attempting to create a session to do subscription stuff %s" % (froj.userhost()))
				s = session.makeSession(self, froj.userhost(), ulang, toj)
				if(s):
					self.sessions[froj.userhost()] = s
					debug.log("PyTransport: New session created \"%s\"" % (froj.userhost()))
					# Tell the session there's a new resource
					s.handleResourcePresence(froj.userhost(), froj.resource, toj.userhost(), toj.resource, 0, None, None, None)
					# Send this subscription
					s.onPresence(el)

class App:
	def __init__(self):
		# Check that there isn't already a PID file
		if(os.path.isfile(utils.doPath(config.pid))):
			print "PID file exists at that location. Please check for running PyICQt and try again."
			sys.exit(1)

		# Create a PID file
		pid = str(os.getpid())
		pf = file(utils.doPath(config.pid),'w')
		pf.write("%s\n" % pid);
		pf.close()

		self.c = component.buildServiceManager(config.jid, config.secret, "tcp:%s:%s" % (config.mainServer, config.port))
		self.transportSvc = PyTransport()
		self.transportSvc.setServiceParent(self.c)
		self.c.startService()
		reactor.addSystemEventTrigger('before', 'shutdown', self.shuttingDown)
	
	def shuttingDown(self):
		self.transportSvc.removeMe()
		os.remove(utils.doPath(config.pid))



if(__name__ == "__main__"):
	app = App()
	if (hasattr(config, "webport") and config.webport):
		try:
			from nevow import appserver
			import webadmin
			site = appserver.NevowSite(webadmin.WebAdmin(pytrans=app.transportSvc))
			reactor.listenTCP(int(config.webport), site)
			debug.log("Web admin interface activated.")
		except:
			debug.log("Unable to start web admin interface.  No Nevow package found.")
	reactor.run()
