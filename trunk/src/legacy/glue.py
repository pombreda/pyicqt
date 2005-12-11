# Copyright 2004 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
if utils.checkTwisted():
	from twisted.xish.domish import Element
else:
	from tlib.domish import Element
from twisted.internet import task
from tlib import oscar
import groupchat
import icqt
import config
import debug
import base64

# The name of the transport
name = "ICQ Transport"

# The transport's version
version = "0.6"

# URL of the transport's web site
url = "http://pyicq-t.blathersource.org"

# This should be set to the identity of the gateway
id = "icq"

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

	return username, password[:8], encoding

# This function should return true if the JID is a group JID, false otherwise
def isGroupJID(jid):
	#if (jid[0] == "#" or jid[0] == "%"):
	if jid.find(config.confjid) > 0:
		return True
	else:
		return False

# This function translates an ICQ screen name to a JID
def icq2jid(icqid):
	if icqid:
		retstr = icqid.lower().replace(' ', '')
		return retstr.replace('@', '%') + "@" + config.jid
	else:
		return config.jid

# This function translates a JID to an ICQ screen name
def jid2icq(jid):
	return unicode(jid[:jid.find('@')].replace('%','@'))

# This function translates an ICQ chat room to a groupchat JID
def icq2jidGroup(chatid, userid=None, exchange=None):
	retstr = chatid.replace(' ', '_')
	retstr = retstr.replace('@', '')
	if exchange:
		retstr = retstr + "%" + str(exchange)
	retstr = retstr + "@" + config.confjid
	if userid:
		retstr = retstr + "/" + userid
	return retstr

# This function translates a groupchat JID to an ICQ chat room
def jid2icqGroup(jid):
	exchange = 4
	groupid = unicode(jid[0:jid.find('@')].replace('_',' '))
	if groupid.find('%') != -1:
		exchange = int(groupid[groupid.find('%')+1:])
		groupid = groupid[:groupid.find('%')]
	if jid.find('/') != -1:
		userid = unicode(jid[jid.find('/'):])
	else:
		userid = None
	return (groupid,userid,exchange)

# This function is called to handle legacy id translation to a JID
translateAccount = icq2jid

def startStats(statistics):
	""" Fills the misciq.Statistics class with the statistics fields.
	You must put a command_OnlineUsers and command_OnlineUsers_Desc
	attributes into the lang classes for this to work.
	Note that OnlineUsers is a builtin stat. You don't need to
	reimplement it yourself. """
	pass

def updateStats(statistics):
	""" This will get called regularly. Use it to update any global
	statistics """
	pass

def addCommands(pytrans):
	""" This function is expected to create handlers for legacy
	specific ad-hoc commands, and set them up with disco as
	appropriate """
	import legacyiq
	pytrans.ICQEmailLookup = legacyiq.EmailLookup(pytrans)
	pytrans.ICQConfirmAccount = legacyiq.ConfirmAccount(pytrans)

# This class handles groupchats with the legacy protocol
class LegacyGroupchat(groupchat.BaseGroupchat):
	def __init__(self, session, resource, ID=None, existing=False, switchboardSession=None):
		groupchat.BaseGroupchat.__init__(self, session, resource, ID)
		groupid,userid,exchange = jid2icqGroup(self.roomJID())
		debug.log("LegacyGroupchat: \"%s\" \"%s\" created" % (self.roomJID(), groupid))
		self.session.legacycon.createChat(groupid,exchange)

	def removeMe(self):
		groupid,userid,exchange = jid2icqGroup(self.roomJID())
		debug.log("LegacyGroupchat: remove \"%s\" \"%s\"" % (self.roomJID(), groupid))
		self.session.legacycon.leaveChat(groupid)
		groupchat.BaseGroupchat.removeMe(self)
		utils.mutilateMe(self)

	def sendLegacyMessage(self, message, noerror):
		groupid,userid,exchange = jid2icqGroup(self.roomJID())
		debug.log("LegacyGroupchat: send message \"%s\" \"%s\" \"%s\"" % (self.roomJID(), groupid, message))
		self.session.legacycon.sendChat(groupid, message)
	
	def sendContactInvite(self, contactJID):
		groupid,userid,exchange = jid2icqGroup(self.roomJID())
		contactid = jid2icq(contactJID)
		debug.log("LegacyGroupchat: send invite \"%s\" \"%s\" \"%s\" \"%s\"" % (self.roomJID(), contactJID, groupid, contactid))
		self.session.legacycon.sendInvite(groupid, contactid)

