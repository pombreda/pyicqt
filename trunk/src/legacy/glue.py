# Copyright 2004 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

from tlib import oscar

import utils
if(utils.checkTwisted()):
	from twisted.xish.domish import Element
else:
	from tlib.domish import Element

import icqt
import config
import debug
import lang
import base64

# The name of the transport
name = "ICQ Transport"

# The transport's version
version = "0.6"

# This should be set to the identity of the gateway
id = "icq"

# Set to True if spool directory entries need to be mangled @ -> %
mangle = True

# This should be set to the name space roster entries are in in the spool
namespace = "jabber:iq:register"

# Helper functions to encrypt and decrypt passwords
def encryptPassword(password):
	return base64.encodestring(password)

def decryptPassword(password):
	return base64.decodestring(password)

# This function should return an xml element as it should exist in the spool
def formRegEntry(username, password, encoding):
	reginfo = Element((None,"query"))
	reginfo.attributes["xmlns"] = "jabber:iq:register"

	userEl = reginfo.addElement("username")
	userEl.addContent(username)

	if config.encryptSpool:
		passEl = reginfo.addElement("encryptedpassword")
		passEl.addContent(encryptPassword(password))
	else:
		passEl = reginfo.addElement("password")
		passEl.addContent(password)

	encEl = reginfo.addElement("encoding")
	encEl.addContent(encoding)

	return reginfo

# This function should, given a spool xml entry, pull the username and password
# out of it and return them
def getAttributes(base):
	username = ""
	password = ""
	encoding = ""
	for child in base.elements():
		try:
			if(child.name == "username"):
				username = child.__str__()
			elif(child.name == "password"):
				password = child.__str__()
			elif(child.name == "encryptedpassword"):
				password = decryptPassword(child.__str__())
			elif(child.name == "encoding"):
				encoding = child.__str__()
		except AttributeError:
			continue

	return username, password, encoding

# This function translates an ICQ screen name to a JID
def icq2jid(icqid):
	if (icqid):
		retstr = icqid.replace(' ', '')
		return retstr.replace('@', '%') + "@" + config.jid
	else:
		return config.jid

# This function translates a JID to an ICQ screen name
def jid2icq(jid):
	return unicode(jid[:jid.find('@')].replace('%', '@'))

# This function is called to handle legacy id translation to a JID
translateAccount = icq2jid

# This class handles most interaction with the legacy protocol
class LegacyConnection(icqt.ICQConnection):
	""" A glue class that connects to the legacy network """
	def __init__(self, username, password, encoding, session):
		debug.log("LegacyConnection: __init__")
		self.session = session
		self.savedShow = None
		self.savedFriendly = None
		icqt.ICQConnection.__init__(self, username, password, encoding)
	
	def removeMe(self, etype=None, econdition=None, etext=None):
		debug.log("LegacyConnection: removeMe")
		icqt.ICQConnection.removeMe(self, etype, econdition, etext)
	
	def jidRes(self, resource):
		to = self.session.jabberID
		if(resource):
			to += "/" + resource
		return to

	def highestResource(self):
		""" Returns highest priority resource """
		return self.session.highestResource()

	def sendMessage(self, dest, resource, body):
		debug.log("LegacyConnection: sendMessage %s %s %s" % (dest, resource, body))
		icqt.ICQConnection.sendMessage(self, dest, body)

	def newResourceOnline(self, resource):
		debug.log("LegacyConnection: newResourceOnline %s" % (resource))
		icqt.ICQConnection.resendBuddies(self, resource)
	
 	def setStatus(self, show, friendly):
		debug.log("LegacyConnection: setStatus %s %s" % (show, friendly))

		self.savedShow = show
		self.savedFriendly = friendly

		try:
			if (show in ["online", "Online", None]):
				icqt.ICQConnection.setICQStatus(self, show)
				icqt.ICQConnection.setAway(self)
				self.session.sendPresence(to=self.session.jabberID, fro=config.jid, show=None)
			else:
				icqt.ICQConnection.setICQStatus(self, show)
				icqt.ICQConnection.setAway(self, friendly)
				self.session.sendPresence(to=self.session.jabberID, fro=config.jid, show=show, status=friendly)
		except AttributeError:
			self.session.sendMessage(to=self.session.jabber.ID, fro=config.jid, body=lang.get(config.lang).sessionnotactive, mtype="error")

        def buildFriendly(self, status):
		friendly = self.jabberID[:self.jabberID.find('@')]
		if(status and len(status) > 0):
			friendly += " - "
			friendly += status
		if(len(friendly) > 127):
			friendly = friendly[:124] + "..."
		debug.log("Session: buildFriendly(%s) returning \"%s\"" % (self.jabberID, friendly))
		return friendly
	
	def jabberSubscriptionReceived(self, source, subtype):
		debug.log("LegacyConnection: jabberSubscriptionReceived %s %s" % (source, subtype))
		icqt.ICQConnection.jabberSubscriptionReceived(self, source, subtype)

	def userTypingNotification(self, dest, resource, composing):
		debug.log("LegacyConnection: userTypingNotification %s %s" % (dest,composing))
		if (composing):
			icqt.ICQConnection.sendTypingNotify(self, "begin", dest)
		else:
			icqt.ICQConnection.sendTypingNotify(self, "finish", dest)

	def jabberVCardRequest(self, vcard, user):
		debug.log("LegacyConnection: jabberVCardRequest %s" % (user))
		return icqt.ICQConnection.getvCard(self, vcard, user)

	def resourceOffline(self, resource):
		debug.log("LegacyConnection: resourceOffline %s" % (resource))
		icqt.ICQConnection.removeResource(self, resource)
		self.session.sendPresence(to=self.session.jabberID+"/"+resource, fro=config.jid, ptype="unavailable")
