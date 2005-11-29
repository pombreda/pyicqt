# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
if utils.checkTwisted():
	from twisted.xish.domish import Element
	from twisted.words.protocols.jabber import jid
else:
	from tlib.domish import Element
	from tlib.jabber import jid

import session
import legacy
import debug
import lang
import jabw
import config
import globals

class RegisterManager:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		if not config.disableRegister:
			self.pytrans.discovery.addFeature("jabber:iq:register", self.incomingRegisterIq, config.jid)
		debug.log("RegisterManager: Created")
	
	def removeRegInfo(self, jabberID):
		debug.log("RegisterManager: removeRegInfo(\"%s\")" % (jabberID))
		try:
			# If the session is active then send offline presences
			session = self.pytrans.sessions[jabberID]
			session.removeMe()
		except KeyError:
			pass
		
		self.pytrans.xdb.removeRegistration(jabberID)
		debug.log("RegisterManager: removeRegInfo(\"%s\") - done" % (jabberID))
	
	
	#def setRegInfo(self, jabberID, username, password):
	#	debug.log("RegisterManager: setRegInfo(\"%s\", \"%s\", \"%s\")" % (jabberID, username, password))
	#	if(len(password) == 0):
	#		(blah1, password, blah3) = self.getRegInfo(jabberID)

	#	reginfo = legacy.formRegEntry(username, password)
	#	self.pytrans.xdb.set(jid.JID(jabberID).full(), legacy.namespace, reginfo)
	
	#def getRegInfo(self, jabberID):
	#	debug.log("RegisterManager: getRegInfo(\"%s\")" % (jabberID))
	#	#result = self.pytrans.xdb.request(jid.JID(jabberID).full(), legacy.namespace)
	#	result = self.pytrans.xdb.request(jid.JID(jabberID).userhost(), legacy.namespace)
	#	if(result == None):
	#		debug.log("RegisterManager: getRegInfo(\"%s\") - not registered!" % (jabberID))
	#		return None
	#	
	#	username, password = legacy.getAttributes(result)
	#	
	#	if(username and password and len(username) > 0 and len(password) > 0):
	#		debug.log("RegisterManager: getRegInfo(\"%s\") - returning reg info \"%s\" \"%s\"!" % (jabberID, username, password))
	#		return (username, password)
	#	else:
	#		debug.log("RegisterManager: getRegInfo(\"%s\") - invalid registration data! %s %s" % (jabberID, username, password))
	#		return None
	
	def incomingRegisterIq(self, incoming):
		# Check what type the Iq is..
		itype = incoming.getAttribute("type")
		debug.log("RegisterManager: In-band registration type \"%s\" received" % (itype))
		if(itype == "get"):
			self.sendRegistrationFields(incoming)
		elif(itype == "set"):
			self.updateRegistration(incoming)
		
	def sendRegistrationFields(self, incoming):
		# Construct a reply with the fields they must fill out
		debug.log("RegisterManager: sendRegistrationFields() for \"%s\" \"%s\"" % (incoming.getAttribute("from"), incoming.getAttribute("id")))
		reply = Element((None, "iq"))
		reply.attributes["from"] = config.jid
		reply.attributes["to"] = incoming.getAttribute("from")
		reply.attributes["id"] = incoming.getAttribute("id")
		reply.attributes["type"] = "result"
		query = reply.addElement("query")
		query.attributes["xmlns"] = "jabber:iq:register"
		instructions = query.addElement("instructions")
		ulang = utils.getLang(incoming)
		instructions.addContent(lang.get("registertext", ulang))
		userEl = query.addElement("username")
		passEl = query.addElement("password")
		
		# Check to see if they're registered
		source = jid.JID(incoming.getAttribute("from")).userhost()
		result = self.pytrans.xdb.getRegistration(source)
		if(result):
			username, password = result
			userEl.addContent(username)
			query.addElement("registered")
		
		self.pytrans.send(reply)
	
	def updateRegistration(self, incoming):
		# Grab the username and password
		debug.log("RegisterManager: updateRegistration() for \"%s\" \"%s\"" % (incoming.getAttribute("from"), incoming.getAttribute("id")))
		source = jid.JID(incoming.getAttribute("from")).userhost()
		ulang = utils.getLang(incoming)
		username = None
		password = None
		
		for queryFind in incoming.elements():
			if(queryFind.name == "query"):
				for child in queryFind.elements():
					try:
						if(child.name == "username"):
							username = child.__str__().lower()
						elif(child.name == "password"):
							password = child.__str__()
						elif(child.name == "remove"):
							# The user wants to unregister the transport! Gasp!
							debug.log("RegisterManager: Session \"%s\" is about to be unregistered" % (source))
							try:
								self.removeRegInfo(source)
								self.successReply(incoming)
							except:
								self.xdbErrorReply(incoming)
								return
							debug.log("RegisterManager: Session \"%s\" has been unregistered" % (source))
							return
					except AttributeError, TypeError:
						continue # Ignore any errors, we'll check everything below
		
		if(username and password and len(username) > 0 and len(password) > 0):
			# Valid registration data
			debug.log("RegisterManager: Valid registration data was received. Attempting to update XDB")
			try:
				self.pytrans.xdb.setRegistration(source, username, password)
				debug.log("RegisterManager: Updated XDB successfully")
				self.successReply(incoming)
				debug.log("RegisterManager: Sent off a result Iq")
				(user, host, res) = jid.parse(incoming.getAttribute("from"))
				debug.log("RegisterManager: Sending subscribe presence %s@%s/%s %s" % (user, host, res, config.jid))
				jabw.sendPresence(self.pytrans, to=user + "@" + host, fro=config.jid, ptype="subscribe")
				if(config.registerMessage):
					jabw.sendMessage(self.pytrans, to=incoming.getAttribute("from"), fro=config.jid, body=config.registerMessage)
			except:
				self.xdbErrorReply(incoming)
				raise
		
		else:
			self.badRequestReply(incoming)
	
	def badRequestReply(self, incoming):
		debug.log("RegisterManager: Invalid registration data was sent to us. Or the removal failed.")
		# Send an error Iq
		reply = incoming
		reply.swapAttributeValues("to", "from")
		reply.attributes["type"] = "error"
		error = reply.addElement("error")
		error.attributes["type"] = "modify"
		interror = error.addElement("bad-request")
		interror["xmlns"] = globals.XMPP_STANZAS
		self.pytrans.send(reply)
	
	def xdbErrorReply(self, incoming):
		debug.log("RegisterManager: Failure in updating XDB or sending result Iq")
		# send an error Iq
		reply = incoming
		reply.swapAttributeValues("to", "from")
		reply.attributes["type"] = "error"
		error = reply.addElement("error")
		error.attributes["type"] = "wait"
		interror = error.addElement("internal-server-error")
		interror["xmlns"] = globals.XMPP_STANZAS
		self.pytrans.send(reply)
	
	def successReply(self, incoming):
		reply = Element((None, "iq"))
		reply.attributes["type"] = "result"
		ID = incoming.getAttribute("id")
		if(ID): reply.attributes["id"] = ID
		reply.attributes["from"] = config.jid
		reply.attributes["to"] = incoming.getAttribute("from")
		self.pytrans.send(reply)

