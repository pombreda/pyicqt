# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.xish.domish import Element
import sys
import config
import legacy
import debug

XMPP_STANZAS = 'urn:ietf:params:xml:ns:xmpp-stanzas'
DISCO = "http://jabber.org/protocol/disco"
DISCO_ITEMS = DISCO + "#items"
DISCO_INFO = DISCO + "#info"
IQ_VERSION = "jabber:iq:version"


class Discovery:
	def __init__ (self, pytrans):
		debug.log("Discovery: Created discovery manager")
		self.pytrans = pytrans
		self.identities = []
		self.features = []
		
		self.addFeature(DISCO, None)
		self.addFeature(IQ_VERSION, self.sendVersion)
	
	def addIdentity(self, category, ctype, name):
		debug.log("Discovery: Adding identitity \"%s\" \"%s\" \"%s\"" % (category, ctype, name))
		self.identities.append((category, ctype, name))
	
	def addFeature(self, var, handler):
		debug.log("Discovery: Adding feature support \"%s\" \"%s\"" % (var, handler))
		self.features.append((var, handler))
	
	def onIq(self, el):
		fro = el.getAttribute("from")
		to = el.getAttribute("to")
		ID = el.getAttribute("id")
		debug.log("Discovery: Iq received \"%s\" \"%s\". Looking for handler" % (fro, ID))
		debug.log("Discovery: Handling el: %s" % (el))
		query = None
		for child in el.elements():
			if(child.name == "query"):
				query = child
				break
		if(query):
			xmlns = query.defaultUri
			
			if(to.find('@') > 0): # Iq to a user
				self.sendIqNotSupported(to=fro, ID=ID, xmlns=DISCO)
			
			else: # Iq to transport
				if(xmlns == DISCO_INFO):
					self.sendDiscoInfoResponse(to=fro, ID=ID)
				elif(xmlns == DISCO_ITEMS):
					self.sendDiscoItemsResponse(to=fro, ID=ID)
				else:
					handled = False
					for (feature, handler) in self.features:
						if(feature == xmlns):
							if(handler):
								debug.log("Discovery: Handler found \"%s\" \"%s\"" % (feature, handler))
								handler(el)
								handled = True
					if(not handled):
						debug.log("Discovery: Unknown Iq request \"%s\" \"%s\" \"%s\"" % (fro, ID, xmlns))
						self.sendIqNotSupported(to=fro, ID=ID, xmlns=DISCO)
	
	def sendDiscoInfoResponse(self, to, ID):
		debug.log("Discovery: Replying to disco#info request from \"%s\" \"%s\"" % (to, ID))
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if(ID):
			iq.attributes["id"] = ID
		query = iq.addElement("query")
		query.attributes["xmlns"] = DISCO_INFO
		
		# Add any identities
		for (category, ctype, name) in self.identities:
			identity = query.addElement("identity")
			identity.attributes["category"] = category
			identity.attributes["type"] = ctype
			identity.attributes["name"] = name
		
		# Add any supported features
		for (var, handler) in self.features:
			feature = query.addElement("feature")
			feature.attributes["var"] = var
		self.pytrans.send(iq)
	
	def sendDiscoItemsResponse(self, to, ID):
		debug.log("Discovery: Replying to disco#items request from \"%s\" \"%s\"" % (to, ID))
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if(ID):
			iq.attributes["id"] = ID
		query = iq.addElement("query")
		query.attributes["xmlns"] = DISCO_ITEMS
		
		self.pytrans.send(iq)
	
	def sendVersion(self, el):
		debug.log("Discovery: Sending transport version information")
		iq = Element((None, "iq"))
		iq.attributes["type"] = "set"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = el.getAttribute("from")
		iq.attributes["id"] = el.getAttribute("id")
		query = iq.addElement("query")
		query.attributes["xmlns"] = IQ_VERSION
		name = query.addElement("name")
		name.addContent(legacy.name)
		version = query.addElement("version")
		version.addContent(legacy.version)
		os = query.addElement("os")
		os.addContent("Python " + sys.version)
		
		self.pytrans.send(iq)
	
	def sendIqNotSupported(self, to, ID, xmlns):
		debug.log("Discovery: Replying with error to unknown Iq request")
		iq = Element((None, "iq"))
		iq.attributes["type"] = "error"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if(ID):
			iq.attributes["id"] = ID
		error = iq.addElement("error")
		error.attributes["xmlns"] = xmlns
		error.attributes["type"] = "cancel"
		error.attributes["xmlns"] = XMPP_STANZAS
		text = error.addElement("text")
		text.attributes["xmlns"] = XMPP_STANZAS
		text.addContent("Not implemented.")
		
		self.pytrans.send(iq)
	
	def sendIqNotValid(self, to, ID, xmlns):
		debug.log("Discovery: Replying with error to invalid Iq request")
		iq = Element((None, "iq"))
		iq.attributes["type"] = "error"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if(ID):
			iq.attributes["id"] = ID
		error = iq.addElement("error")
		error.attributes["xmlns"] = xmlns
		error.attributes["type"] = "modify"
		error.attributes["xmlns"] = XMPP_STANZAS
		text = error.addElement("text")
		text.attributes["xmlns"] = XMPP_STANZAS
		text.addContent("Not valid.")
		
		self.pytrans.send(iq)

