# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
if(utils.checkTwisted()):
	from twisted.xish.domish import Element
else:
	from tlib.domish import Element
import sys
import config
import legacy
import debug
import jabw

XMPP_STANZAS = 'urn:ietf:params:xml:ns:xmpp-stanzas'
DISCO = "http://jabber.org/protocol/disco"
DISCO_ITEMS = DISCO + "#items"
DISCO_INFO = DISCO + "#info"
VCARD = "vcard-temp"

class Discovery:
	def __init__ (self, pytrans):
		debug.log("Discovery: Created discovery manager")
		self.pytrans = pytrans
		self.identities = []
		self.features = []
		
		self.addFeature(DISCO, None)
	
	def addIdentity(self, category, ctype, name):
		debug.log("Discovery: Adding identity \"%s\" \"%s\" \"%s\"" % (category, ctype, name))
		self.identities.append((category, ctype, name))
	
	def addFeature(self, var, handler):
		debug.log("Discovery: Adding feature support \"%s\" \"%s\"" % (var, handler))
		self.features.append((var, handler))
	
	def onIq(self, el):
		fro = el.getAttribute("from")
		to = el.getAttribute("to")
		ID = el.getAttribute("id")
		type = el.getAttribute("type")
		if(not type in ["get","set"]):
			# Never reply to an error or result IQ, nasty loops will result.
			debug.log("Discovery: Unhandled %s Iq received \"%s\" \"%s\". Looking for handler" % (type, fro, ID))
			return
			
		debug.log("Discovery: Iq received \"%s\" \"%s\". Looking for handler" % (fro, ID))
		query = None
		vcard = None
		for child in el.elements():
			debug.log("Discover: Child: %s" % (child.name))
			if(child.name == "vCard"):
				debug.log("Discover: Matched vCard")
				vcard = child
				break
			if(child.name == "query"):
				debug.log("Discover: Matched query")
				query = child
				break

		if(vcard):
			xmlns = vcard.getAttribute("xmlns")
			debug.log("Discover: %s %s" % (xmlns, vcard.toXml()))
			if(type == "get"):
				if(to.find('@') > 0): # Iq to a user
					#if(xmlns == VCARD):
						self.sendIqVCard(to=fro, target=to, ID=ID, xmlns=xmlns)
					#else:
					#	debug.log("VCard: no appropriate namespace \"%s\", \"%s\" \"%s\" \"%s\"" % (to, fro, ID, xmlns))
					#	self.sendIqNotSupported(to=fro, ID=ID, xmlns=VCARD)
				else:
					debug.log("VCard: no reasonable to specified \"%s\", \"%s\" \"%s\"" % (to, fro, ID))
					self.sendIqNotSupported(to=fro, ID=ID, xmlns=VCARD)
			else:
				debug.log("VCard: not a get request \"%s\", \"%s\" \"%s\"" % (to, fro, ID))
				self.sendIqNotSupported(to=fro, ID=ID, xmlns=VCARD)

		if(query):
			xmlns = query.defaultUri
			
			if(to.find('@') > 0): # Iq to a user
				debug.log("Discovery: Unknown Iq request \"%s\", \"%s\" \"%s\" \"%s\"" % (to, fro, ID, xmlns))
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
	
	def sendIqNotSupported(self, to, ID, xmlns):
		debug.log("Discovery: Replying with error to unknown Iq request")
		self.sendIqError(to, ID, "feature-not-implemented", "cancel", "Not implemented.", 501)
	
	def sendIqNotValid(self, to, ID, xmlns):
		debug.log("Discovery: Replying with error to invalid Iq request")
		self.sendIqError(to, ID, "bad-request", "modify", "Not valid.", 400)

	def sendIqError(self, to, ID, condition, type, text, code=None):
		iq = Element((None, "iq"))
		iq.attributes["type"] = "error"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if(ID):
			iq.attributes["id"] = ID
		iq.addChild(jabw.makeErrorElement(type, condition, text))
		#error = iq.addElement("error")
		#error.attributes["type"] = type
		#if code:
		#	error.attributes["code"] = code
		#con = error.addElement(condition)
		#con.attributes["xmlns"] = XMPP_STANZAS
		#if text:
		#	txt = error.addElement("text")
		#	txt.attributes["xmlns"] = XMPP_STANZAS
		#	txt.addContent(text)

		self.pytrans.send(iq)

	def sendIqVCard(self, to, target, ID, xmlns):
		debug.log("Discovery: Replying to vcard request")
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = target
		iq.attributes["to"] = to
		if(ID):
			iq.attributes["id"] = ID
		vcard = iq.addElement("vCard")
		vcard.attributes["xmlns"] = VCARD

		user = target.split('@')[0]
		if (hasattr(self.pytrans, "legacycon")):
			self.pytrans.legacycon.jabberVCardRequest(vcard, user).addCallback(self.gotIqVCard, iq)

	def gotIqVCard(self, vcard, iq):
		# DSH removed the try/except... why?
		try:
			debug.log("Discovery: gotIqVCard iq %s" % (iq.toXml()))
			if not len(vcard.children):
				iq.attributes["type"] = "error"
				error = iq.addElement("error")
				error.attributes["type"] = "cancel"
				error.attributes["code"] = "502"
				type = error.addElement("undefined-condition")
				type.attributes["xmlns"] = "urn:ietf:params:xml:ns:xmpp-stanzas"
			self.pytrans.send(iq)
		except:
			pass
