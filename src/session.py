# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
import legacy
import jabw
import debug
import config
import lang




def makeSession(pytrans, jabberID, ulang):
	""" Tries to create a session object for the corresponding JabberID. Retrieves information
	from XDB to create the session. If it fails, then the user is most likely not registered with
	the transport """
	debug.log("session: makeSession(\"%s\")" % (jabberID))
	if(pytrans.sessions.has_key(jabberID)):
		debug.log("session: makeSession() - removing existing session")
		pytrans.sessions[jabberID].removeMe()
	result = pytrans.registermanager.getRegInfo(jabberID)
	if(result):
		username, password, nickname = result
		return Session(pytrans, jabberID, username, password, nickname, ulang)
	else:
		return None



class Session(jabw.JabberConnection):
	""" A class to represent each registered user's session with the legacy network. Exists as long as there
	is a Jabber resource for the user available """
	
	def __init__(self, pytrans, jabberID, username, password, nickname, ulang):
		""" Initialises the session object and connects to the legacy network """
		jabw.JabberConnection.__init__(self, pytrans, jabberID)
		debug.log("Session: Creating new session \"%s\"" % (jabberID))
		
		self.pytrans = pytrans
		self.alive = True
		self.ready = False # Only ready when we're logged into the legacy service
		self.jabberID = jabberID # the JabberID of the Session's user
		self.username = username # the legacy network ID of the Session's user
		self.password = password
		self.nickname = nickname
		self.lang = ulang
		
		self.show = None
		self.status = None
		
		self.resourceList = []
		self.groupchats = []
		
		self.legacycon = legacy.LegacyConnection(self.username, self.password, self)
		self.pytrans.legacycon = self.legacycon
		
		if(config.sessionGreeting):
			self.sendMessage(to=self.jabberID, fro=config.jid, body=lang.get(self.lang).sessionGreeting)
		debug.log("Session: New session created \"%s\" \"%s\" \"%s\" \"%s\"" % (jabberID, username, password, nickname))
	
	
	def removeMe(self):
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
			self.sendPresence(to=self.jabberID, fro=config.jid, ptype="unavailable")
		
		# Clean up stuff on the legacy service end (including sending offline presences for all contacts)
		if(self.legacycon):
			self.legacycon.removeMe()
			self.legacycon = None
		
		# Remove any groupchats we may be in
		for groupchat in utils.copyList(self.groupchats):
			groupchat.removeMe()
		
		if(self.pytrans):
			# Remove us from the session list
			del self.pytrans.sessions[self.jabberID]
			# Clean up the no longer needed reference
			self.pytrans = None
		
		debug.log("Session: Completed removal \"%s\"" % (self.jabberID))
	
	def updateNickname(self, nickname):
		self.nickname = nickname
		self.setStatus(self.show, self.status)
	
	def setStatus(self, show, status):
		self.show = show
		self.status = status
		self.legacycon.setStatus(show, status)
	
	def sendNotReadyError(self, source, resource, dest, body):
		self.sendErrorMessage(source + '/' + resource, dest, "wait", "not-allowed", lang.get(self.lang).waitForLogin, body)
	
	def findGroupchat(self, to):
		pos = to.find('@')
		if(pos > 0):
			roomID = to[:pos]
		else:
			roomID = to
		
		for groupchat in self.groupchats:
			if(groupchat.ID == roomID):
				return groupchat
		
		return None
		
	def messageReceived(self, source, resource, dest, destr, mtype, body):
		if(not self.ready):
			self.sendNotReadyError(source, resource, dest, body)
			return
		
		# Sends the message to the legacy translator
		groupchat = self.findGroupchat(dest)
		if(groupchat):
			# It's for a groupchat
			if(destr and len(destr) > 0):
				self.sendMessage(to=(source + "/" + resource), fro=dest, body=lang.get(self.lang).groupchatPrivateError)
			else:
				debug.log("Session: Message received for groupchat \"%s\" \"%s\"" % (self.jabberID, groupchat.ID))
				groupchat.sendMessage(body)
		else:
			debug.log("Session: messageReceived(), passing onto legacycon.sendMessage()")
			self.legacycon.sendMessage(dest, body)
	
	def inviteReceived(self, source, resource, dest, destr, roomjid):
		if(not self.ready):
			self.sendNotReadyError(source, resource, dest, roomjid)
			return
		
		groupchat = self.findGroupchat(roomjid)
		if(groupchat):
			debug.log("Session: inviteReceived(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (source, resource, dest, destr, roomjid))
			groupchat.sendContactInvite(dest)
	
	def presenceReceived(self, source, resource, to, tor, priority, ptype, show, status):
		# Checks resources and priorities so that the highest priority resource always appears as the
		# legacy services status. If there are no more resources then the session is deleted
		# Additionally checks if the presence is to a groupchat room
		groupchat = self.findGroupchat(to)
		if(groupchat):
			# It's for a groupchat
			if(ptype == "unavailable"):
				# Kill the groupchat
				debug.log("Session: Presence received to kill groupchat \"%s\" \"%s\"" % (self.jabberID, groupchat.ID))
				groupchat.removeMe()
			else:
				if(source == self.jabberID):
					debug.log("Session: Presence for groupchat \"%s\" \"%s\"" % (self.jabberID, groupchat.ID))
					if(ptype == "error"):
						groupchat.removeMe()
					else:
						groupchat.userJoined(tor)
				else:
					debug.log("Session: Sending error presence for groupchat (user not allowed) \"%s\" \"%s\"" % (self.jabberID, groupchat.ID))
					self.sendPresence(to=(source + "/" + resource), fro=to, ptype="error")
		
		elif(legacy.isGroupJID(to) and to != config.jid and ptype != "error"):
			# It's a new groupchat
			gcID = to[:to.find('@')] # Grab the room name
			debug.log("Session: Creating a new groupchat \"%s\" \"%s\"" % (self.jabberID, gcID))
			groupchat = legacy.LegacyGroupchat(self, resource, gcID) # Creates an empty groupchat
			groupchat.userJoined(tor)
		
		else:
			# Not for groupchat
			self.handleResourcePresence(source, resource, to, tor, priority, ptype, show, status)

		
	def handleResourcePresence(self, source, resource, to, tor, priority, ptype, show, status):
		if(to.find('@') > 0): return # Ignore presence packets sent to users
		r = SessionResource(resource, show, status, priority)
		if(ptype == None):
			# Check to see if this is a new resource, if so, send out the contact list
			debug.log("Session: Presence change received \"%s\"" % (self.jabberID))
			if(self.resourceList.count(r) == 0):
				debug.log("Session: New resource online \"%s\" \"%s\" \"%s\"" % (self.jabberID, resource, priority))
				self.legacycon.newResourceOnline(resource)
			
			# We must check the resource and priority, only interested in the highest priority
			higher = False
			oldList = utils.copyList(self.resourceList)
			self.resourceList = []
			for checkR in oldList:
				if(checkR > r):
					higher = True
				if(checkR == r):
					self.resourceList.append(r)
				else:
					self.resourceList.append(checkR)
			if(self.resourceList.count(r) == 0):
				self.resourceList.append(r) # Make sure it's in there
			
			if(not higher):
				# No higher resource was found. So we must be the highest!
				# This means we must update the presence on the legacy network
				debug.log("Session: \"%s\" Updating status on legacy network \"%s\" \"%s\"" % (self.jabberID, show, status))
				self.setStatus(show, status)
		
		elif(ptype == "unavailable"):
			# This resource has gone offline, so we need to remove it from the list, and find the next highest
			# resource to use to update our status on the legacy network
			debug.log("Session: Unavailable presence received from \"%s\". Looking for other resources" % (self.jabberID))
			lst = utils.copyList(self.resourceList)
			self.resourceList = []
			for i in lst:
				if(r != i):
					self.resourceList.append(i)
			
			highest = None
			for checkR in self.resourceList:
				if(checkR > highest): # comparisons against None are always True
					highest = checkR
			if(highest == None):
				# There are no resources left, so offline this session
				debug.log("Session: No resources left \"%s\"" % (source))
				self.removeMe()
			else:
				# Update the legacy network's status with the highest leftover resource
				debug.log("Session: New resource \"%s\" found for session \"%s\"" % (highest.resource, self.jabberID))
				self.setStatus(highest.show, highest.status)
	
	
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
