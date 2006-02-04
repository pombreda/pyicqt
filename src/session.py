# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import config
import utils
import legacy
import jabw
import contact
import avatar
import debug
import lang
from tlib.twistwrap import jid



def makeSession(pytrans, jabberID, ulang, rosterID):
	""" Tries to create a session object for the corresponding JabberID. Retrieves information
	from XDB to create the session. If it fails, then the user is most likely not registered with
	the transport """
	debug.log("Session: makeSession(\"%s\")" % (jabberID))
	if pytrans.sessions.has_key(jabberID):
		debug.log("Session: makeSession() - removing existing session")
		pytrans.sessions[jabberID].removeMe()
	result = pytrans.xdb.getRegistration(jabberID)
	if result:
		username, password = result
		return Session(pytrans, jabberID, username, password, ulang, rosterID)
	else:
		return None



class Session(jabw.JabberConnection):
	""" A class to represent each registered user's session with the legacy network. Exists as long as there
	is a Jabber resource for the user available """
	
	def __init__(self, pytrans, jabberID, username, password, ulang, rosterID):
		""" Initialises the session object and connects to the legacy network """
		jabw.JabberConnection.__init__(self, pytrans, jabberID)
		debug.log("Session: Creating new session \"%s\"" % (jabberID))
		
		self.pytrans = pytrans
		self.alive = True
		self.ready = False # Only ready when we're logged into the legacy service
		self.jabberID = jabberID # the JabberID of the Session's user
		self.username = username # the legacy network ID of the Session's user
		self.password = password
		self.nickname = ""
		self.description = ""
		self.avatar = None
		self.lang = ulang

		if rosterID.resource == "registered":
			self.registeredmunge = True
		else:
			self.registeredmunge = False

		self.show = None
		self.status = None
		self.url = None
		
		self.resourceList = {}
		self.capabilities = []
		
		self.contactList = contact.ContactList(self)
		self.legacycon = legacy.LegacyConnection(self.username, self.password, self)
		self.pytrans.legacycon = self.legacycon
		self.contactList.legacyList = self.legacycon.legacyList

		if config.sessionGreeting:
			self.sendMessage(to=self.jabberID, fro=config.jid, body=config.sessionGreeting)
		self.updateNickname("")
		self.updateDescription("")
		self.doVCardUpdate()
		debug.log("Session: New session created \"%s\" \"%s\" \"%s\"" % (jabberID, username, password))

		self.pytrans.statistics.stats["TotalSessions"] += 1
		self.pytrans.statistics.stats["OnlineSessions"] += 1
		if len(self.pytrans.sessions)+1 > self.pytrans.statistics.stats["MaxConcurrentSessions"]:
			self.pytrans.statistics.stats["MaxConcurrentSessions"] = len(self.pytrans.sessions)+1
		self.pytrans.statistics.sessionUpdate(self.jabberID, "Connections", 1)
	
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
		if self.pytrans:
			tmpjid = config.jid
			if self.registeredmunge:
				tmpjid = tmpjid + "/registered"
			self.sendPresence(to=self.jabberID, fro=tmpjid, ptype="unavailable")
			self.pytrans.statistics.stats["OnlineSessions"] -= 1

		# Clean up stuff on the legacy service end (including sending offline presences for all contacts)
		if self.legacycon:
			self.legacycon.removeMe()
			self.legacycon = None

		if self.contactList:
			self.contactList.removeMe()
			self.contactList = None

		if self.pytrans:
			# Remove us from the session list
			del self.pytrans.sessions[self.jabberID]
			# Clean up the no longer needed reference
			self.pytrans = None
		
		debug.log("Session: Completed removal \"%s\"" % (self.jabberID))

	def doVCardUpdate(self):
		def vCardReceived(el):
			if not self.alive: return
			debug.log("Session %s - Got user's vCard" % (self.jabberID))
			vCard = None
			for e in el.elements():
				if e.name == "vCard" and e.defaultUri == "vcard-temp":
					vCard = e
					break
			else:
				self.legacycon.updateAvatar() # Default avatar
				return
			avatarSet = False
			for e in vCard.elements():
				if e.name == "DESC":
					self.updateDescription(e.__str__())
				if e.name == "NICKNAME":
					self.updateNickname(e.__str__())
				if e.name == "PHOTO":
					imageData = avatar.parsePhotoEl(e)
					if not imageData:
						errback() # Possibly it wasn't in a supported format?
					self.avatar = self.pytrans.avatarCache.setAvatar(imageData)
					self.legacycon.updateAvatar(self.avatar)
					avatarSet = True
			if not avatarSet:
				self.legacycon.updateAvatar() # Default avatar

		def errback(args=None):
			debug.log("Session %s - error fetching avatar from vCard" % (self.jabberID))
			self.legacycon.updateAvatar()

		debug.log("Session %s - Fetching user's vCard" % (self.jabberID))
		d = self.sendVCardRequest(to=self.jabberID, fro=config.jid)
		d.addCallback(vCardReceived)
		d.addErrback(errback)

	def updateNickname(self, nickname):
		self.nickname = nickname
		if not self.nickname:
			j = jid.JID(self.jabberID)
			self.nickname = j.user
		self.setStatus(self.show, self.status, self.url)

	def updateDescription(self, description):
		self.description = description
		if not self.description:
			self.description = "I am a PyICQ-t user with no profile set."

	def setStatus(self, show, status, url=None):
		self.show = show
		self.status = status
		self.url = url
		self.legacycon.setStatus(self.nickname, show, status, url)
	
	def sendNotReadyError(self, source, resource, dest, body):
		self.sendErrorMessage(source + '/' + resource, dest, "wait", "not-allowed", lang.get("waitforlogin", self.lang), body)
	
	def nicknameReceived(self, source, dest, nickname):
		if dest.find('@') > 0: return # Ignore presence packets sent to users
        
		self.updateNickname(nickname)

	def avatarHashReceived(self, source, dest, avatarHash):
		if dest.find('@') > 0: return # Ignore presence packets sent to users

		if avatarHash == " ": # Setting no avatar
			self.legacycon.updateAvatar() # Default
		elif not self.avatar or (self.avatar and self.avatar.getImageHash() != avatarHash):
			imageData = self.pytrans.avatarCache.getAvatar(avatarHash)
			if imageData:
				self.avatar = avatar.Avatar(imageData) # Stuff in the cache is always PNG
				self.legacycon.updateAvatar(self.avatar)
			else:
				self.doVCardUpdate()

	def messageReceived(self, source, resource, dest, destr, mtype, body, noerror, xhtml, autoResponse=0):
		if dest == config.jid:
			if body.lower().startswith("end"):
				debug.log("Session: Received 'end' request. Killing session %s" % (self.jabberID))
				self.removeMe()
			return

		if not self.ready:
			self.sendNotReadyError(source, resource, dest, body)
			return
		
		debug.log("Session: messageReceived(), passing onto legacycon.sendMessage()")
		self.legacycon.sendMessage(dest, resource, body, noerror, xhtml, autoResponse=autoResponse)
	
	def typingNotificationReceived(self, dest, resource, composing):
		""" The user has sent typing notification to a contact on the legacy service """
		self.legacycon.userTypingNotification(dest, resource, composing)

	def chatStateReceived(self, dest, resource, state):
		""" The user has sent a chat state notification to a contact on the legacy service """
		self.legacycon.chatStateNotification(dest, resource, state)
	
	def presenceReceived(self, source, resource, to, tor, priority, ptype, show, status, url=None):
		# Checks resources and priorities so that the highest priority resource always appears as the
		# legacy services status. If there are no more resources then the session is deleted
		self.handleResourcePresence(source, resource, to, tor, priority, ptype, show, status, url)

		
	def handleResourcePresence(self, source, resource, to, tor, priority, ptype, show, status, url):
		if ptype and ptype != "unavailable": return # Ignore presence errors, probes, etc
		if to.find('@') > 0: return # Ignore presence packets sent to users

		existing = self.resourceList.has_key(resource)
		if ptype == "unavailable":
			if existing:
				debug.log("Session: %s - resource \"%s\" gone offline" % (self.jabberID, resource))
				self.resourceOffline(resource)
			else:
				return # I don't know the resource, and they're leaving, so it's all good
		else:
			if not existing:
				debug.log("Session %s - resource \"%s\" has come online" % (self.jabberID, resource))
				self.contactList.resendLists("%s/%s"%(source,resource))
			debug.log("Session %s - resource \"%s\" setting \"%s\" \"%s\" \"%s\"" % (self.jabberID, resource, show, status, priority)) 
			self.resourceList[resource] = SessionResource(show, status, priority, url)

		highestActive = self.highestResource()

		if highestActive:
			# If we're the highest active resource, we should update the legacy service
			debug.log("Session %s - updating status on legacy service, resource %s" % (self.jabberID, highestActive))
			r = self.resourceList[highestActive]
			self.setStatus(r.show, r.status, r.url)
		else:
			debug.log("Session %s - calling removeMe in 0 seconds. Last resource gone offline" % (self.jabberID))
			#reactor.callLater(0, self.removeMe)
			self.removeMe()
			#FIXME Which of the above?

	def highestResource(self):
		""" Returns the highest priority resource """
		highestActive = None
		for checkR in self.resourceList.keys():
			if highestActive == None or self.resourceList[checkR].priority > self.resourceList[highestActive].priority: 
				highestActive = checkR

		if highestActive:
			debug.log("Session %s - highest active resource is \"%s\" at %d" % (self.jabberID, highestActive, self.resourceList[highestActive].priority))

		return highestActive

	def resourceOffline(self, resource):
		del self.resourceList[resource]
		self.legacycon.resourceOffline(resource)

	def subscriptionReceived(self, to, subtype):
		""" Sends the subscription request to the legacy services handler """
		if to.find('@') > 0:
			debug.log("Session: \"%s\" subscriptionReceived(), passing onto contactList.jabberSubscriptionReceived()" % (self.jabberID))
			self.contactList.jabberSubscriptionReceived(to, subtype)
		else:
			if subtype == "subscribe":
				self.sendPresence(to=self.jabberID, fro=config.jid, ptype="subscribed")
			elif subtype.startswith("unsubscribe"):
				# They want to unregister.
				jid = self.jabberID
				debug.log("Session: \"%s\" is about to be unregistered" % (jid))
				self.pytrans.registermanager.removeRegInfo(jid)
				debug.log("Session: \"%s\" is has been unregistered" % (jid))




class SessionResource:
	""" A convienence class to allow comparisons of Jabber resources """
	def __init__(self, show=None, status=None, priority=None, url=None):
		self.show = show
		self.status = status
		self.priority = 0
		self.url = url
		try:
			self.priority = int(priority)
		except TypeError: pass
		except ValueError: pass
