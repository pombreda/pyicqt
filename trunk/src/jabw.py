# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.xish.domish import Element
#from twisted.protocols.jabber.jid import JID
from tlib.jabber.jid import JID
import utils
import debug


def sendMessage(pytrans, to, fro, body, mtype=None):
	""" Sends a Jabber message """
	debug.log("jabw: Sending a Jabber message \"%s\" \"%s\" \"%s\" \"%s\"" % (to, fro, utils.latin1(body), mtype))
	el = Element((None, "message"))
	el.attributes["to"] = to
	el.attributes["from"] = fro
	el.attributes["id"] = pytrans.makeMessageID()
	if(mtype):
		el.attributes["type"] = mtype
	b = el.addElement("body")
	b.addContent(body)
	x = el.addElement("x")
	x.attributes["xmlns"] = "jabber:x:event"
	composing = x.addElement("composing")
	pytrans.send(el)

def sendPresence(pytrans, to, fro, show=None, status=None, priority=None, ptype=None):
	el = Element((None, "presence"))
	el.attributes["to"] = to
	el.attributes["from"] = fro
	if(ptype):
		el.attributes["type"] = ptype
	if(show):
		s = el.addElement("show")
		s.addContent(show)
	if(status):
		s = el.addElement("status")
		s.addContent(status)
	if(priority):
		s = el.addElement("priority")
		s.addContent(priority)
	pytrans.send(el)


def sendErrorMessage(pytrans, to, fro, etype, eelement, econtent, body=None):
	el = Element((None, "message"))
	el.attributes["to"] = to
	el.attributes["from"] = fro
	el.attributes["type"] = "error"
	error = el.addElement("error")
	error.attributes["type"] = etype
	desc = error.addElement(eelement)
	desc.attributes["xmlns"] = "urn:ietf:params:xml:ns:xmpp-stanzas"
	text = error.addElement("text")
	text.attributes["xmlns"] = "urn:ietf:params:xml:ns:xmpp-stanzas"
	text.addContent(econtent)
	if(body and len(body) > 0):
		b = el.addElement("body")
		b.addContent(body)
	pytrans.send(el)




class JabberConnection:
	""" A class to handle a Jabber "Connection", ie, the Jabber side of the gateway.
	If you want to send a Jabber event, this is the place, and this is where incoming
	Jabber events for a session come to. """
	
	def __init__(self, pytrans, jabberID):
		self.pytrans = pytrans
		self.jabberID = jabberID
		self.typingUser = False # Whether this user can accept typing notifications
		self.messageIDs = dict() # The ID of the last message the user sent to a particular contact. Indexed by contact JID
		debug.log("User: %s - JabberConnection constructed" % (self.jabberID))
	
	def removeMe(self):
		""" Cleanly deletes the object """
		debug.log("User: %s - JabberConnection removed" % (self.jabberID))

	def sendTypingNotification(self, to, fro, typing):
		""" Sends the user the contact's current typing notification status """
		if(self.typingUser):
			debug.log("jabw: Sending a Jabber typing notification message \"%s\" \"%s\" \"%s\"" % (to, fro, typing))
			el = Element((None, "message"))
			el.attributes["to"] = to
			el.attributes["from"] = fro
			x = el.addElement("x")
			x.attributes["xmlns"] = "jabber:x:event"
			if(typing):
				composing = x.addElement("composing") 
			id = x.addElement("id")
			if(self.messageIDs.has_key(fro) and self.messageIDs[fro]):
				id.addContent(self.messageIDs[fro])
			self.pytrans.send(el)
	
	def checkFrom(self, el):
		""" Checks to see that this packet was intended for this object """
		fro = el.getAttribute("from")
		froj = JID(fro)
		
		return (froj.userhost() == self.jabberID) # Compare with the Jabber ID that we're looking at
	
	def sendMessage(self, to, fro, body, mtype=None):
		""" Sends a Jabber message """
		debug.log("User: %s - JabberConnection sending message \"%s\" \"%s\" \"%s\" \"%s\"" % (self.jabberID, to, fro, utils.latin1(body), mtype))
		sendMessage(self.pytrans, to, fro, body, mtype)
	
	def sendErrorMessage(self, to, fro, etype, eelement, econtent, body=None):
		debug.log("User: %s - JabberConnection sending error response." % (self.jabberID))
		sendErrorMessage(self.pytrans, to, fro, etype, eelement, econtent, body)
	
	def sendPresence(self, to, fro, show=None, status=None, priority=None, ptype=None):
		""" Sends a Jabber presence packet """
		debug.log("User: %s - JabberConnection sending presence \"%s\" \"%s\" \"%s\" \"%s\" \"%s\" \"%s\"" % (self.jabberID, to, fro, show, utils.latin1(status), priority, ptype))
		sendPresence(self.pytrans, to, fro, show, status, priority, ptype)
	
	def sendRosterImport(self, jid, ptype, sub, name="", groups=[]):
		""" Sends a special presence packet. This will work with all clients, but clients that support roster-import will give a better user experience
		IMPORTANT - Only ever use this for contacts that have already been authorised on the legacy service """
		el = Element((None, "presence"))
		el.attributes["to"] = self.jabberID
		el.attributes["from"] = jid
		el.attributes["type"] = ptype
		r = el.addElement("x")
		r.attributes["xmlns"] = "http://jabber.org/protocol/roster-subsync"
		item = r.addElement("item")
		item.attributes["subscription"] = sub
		if(name):
			item.attributes["name"] = unicode(name)
		for group in groups:
			g = item.addElement("group")
			g.addContent(group)
		
		self.pytrans.send(el)
	
	def onMessage(self, el):
		""" Handles incoming message packets """
		if(not self.checkFrom(el)): return
		debug.log("User: %s - JabberConnection received message packet" % (self.jabberID))
		fro = el.getAttribute("from")
		froj = JID(fro)
		to = el.getAttribute("to")
		toj = JID(to)
		mID = el.getAttribute("id")
		
		mtype = el.getAttribute("type")
		body = ""
		invite = ""
		messageEvent = False
		composing = None
		for child in el.elements():
			if(child.name == "body"):
				body = child.__str__()
			if(child.name == "x"):
				if(child.uri == "jabber:x:conference"):
					invite = child.getAttribute("jid") # The room the contact is being invited to
				if(child.uri == "jabber:x:event"):
					messageEvent = True
					composing = False
					for deepchild in child.elements():
						if(deepchild.name == "composing"):
							composing = True

		if(invite):
			debug.log("User: %s - JabberConnection parsed message groupchat invite packet \"%s\" \"%s\" \"%s\" \"%s\"" % (self.jabberID, froj.userhost(), to, froj.resource, utils.latin1(invite)))
			self.inviteReceived(froj.userhost(), froj.resource, toj.userhost(), toj.resource, invite)

		# Check message event stuff
		if(body and messageEvent):
			self.typingUser = True
		elif(body and not messageEvent):
			self.typingUser = False
		elif(not body and messageEvent):
			debug.log("User: %s - JabberConnection parsed typing notification \"%s\" \"%s\"" % (self.jabberID, toj.userhost(), composing))
			self.typingNotificationReceived(toj.userhost(), composing)

		if(body):
