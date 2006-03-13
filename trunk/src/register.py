# Copyright 2004-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from tlib.twistwrap import Element, jid
import session
import legacy
from debug import LogEvent, INFO, WARN, ERROR
import lang
import jabw
import config
import globals

class RegisterManager:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		if not config.disableRegister:
			self.pytrans.discovery.addFeature(globals.IQREGISTER, self.incomingRegisterIq, config.jid)
		LogEvent(INFO)
	
	def removeRegInfo(self, jabberID):
		LogEvent(INFO)
		try:
			# If the session is active then send offline presences
			session = self.pytrans.sessions[jabberID]
			session.removeMe()
		except KeyError:
			pass
		
		self.pytrans.xdb.removeRegistration(jabberID)
		LogEvent(INFO, "", "done")
	
	
	def incomingRegisterIq(self, incoming):
		# Check what type the Iq is..
		itype = incoming.getAttribute("type")
		LogEvent(INFO)
		if(itype == "get"):
			self.sendRegistrationFields(incoming)
		elif(itype == "set"):
			self.updateRegistration(incoming)
		
	def sendRegistrationFields(self, incoming):
		# Construct a reply with the fields they must fill out
		LogEvent(INFO)
		reply = Element((None, "iq"))
		reply.attributes["from"] = config.jid
		reply.attributes["to"] = incoming.getAttribute("from")
		reply.attributes["id"] = incoming.getAttribute("id")
		reply.attributes["type"] = "result"
		query = reply.addElement("query")
		query.attributes["xmlns"] = globals.IQREGISTER
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
		LogEvent(INFO)
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
							LogEvent(INFO, "", "Unregistering")
							try:
								self.removeRegInfo(source)
								self.successReply(incoming)
							except:
								self.xdbErrorReply(incoming)
								return
							LogEvent(INFO, "", "Unregistered!")
							return
					except AttributeError, TypeError:
						continue # Ignore any errors, we'll check everything below
		
		if(username and password and len(username) > 0 and len(password) > 0):
			# Valid registration data
			LogEvent(INFO, "", "Updating XDB")
			try:
				self.pytrans.xdb.setRegistration(source, username, password)
				LogEvent(INFO, "", "Updated XDB")
				self.successReply(incoming)
				LogEvent(INFO, "", "Sent a result Iq")
				(user, host, res) = jid.parse(incoming.getAttribute("from"))
				jabw.sendPresence(self.pytrans, to=user + "@" + host, fro=config.jid, ptype="subscribe")
				if(config.registerMessage):
					jabw.sendMessage(self.pytrans, to=incoming.getAttribute("from"), fro=config.jid, body=config.registerMessage)
			except:
				self.xdbErrorReply(incoming)
				raise
		
		else:
			self.badRequestReply(incoming)
	
	def badRequestReply(self, incoming):
		LogEvent(INFO)
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
		LogEvent(INFO)
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

