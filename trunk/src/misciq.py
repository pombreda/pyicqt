# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

from tlib.jabber import component, jid
from tlib.domish import Element

import legacy
import config
import utils
import lang
import debug


IQ_GATEWAY = "jabber:iq:gateway"

class GatewayTranslator:
	def __init__(self, pytrans):
		self.pytrans = pytrans
	
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
		query.attributes["xmlns"] = IQ_GATEWAY
		desc = query.addElement("desc")
		desc.addContent(lang.get(ulang).gatewayTranslator)
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
			query.attributes["xmlns"] = IQ_GATEWAY
			prompt = query.addElement("prompt")
			prompt.addContent(legacy.translateAccount(legacyaccount))
			
			self.pytrans.send(iq)
		
		else:
			self.pytrans.discovery.sendIqNotValid(to, ID, IQ_GATEWAY)