# 			body = utils.utf8(body)
			# Save the message ID for later
			self.messageIDs[to] = mID
			debug.log("User: %s - JabberConnection parsed message packet \"%s\" \"%s\" \"%s\" \"%s\" \"%s\"" % (self.jabberID, froj.userhost(), to, froj.resource, mtype, utils.latin1(body)))
			self.messageReceived(froj.userhost(), froj.resource, toj.userhost(), toj.resource, mtype, body)
	
	def onPresence(self, el):
		""" Handles incoming presence packets """
		if(not self.checkFrom(el)): return
		debug.log("User: %s - JabberConnection received presence packet" % (self.jabberID))
		fro = el.getAttribute("from")
		froj = JID(fro)
		to = el.getAttribute("to")
		toj = JID(to)
		
		# Grab the contents of the <presence/> packet
		ptype = el.getAttribute("type")
		if(ptype in ["subscribe", "subscribed", "unsubscribe", "unsubscribed"]):
			debug.log("User: %s - JabberConnection parsed subscription presence packet \"%s\" \"%s\"" % (self.jabberID, toj.userhost(), ptype))
			self.subscriptionReceived(toj.userhost(), ptype)
		else:
			status = None
			show = None
			priority = None
			for child in el.elements():
				if(child.name == "status"):
					status = child.__str__()
				elif(child.name == "show"):
					show = child.__str__()
				elif(child.name == "priority"):
					priority = child.__str__()
			
			debug.log("User: %s - JabberConnection parsed presence packet \"%s\" \"%s\" \"%s\" \"%s\" \"%s\" \"%s\"" % (self.jabberID, froj.userhost(), froj.resource, priority, ptype, show, utils.latin1(status)))
			self.presenceReceived(froj.userhost(), froj.resource, toj.userhost(), toj.resource, priority, ptype, show, status)
	
	
	
	def messageReceived(self, source, resource, dest, destr, mtype, body):
		""" Override this method to be notified when a message is received """
		pass
	
	def inviteReceived(self, source, resource, dest, destr, roomjid):
		""" Override this method to be notified when an invitation is received """
		pass
	
	def presenceReceived(self, source, resource, to, tor, priority, ptype, show, status):
		""" Override this method to be notified when presence is received """
		pass
	
	def subscriptionReceived(self, source, subtype):
		""" Override this method to be notified when a subscription packet is received """
		pass



