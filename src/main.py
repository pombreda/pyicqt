# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import sys
reload(sys)
sys.setdefaultencoding('iso-8859-1')
del sys.setdefaultencoding

from twisted.internet import reactor
from twisted.web import proxy, server
from tlib.jabber import component, jid
from tlib.domish import Element
from twisted.internet import task
import twisted.python.log
from nevow import appserver

import os
import types
import xdb
import session
import jabw
import disco
import register
import misciq
import utils
import legacy
import config
import lang
import debug
import webadmin

#import gc
#gc.set_debug(gc.DEBUG_COLLECTABLE | gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_INSTANCES | gc.DEBUG_OBJECTS)



class PyTransport(component.Service):
	def __init__(self):
		debug.log("PyTransport: Service starting up")
		self.xdb = xdb.XDB(config.jid, legacy.mangle)
		self.registermanager = register.RegisterManager(self)
		self.gatewayTranslator = misciq.GatewayTranslator(self)
		
		# Discovery, as well as some builtin features
		self.discovery = disco.Discovery(self)
		self.discovery.addIdentity("gateway", legacy.id, legacy.name)
		if (legacy.confid and legacy.confid != ""):
			self.discovery.addIdentity("conference", legacy.confid, legacy.name + " Chatrooms")
			self.discovery.addFeature("http://jabber.org/protocol/muc", None) # So that clients know you can create groupchat rooms on the server
		self.discovery.addFeature("jabber:iq:register", self.registermanager.incomingRegisterIq)
		self.discovery.addFeature("jabber:iq:gateway", self.gatewayTranslator.incomingIq)
		
		self.xmlstream = None
		self.sessions = {}
		
		# Groupchat ID handling
		self.lastID = 0
		self.reservedIDs = []

		# Statistics
		self.stats = { }
		self.stats['incmessages'] = 0
		self.stats['outmessages'] = 0
		self.stats['totalsess'] = 0
		self.stats['maxsess'] = 0

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
	
	def makeID(self):
		newID = "r" + str(self.lastID)
		self.lastID += 1
		if(self.reservedIDs.count(newID) > 0):
			# Ack, it's already used.. Try again
			return self.makeID()
		else:
			return newID
	
	def reserveID(self, ID):
		self.reservedIDs.append(ID)
	
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
	
	def componentDisconnected(self):
		debug.log("PyTransport: Disconnected from main Jabberd server")
		self.xmlstream = None
	
	def onMessage(self, el):
		fro = el.getAttribute("from")
		froj = jid.JID(fro.lower())
		to = el.getAttribute("to")
		if(to.find('@') < 0): return
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
			jabw.sendErrorMessage(self, fro, to, "auth", "forbidden", lang.get(ulang).notLoggedIn, body)
	
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
						jabw.sendMessage(self, to=froj.userhost(), fro=config.jid, body=lang.get(ulang).notRegistered)
				
				elif(ptype != "error"):
					debug.log("PyTransport: Sending unavailable presence to non-logged in user \"%s\"" % (froj.userhost()))
					el.swapAttributeValues("from", "to")
					el.attributes["type"] = "unavailable"
					self.send(el)
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
		self.c = component.buildServiceManager(config.jid, config.secret, "tcp:%s:%s" % (config.mainServer, config.port))
		self.transportSvc = PyTransport()
		self.transportSvc.setServiceParent(self.c)
		self.c.startService()
		reactor.addSystemEventTrigger('before', 'shutdown', self.shuttingDown)

		# Create a PID file
		pid = str(os.getpid())
		pf = file(config.pid,'w')
		pf.write("%s\n" % pid);
		pf.close()

	
	def shuttingDown(self):
		self.transportSvc.removeMe()
		os.remove(config.pid)



if(__name__ == "__main__"):
	#import tests.runtests
	#debug.log("Twisted test cases passed successfully.")
	app = App()

	if (hasattr(config, "webport") and config.webport):
		site = appserver.NevowSite(webadmin.WebAdmin(pytrans=app.transportSvc))
		reactor.listenTCP(int(config.webport), site)
	reactor.run()
