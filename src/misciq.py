# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
if(utils.checkTwisted()):
	from twisted.xish.domish import Element
	from twisted.words.protocols.jabber import component, jid
else:
	from tlib.domish import Element
	from tlib.jabber import component, jid

import legacy
import config
import lang
import debug
import sys


class GatewayTranslator:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature("jabber:iq:gateway", self.incomingIq)

	
	def incomingIq(self, el):
		fro = el.getAttribute("from")
		ID = el.getAttribute("id")
		itype = el.getAttribute("type")
		if(itype == "get"):
			self.sendPrompt(fro, ID, utils.getLang(el))
		elif(itype == "set"):
			self.sendTranslation(fro, ID, el)
	
	
	def sendPrompt(self, to, ID, ulang):
		debug.log("GatewayTranslator: Sending translation details for jabber:iq:gateway - user %s %s" % (to, ID))
		
		iq = Element((None, "iq"))
		
		iq.attributes["type"] = "result"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		iq.attributes["id"] = ID
		query = iq.addElement("query")
		query.attributes["xmlns"] = "jabber:iq:gateway"
		desc = query.addElement("desc")
		desc.addContent(lang.get(ulang).gatewaytranslator)
		prompt = query.addElement("prompt")
		
		self.pytrans.send(iq)
	
	def sendTranslation(self, to, ID, el):
		debug.log("GatewayTranslator: Translating account for jabber:iq:gateway - user %s %s" % (to, ID))
		
		# Find the user's legacy account
		legacyaccount = None
		for query in el.elements():
			if(query.name == "query"):
				for child in query.elements():
					if(child.name == "prompt"):
						legacyaccount = str(child)
						break
				break
		
		
		if(legacyaccount and len(legacyaccount) > 0):
			debug.log("GatewayTranslator: Sending translated account for jabber:iq:gateway - user %s %s" % (to, ID))
			iq = Element((None, "iq"))
			iq.attributes["type"] = "result"
			iq.attributes["from"] = config.jid
			iq.attributes["to"] = to
			iq.attributes["id"] = ID
			query = iq.addElement("query")
			query.attributes["xmlns"] = "jabber:iq:gateway"
			prompt = query.addElement("prompt")
			prompt.addContent(legacy.translateAccount(legacyaccount))
			
			self.pytrans.send(iq)
		
		else:
			self.pytrans.discovery.sendIqNotValid(to, ID, "jabber:iq:gateway")

class VersionTeller:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature("jabber:iq:version", self.incomingIq)

	def incomingIq(self, el):
		eltype = el.getAttribute("type")
		if(eltype != "get"): return # Only answer "get" stanzas

		self.sendVersion(el)

	def sendVersion(self, el):
		debug.log("Discovery: Sending transport version information")
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = el.getAttribute("from")
		if(el.getAttribute("id")):
			iq.attributes["id"] = el.getAttribute("id")
		query = iq.addElement("query")
		query.attributes["xmlns"] = "jabber:iq:version"
		name = query.addElement("name")
		name.addContent(legacy.name)
		version = query.addElement("version")
		version.addContent(legacy.version)
		os = query.addElement("os")
		os.addContent("Python" + sys.version)

		self.pytrans.send(iq)