# This class handles most interaction with the legacy protocol
class LegacyConnection(icqt.ICQConnection):
	""" A glue class that connects to the legacy network """
	def __init__(self, username, password, session):
		debug.log("LegacyConnection: __init__")
		self.session = session
		self.savedShow = None
		self.savedFriendly = None
		icqt.ICQConnection.__init__(self, username, password)

		import legacylist
		self.legacyList = legacylist.LegacyList(self.session)
	
	def removeMe(self):
		debug.log("LegacyConnection: removeMe")
		icqt.ICQConnection.removeMe(self)
		self.legacyList.removeMe()
		self.legacyList = None
		self.session = None
		utils.mutilateMe(self)

	def jidRes(self, resource):
		to = self.session.jabberID
		if resource:
			to += "/" + resource
		return to

	def highestResource(self):
		""" Returns highest priority resource """
		return self.session.highestResource()

	def sendMessage(self, dest, resource, body, noerror, xhtml):
		debug.log("LegacyConnection: sendMessage %s %s %s" % (dest, resource, body))
		icqt.ICQConnection.sendMessage(self, dest, body, xhtml)

	def newResourceOnline(self, resource):
		debug.log("LegacyConnection: newResourceOnline %s" % (resource))
		icqt.ICQConnection.resendBuddies(self, resource)
	
 	def setStatus(self, nickname, show, friendly):
		debug.log("LegacyConnection: setStatus %s %s" % (show, friendly))

		if show=="away" and not friendly:
			friendly="Away"
		elif show=="dnd" and not friendly:
			friendly="Do Not Disturb"
		elif show=="xa" and not friendly:
			friendly="Extended Away"
		elif show=="chat" and not friendly:
			friendly="Free to Chat"

		self.savedShow = show
		self.savedFriendly = friendly

		if not self.session.ready:
			return

		if not show or show == "online" or show == "Online" or show == "chat":
			icqt.ICQConnection.setICQStatus(self, show)
			icqt.ICQConnection.setAway(self)
			self.session.sendPresence(to=self.session.jabberID, fro=config.jid, show=None)
		else:
			icqt.ICQConnection.setICQStatus(self, show)
			icqt.ICQConnection.setAway(self, friendly)
			self.session.sendPresence(to=self.session.jabberID, fro=config.jid, show=show, status=friendly)

        def buildFriendly(self, status):
		friendly = self.jabberID[:self.jabberID.find('@')]
		if status and len(status) > 0:
			friendly += " - "
			friendly += status
		if len(friendly) > 127:
			friendly = friendly[:124] + "..."
		debug.log("Session: buildFriendly(%s) returning \"%s\"" % (self.jabberID, friendly))
		return friendly
	
	def userTypingNotification(self, dest, resource, composing):
		debug.log("LegacyConnection: userTypingNotification %s %s" % (dest,composing))
		if composing:
			icqt.ICQConnection.sendTypingNotify(self, "begin", dest)
		else:
			icqt.ICQConnection.sendTypingNotify(self, "finish", dest)

	def chatStateNotification(self, dest, resource, state):
		debug.log("LegacyConnection: chatStateNotification %s %s" % (dest,state))
		if state == "composing":
			icqt.ICQConnection.sendTypingNotify(self, "begin", dest)
		elif state == "paused" or state == "inactive":
			icqt.ICQConnection.sendTypingNotify(self, "idle", dest)
		elif state == "active" or state == "gone":
			icqt.ICQConnection.sendTypingNotify(self, "finish", dest)
		pass

	def jabberVCardRequest(self, vcard, user):
		debug.log("LegacyConnection: jabberVCardRequest %s" % (user))
		return icqt.ICQConnection.getvCard(self, vcard, user)

	def createChat(self, chatroom, exchange):
		debug.log("LegacyConnection: createChat %s %d" % (chatroom, exchange))
		icqt.ICQConnection.createChat(self, chatroom, exchange)

	def leaveChat(self, chatroom):
		debug.log("LegacyConnection: leaveChat %s" % (chatroom))
		icqt.ICQConnection.leaveChat(self, chatroom)

	def sendChat(self, chatroom, message):
		debug.log("LegacyConnection: sendChat %s %s" % (chatroom, message))
		icqt.ICQConnection.sendChat(self, chatroom, message)

	def sendInvite(self, chatroom, contact):
		debug.log("LegacyConnection: sendInvite %s %s" % (chatroom, contact))
		icqt.ICQConnection.sendInvite(self, chatroom, contact)

	def resourceOffline(self, resource):
		debug.log("LegacyConnection: resourceOffline %s" % (resource))
		icqt.ICQConnection.resourceOffline(self, resource)

	def updateAvatar(self, av=None):
		""" Called whenever a new avatar needs to be set. Instance of avatar.Avatar is passed """
		imageData = ""
		if av:
			imageData = av.getImageData()
		else:
			f = open("legacy/defaultJabberAvatar.png")
			imageData = f.read()
			f.close()

		icqt.ICQConnection.changeAvatar(self, imageData)

	def doSearch(self, form, iq):
		debug.log("LegacyConnection: doSearch")
		return icqt.ICQConnection.doSearch(self, form, iq)
