# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
import legacy
import jabw
import debug
import config
import lang
import stats




def makeSession(pytrans, jabberID, ulang, rosterID):
	""" Tries to create a session object for the corresponding JabberID. Retrieves information
	from XDB to create the session. If it fails, then the user is most likely not registered with
	the transport """
	debug.log("session: makeSession(\"%s\")" % (jabberID))
	if(pytrans.sessions.has_key(jabberID)):
		debug.log("session: makeSession() - removing existing session")
		pytrans.sessions[jabberID].removeMe()
	result = pytrans.registermanager.getRegInfo(jabberID)
	if(result):
		username, password, encoding = result
		return Session(pytrans, jabberID, username, password, encoding, ulang, rosterID)
	else:
		return None



class Session(jabw.JabberConnection):
	""" A class to represent each registered user's session with the legacy network. Exists as long as there
	is a Jabber resource for the user available """
	
	def __init__(self, pytrans, jabberID, username, password, encoding, ulang, rosterID):
		""" Initialises the session object and connects to the legacy network """
		jabw.JabberConnection.__init__(self, pytrans, jabberID)
		debug.log("Session: Creating new session \"%s\"" % (jabberID))
		
		self.pytrans = pytrans
		self.alive = True
		self.ready = False # Only ready when we're logged into the legacy service
		self.jabberID = jabberID # the JabberID of the Session's user
		self.username = username # the legacy network ID of the Session's user
		self.password = password
		self.encoding = encoding
		self.lang = ulang

		if (rosterID.resource == "registered"):
			self.registeredmunge = True
		else:
			self.registeredmunge = False
		
		self.show = None
		self.status = None
		
		self.resourceList = {}
		
		self.legacycon = legacy.LegacyConnection(self.username, self.password, self.encoding, self)
		self.pytrans.legacycon = self.legacycon
		
		if (config.sessionGreeting != ""):
			self.sendMessage(to=self.jabberID, fro=config.jid, body=config.sessiongreeting)
		debug.log("Session: New session created \"%s\" \"%s\" \"%s\" \"%s\"" % (jabberID, username, password, encoding))

		stats.totalsess += 1
		if(len(self.pytrans.sessions)+1 > stats.maxsess):
			stats.maxsess = len(self.pytrans.sessions)+1
		stats.sessionUpdate(self.jabberID, "connections", 1)
	
	def removeMe(self, etype=None, econdition=None, etext=None):
		""" Safely removes the session object, including sending <presence type="unavailable"/> messages for each legacy related item on the user's contact list """
		# Send offline presence to Jabber ID
		# Delete all objects cleanly
		# Remove this Session object from the pytrans
		
		debug.log("Session: Removing \"%s\"" % (self.jabberID))
		
		# Mark as dead
		self.alive = False
		self.ready = False
		
		# Send offline presence to the user
		if(self.pytrans):
			tmpjid = config.jid
			if (self.registeredmunge):
				tmpjid = tmpjid + "/registered"
			if etype:
				ptype = "error"
			else:
				ptype = "unavailable"
			self.sendPresence(to=self.jabberID, fro=tmpjid, ptype=ptype, etype=etype, econdition=econdition, etext=etext)
		
		# Clean up stuff on the legacy service end (including sending offline presences for all contacts)
		if(self.legacycon):
			self.legacycon.removeMe()
			self.legacycon = None
		
		if(self.pytrans):
			# Remove us from the session list
			del self.pytrans.sessions[self.jabberID]
			# Clean up the no longer needed reference
			self.pytrans = None
		
		debug.log("Session: Completed removal \"%s\"" % (self.jabberID))
	
	def setStatus(self, show, status):
		self.show = show
		self.status = status
		self.legacycon.setStatus(show, status)
	
	def sendNotReadyError(self, source, resource, dest, body):
		self.sendErrorMessage(source + '/' + resource, dest, "wait", "not-allowed", lang.get(self.lang).waitforlogin, body)
	
	def messageReceived(self, source, resource, dest, destr, mtype, body):
		if(dest == config.jid):
			if(body.lower().startswith("end")):
				debug.log("Session: Received 'end' request. Killing session %s" % (self.jabberID))
				self.removeMe()
			return

		if(not self.ready):
			self.sendNotReadyError(source, resource, dest, body)
			return
		
		# Sends the message to the legacy translator
		debug.log("Session: messageReceived(), passing onto legacycon.sendMessage()")
		self.legacycon.sendMessage(dest, resource, body)
	
	def typingNotificationReceived(self, dest, resource, composing):
		""" The user has sent typing notification to a contact on the legacy service """
		self.legacycon.userTypingNotification(dest, resource, composing)
	
	def presenceReceived(self, source, resource, to, tor, priority, ptype, show, status):
		# Checks resources and priorities so that the highest priority resource always appears as the
		# legacy services status. If there are no more resources then the session is deleted
		self.handleResourcePresence(source, resource, to, tor, priority, ptype, show, status)

		
	def handleResourcePresence(self, source, resource, to, tor, priority, ptype, show, status):
		if(not ptype in [None, "unavailable"]): return # Ignore presence errors, probes, etc
		if(to.find('@') > 0): return # Ignore presence packets sent to users

		existing = self.resourceList.has_key(resource)
		if(ptype == "unavailable"):
			if(existing):
				debug.log("Session: %s - resource \"%s\" gone offline" % (self.jabberID, resource))
				self.resourceOffline(resource)
			else:
				return # I don't know the resource, and they're leaving, so it's all good
		else:
			if(not existing):
				debug.log("Session %s - resource \"%s\" has come online" % (self.jabberID, resource))
				self.legacycon.newResourceOnline(resource)
			debug.log("Session %s - resource \"%s\" setting \"%s\" \"%s\" \"%s\"" % (self.jabberID, resource, show, status, priority)) 
			self.resourceList[resource] = SessionResource(resource, show, status, priority)

		highestActive = self.highestResource()

		if(highestActive):
			# If we're the highest active resource, we should update the legacy service
			debug.log("Session %s - updating status on legacy service, resource %s" % (self.jabberID, highestActive))
			r = self.resourceList[highestActive]
			self.setStatus(r.show, r.status)
		else:
			debug.log("Session %s - tearing down, last resource gone offline")
			self.removeMe()

	def highestResource(self):
		""" Returns the highest priority resource """
		highestActive = None
		for checkR in self.resourceList.keys():
			if(highestActive == None or self.resourceList[checkR].priority > self.resourceList[highestActive].priority): 
				highestActive = checkR

		if(highestActive):
			debug.log("Session %s - highest active resource is \"%s\" at %d" % (self.jabberID, highestActive, self.resourceList[highestActive].priority))

		return highestActive

	def resourceOffline(self, resource):
		del self.resourceList[resource]
		self.legacycon.resourceOffline(resource)
	
	def subscriptionReceived(self, to, subtype):
		""" Sends the subscription request to the legacy services handler """
		debug.log("Session: \"%s\" subscriptionReceived(), passing onto legacycon.jabberSubscriptionReceived()" % (self.jabberID))
		self.legacycon.jabberSubscriptionReceived(to, subtype)
	








class SessionResource:
	""" A convienence class to allow comparisons of Jabber resources """
	def __init__(self, resource, show=None, status=None, priority=None):
		self.resource = resource
		self.show = show
		self.status = status
		self.priority = 0
		try:
			self.priority = int(priority)
		except: pass
	
	def __eq__(self, other):
		if(other):
			return (self.resource == other.resource)
		else:
			return False
	
	def __ne__(self, other):
		if(other):
			return (self.resource != other.resource)
		else:
			return False
	
	def __cmp__(self, other):
		if(other):
			return self.priority.__cmp__(other.priority)
		else:
			return 1
