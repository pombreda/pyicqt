# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.web import microdom
import groupchat

# The name of the transport
name = "Foo Transport"

# The transport version
version = "0.1"

# XDB '@' -> '%' mangling
mangle = True

# The transport identifier (eg, aim, icq, msn)
id = "foo"

# This should be set to the name space registration entries are in, in the xdb spool
namespace = "jabber:iq:register"



def isGroupJID(jid):
	""" Returns True if the JID passed is a valid groupchat JID (eg, for MSN, if it does not contain '%') """
	pass



def formRegEntry(username, password, nickname):
	""" Returns a microdom.Element representation of the data passed. This element will be written to the XDB spool file """
	pass



def getAttributes(base):
	""" This function should, given a spool microdom.Element, pull the username, password,
	and nickname out of it and return them """
	pass
#	return username, password, nickname




def translateAccount(legacyaccount):
	""" Translates the legacy account into a Jabber ID, eg, user@hotmail.com --> user%hotmail.com@msn.jabber.org """
	pass



class LegacyGroupchat(groupchat.BaseGroupchat):
	""" A class to represent a groupchat on the legacy service. All the functions below
	must be implemented to translate messages from Jabber to the legacy protocol.
	Look in groupchat.py for available functions to call.
	"""
	def __init__(self, session, resource, ID=None):
		groupchat.BaseGroupchat.__init__(self, session, resource, ID)
		# Initialisation stuff for the legacy protocol goes here

	def removeMe(self):
		""" Cleanly remove the the groupchat, including removing the user from the legacy room """
		groupchat.BaseGroupchat.removeMe(self)
	
	def sendLegacyMessage(self, message):
		""" Send this message to the legacy room  """
	
	def sendContactInvite(self, contactJID):
		""" Invite this user to the legacy room """




class LegacyConnection:
	""" A base class that must have all functions reimplemented by legacy protocols to translate
	from Jabber to that legacy protocol. Any incoming events from the legacy system must be
	translated by calling the appropriate functions in the Session, JabberConnection or PyTransport classes.
	You must also set self.session.ready = True at some point (usually when you have been connected to the
	legacy service """
	def __init__(self, session):
		pass
	
	def removeMe(self):
		""" Called by PyTransport when the user's session is ending.
		Must cleanly delete this object. Including sending an offline presence packet
		for any contacts that may be on the user's list """
		pass
	
	def sendMessage(self, dest, body):
		""" Called whenever PyTransport wants to send a message to a remote user """
		pass
	
	def setStatus(self, show, friendly):
		""" Called whenever PyTransport needs to change the status on the legacy service 
		'show' is a Jabber status description, and friendly is a friendly name for the contact """
		pass
	
	def newResourceOnline(self, resource):
		""" Called by PyTransport when a new resource comes online. You should send them any legacy contacts' status """
		pass
	
	def jabberSubscriptionReceived(self, to, subtype):
		""" Called by PyTransport whenever a Jabber subscription packet is received """
		pass


