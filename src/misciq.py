# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from tlib.twistwrap import Element, jid
from twisted.internet import reactor, task

import jabw
import legacy
import disco
import config
import lang
import debug
import base64
import sys
import avatar
import globals

class ConnectUsers:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.adHocCommands.addCommand("connectusers", self.incomingIq, "command_ConnectUsers")
        
	def sendProbes(self):
		for jid in self.pytrans.xdb.getRegistrationList():
			jabw.sendPresence(self.pytrans, jid, config.jid, ptype="probe")

	def incomingIq(self, el):
		to = el.getAttribute("from")
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		if config.admins.count(jid.JID(to).userhost()) == 0:
			self.pytrans.discovery.sendIqError(to=to, fro=config.jid, ID=ID, xmlns=globals.COMMANDS, etype="cancel", condition="not-authorized")
			return

		self.sendProbes()

		iq = Element((None, "iq"))
		iq.attributes["to"] = to
		iq.attributes["from"] = config.jid
		if ID:
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"

		command = iq.addElement("command")
		command.attributes["sessionid"] = self.pytrans.makeMessageID()
		command.attributes["xmlns"] = globals.COMMANDS
		command.attributes["status"] = "completed"

		x = command.addElement("x")
		x.attributes["xmlns"] = "jabber:x:data"
		x.attributes["type"] = "result"

		title = x.addElement("title")
		title.addContent(lang.get("command_ConnectUsers", ulang))

		field = x.addElement("field")
		field.attributes["type"] = "fixed"
		field.addElement("value").addContent(lang.get("command_Done", ulang))

		self.pytrans.send(iq)


class Statistics:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.adHocCommands.addCommand("stats", self.incomingIq, "command_Statistics")

		# self.stats is indexed by a unique ID, with value being the value for that statistic
		self.stats = {}
		self.stats["Uptime"] = 0
		self.stats["OnlineSessions"] = 0
		self.stats["IncomingMessages"] = 0
		self.stats["OutgoingMessages"] = 0
		self.stats["TotalSessions"] = 0
		self.stats["MaxConcurrentSessions"] = 0

		self.sessionstats = {}

		legacy.startStats(self)

	def sessionSetup(self, jid):
		self.sessionstats[jid] = { } 
		self.sessionstats[jid]['IncomingMessages'] = 0
		self.sessionstats[jid]['OutgoingMessages'] = 0
		self.sessionstats[jid]['Connections'] = 0

	def sessionUpdate(self, jid, setting, value):
		if not self.sessionstats.has_key(jid):
			self.sessionSetup(jid)
		self.sessionstats[jid][setting] += value

	def incomingIq(self, el):
		to = el.getAttribute("from")
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		iq = Element((None, "iq"))
		iq.attributes["to"] = to
		iq.attributes["from"] = config.jid
		if ID:
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"

		command = iq.addElement("command")
		command.attributes["sessionid"] = self.pytrans.makeMessageID()
		command.attributes["xmlns"] = globals.COMMANDS
		command.attributes["status"] = "completed"

		x = command.addElement("x")
		x.attributes["xmlns"] = "jabber:x:data"
		x.attributes["type"] = "result"

		title = x.addElement("title")
		title.addContent(lang.get("command_Statistics", ulang))

		for key in self.stats:
			label = lang.get("statistics_%s" % key, ulang)
			description = lang.get("statistics_%s_Desc" % key, ulang)
			field = x.addElement("field")
			field.attributes["var"] = key
			field.attributes["label"] = label
			field.attributes["type"] = "text-single"
			field.addElement("value").addContent(str(self.stats[key]))
			field.addElement("desc").addContent(description)

		self.pytrans.send(iq)



class AdHocCommands:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature(globals.COMMANDS, self.incomingIq, config.jid)
		self.pytrans.discovery.addNode(globals.COMMANDS, self.sendCommandList, "command_CommandList", config.jid, True)

		self.commands = {} # Dict of handlers indexed by node
		self.commandNames = {} # Dict of names indexed by node

	def addCommand(self, command, handler, name):
		self.commands[command] = handler
		self.commandNames[command] = name
		self.pytrans.discovery.addNode(command, self.incomingIq, name, config.jid, False)

	def incomingIq(self, el):
		itype = el.getAttribute("type")
		fro = el.getAttribute("from")
		froj = jid.JID(fro)
		to = el.getAttribute("to")
		ID = el.getAttribute("id")

		debug.log("Discovery: AdHoc Iq received \"%s\" \"%s\". Looking for handler" % (fro, ID))

		node = None
		for child in el.elements():
			xmlns = child.defaultUri
			node = child.getAttribute("node")

			handled = False
			if child.name == "query" and xmlns == globals.DISCO_INFO:
				if node and self.commands.has_key(node) and itype == "get":
					self.sendCommandInfoResponse(to=fro, ID=ID)
					handled = True
			elif child.name == "query" and xmlns == globals.DISCO_ITEMS:
				if node and self.commands.has_key(node) and itype == "get":
					self.sendCommandItemsResponse(to=fro, ID=ID)
					handled = True
			elif child.name == "command" and xmlns == globals.COMMANDS:
				if node and self.commands.has_key(node) and (itype == "set" or itype == "error"):
					self.commands[node](el)
					handled = True
			if not handled:
				debug.log("Discovery: Unknown AdHoc Iq request \"%s\" \"%s\" \"%s\"" % (fro, ID, node))
				self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=xmlns, etype="cancel", condition="feature-not-implemented")


	def sendCommandList(self, el):
		to = el.getAttribute("from")
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		iq = Element((None, "iq"))
		iq.attributes["to"] = to
		iq.attributes["from"] = config.jid
		iq.attributes["id"] = ID
		iq.attributes["type"] = "result"

		query = iq.addElement("query")
		query.attributes["xmlns"] = globals.DISCO_ITEMS
		query.attributes["node"] = globals.COMMANDS

		for command in self.commands:
			item = query.addElement("item")
			item.attributes["jid"] = config.jid
			item.attributes["node"] = command
			item.attributes["name"] = lang.get(self.commandNames[command], ulang)

		self.pytrans.send(iq)

	def sendCommandInfoResponse(self, to, ID):
		debug.log("Discovery: Replying to AdHoc disco#info request from \"%s\" \"%s\"" % (to, ID))
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if ID: iq.attributes["id"] = ID
		query = iq.addElement("query")
		query.attributes["xmlns"] = globals.DISCO_INFO

		# Add supported feature
		feature = query.addElement("feature")
		feature.attributes["var"] = globals.COMMANDS
		self.pytrans.send(iq)

	def sendCommandItemsResponse(self, to, ID):
		debug.log("Discovery: Replying to AdHoc disco#items request from \"%s\" \"%s\"" % (to, ID))
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = to
		if ID: iq.attributes["id"] = ID
		query = iq.addElement("query")
		query.attributes["xmlns"] = globals.DISCO_ITEMS

		self.pytrans.send(iq)



class VCardFactory:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature("vcard-temp", self.incomingIq, "USER")
		self.pytrans.discovery.addFeature("vcard-temp", self.incomingIq, config.jid)
		self.pytrans.adHocCommands.addCommand("updatemyvcard", self.getMyVCard, "command_UpdateMyVCard")

	def incomingIq(self, el):
		itype = el.getAttribute("type")
		fro = el.getAttribute("from")
		froj = jid.JID(fro)
		to = el.getAttribute("to")
		ID = el.getAttribute("id")
		if itype != "get" and itype != "error":
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="cancel", condition="feature-not-implemented")
			return

		debug.log("VCardFactory: Retrieving vCard for user %s %s" % (to, ID))

		toGateway = not (to.find('@') > 0)
		if not toGateway:
			if not self.pytrans.sessions.has_key(froj.userhost()):
				self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="auth", condition="not-authorized")
				return
			s = self.pytrans.sessions[froj.userhost()]
			if not s.ready:
				self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="auth", condition="not-authorized")
				return

			c = s.contactList.findContact(to)
			if not c:
				iq = Element((None, "iq"))
				iq.attributes["to"] = fro
				iq.attributes["from"] = to
				iq.attributes["id"] = ID
				iq.attributes["type"] = "result"
				vCard = iq.addElement("vCard")
				vCard.attributes["xmlns"] = "vcard-temp"
				self.pytrans.legacycon.getvCardNotInList(vCard, to).addCallback(self.gotvCardResponse, iq)
				return
				# Lets leave this up to the legacy pieces
				#self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="cancel", condition="recipient-unavailable")


		iq = Element((None, "iq"))
		iq.attributes["to"] = fro
		iq.attributes["from"] = to
		iq.attributes["id"] = ID
		iq.attributes["type"] = "result"
		vCard = iq.addElement("vCard")
		vCard.attributes["xmlns"] = "vcard-temp"
		if toGateway:
			FN = vCard.addElement("FN")
			FN.addContent(legacy.name)
			DESC = vCard.addElement("DESC")
			DESC.addContent(legacy.name)
			URL = vCard.addElement("URL")
			URL.addContent(legacy.url)

			from legacy import defaultAvatar
			PHOTO = defaultAvatar.makePhotoElement()
			vCard.addChild(PHOTO)

			self.pytrans.send(iq)
		else:
			c.fillvCard(vCard, to).addCallback(self.gotvCardResponse, iq)

	def gotvCardResponse(self, vcard, iq):
		#debug.log("VCardFactory: Sending vCard %s" % (vcard.toXml()))
		debug.log("VCardFactory: Sending vCard")
		self.pytrans.send(iq)

	def getMyVCard(self, el):
		to = el.getAttribute("from")
		fro = el.getAttribute("from")
		froj = jid.JID(fro)
		ID = el.getAttribute("id")
		ulang = utils.getLang(el)

		if not self.pytrans.sessions.has_key(froj.userhost()):
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="auth", condition="not-authorized")
			return
		s = self.pytrans.sessions[froj.userhost()]
		if not s.ready:
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns="vcard-temp", etype="auth", condition="not-authorized")
			return

		s.doVCardUpdate()

		iq = Element((None, "iq"))
		iq.attributes["to"] = to
		iq.attributes["from"] = config.jid
		if ID:
			iq.attributes["id"] = ID
		iq.attributes["type"] = "result"

		command = iq.addElement("command")
		command.attributes["sessionid"] = self.pytrans.makeMessageID()
		command.attributes["xmlns"] = globals.COMMANDS
		command.attributes["status"] = "completed"

		x = command.addElement("x")
		x.attributes["xmlns"] = "jabber:x:data"
		x.attributes["type"] = "result"

		title = x.addElement("title")
		title.addContent(lang.get("command_UpdateMyVCard", ulang))

		field = x.addElement("field")
		field.attributes["type"] = "fixed"
		field.addElement("value").addContent(lang.get("command_Done", ulang))

		self.pytrans.send(iq)


class IqAvatarFactory:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature("jabber:iq:avatar", self.incomingIq, "USER")
		self.pytrans.discovery.addFeature("storage:client:avatar", self.incomingIq, "USER")

	def incomingIq(self, el):
		itype = el.getAttribute("type")
		fro = el.getAttribute("from")
		froj = jid.JID(fro)
		to = el.getAttribute("to")
		ID = el.getAttribute("id")
		for query in el.elements():
			if(query.name == "query"):
				xmlns = query.defaultUri
		if not xmlns:
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=xmlns, etype="cancel", condition="bad-request")
			return
		if itype != "get" and itype != "error":
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=xmlns, etype="cancel", condition="feature-not-implemented")
			return

		debug.log("IqAvatarFactory: Retrieving avatar for user %s %s" % (to, ID))

		if not self.pytrans.sessions.has_key(froj.userhost()):
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=xmlns, etype="auth", condition="not-authorized")
			return
		s = self.pytrans.sessions[froj.userhost()]
		if not s.ready:
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=xmlns, etype="auth", condition="not-authorized")
			return

		c = s.contactList.findContact(to)
		if not c:
			self.pytrans.discovery.sendIqError(to=fro, fro=config.jid, ID=ID, xmlns=xmlns, etype="cancel", condition="recipient-unavailable")
			return

		iq = Element((None, "iq"))
		iq.attributes["to"] = fro
		iq.attributes["from"] = to
		iq.attributes["id"] = ID
		iq.attributes["type"] = "result"
		query = iq.addElement("query")
		query.attributes["xmlns"] = xmlns
		if c.avatar:
			DATA = c.avatar.makeDataElement()
			query.addChild(DATA)


class PingService:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		#self.pingCounter = 0
		#self.pingTask = task.LoopingCall(self.pingCheck)
		self.pingTask = task.LoopingCall(self.whitespace)
		reactor.callLater(10.0, self.start)

	def start(self):
		self.pingTask.start(120.0)

	def whitespace(self):
		self.pytrans.send(" ")

	def pingCheck(self):
		if self.pingCounter >= 2 and self.pytrans.xmlstream: # Two minutes of no response from the main server
			debug.log("Disconnecting because the main server has ignored our 'pings' for too long.")
			self.pytrans.xmlstream.transport.loseConnection()
		elif config.mainServerJID:
			d = self.pytrans.discovery.sendIq(self.makePingPacket())
			d.addCallback(self.pongReceived)
			d.addErrback(self.pongFailed)
			self.pingCounter += 1

	def pongReceived(self, el):
		self.pingCounter = 0

	def pongFailed(self, el):
		pass

	def makePingPacket(self):
		iq = Element((None, "iq"))
		iq.attributes["from"] = config.jid
		iq.attributes["to"] = config.mainServerJID
		iq.attributes["type"] = "get"
		query = iq.addElement("query")
		query.attributes["xmlns"] = "jabber:iq:version"
		return iq

class GatewayTranslator:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature("jabber:iq:gateway", self.incomingIq, config.jid)
	
	def incomingIq(self, el):
		fro = el.getAttribute("from")
		ID = el.getAttribute("id")
		itype = el.getAttribute("type")
		if itype == "get":
			self.sendPrompt(fro, ID, utils.getLang(el))
		elif itype == "set":
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
		desc.addContent(lang.get("gatewaytranslator", ulang))
		prompt = query.addElement("prompt")
		
		self.pytrans.send(iq)
	
	def sendTranslation(self, to, ID, el):
		debug.log("GatewayTranslator: Translating account for jabber:iq:gateway - user %s %s" % (to, ID))
		
		# Find the user's legacy account
		legacyaccount = None
		for query in el.elements():
			if query.name == "query":
				for child in query.elements():
					if child.name == "prompt":
						legacyaccount = str(child)
						break
				break
		
		
		if legacyaccount and len(legacyaccount) > 0:
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
			self.pytrans.discovery.sendIqError(to, ID, "jabber:iq:gateway")
			self.pytrans.discovery.sendIqError(to=to, fro=config.jid, ID=ID, xmlns="jabber:iq:gateway", etype="retry", condition="bad-request")



class VersionTeller:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature("jabber:iq:version", self.incomingIq, config.jid)
		self.pytrans.discovery.addFeature("jabber:iq:version", self.incomingIq, "USER")

	def incomingIq(self, el):
		eltype = el.getAttribute("type")
		if eltype != "get": return # Only answer "get" stanzas

		self.sendVersion(el)

	def sendVersion(self, el):
		debug.log("Discovery: Sending transport version information")
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = el.getAttribute("to")
		iq.attributes["to"] = el.getAttribute("from")
		if el.getAttribute("id"):
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


class SearchFactory:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.discovery.addFeature("jabber:iq:search", self.incomingIq, config.jid)

	def incomingIq(self, el):
		eltype = el.getAttribute("type")
		ID = el.getAttribute("id")
		to = el.getAttribute("from")
		if not hasattr(self.pytrans, "legacycon"):
			self.pytrans.discovery.sendIqError(to=to, fro=config.jid, ID=ID, xmlns=globals.COMMANDS, etype="cancel", condition="service-unavailable")
		elif eltype == "get":
			self.sendSearchForm(el)
		elif eltype == "set":
			self.processSearch(el)

	def sendSearchForm(self, el):
		debug.log("SearchFactory: Sending search form")
		ulang = utils.getLang(el)
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = el.getAttribute("to")
		iq.attributes["to"] = el.getAttribute("from")
		if el.getAttribute("id"):
			iq.attributes["id"] = el.getAttribute("id")
		query = iq.addElement("query")
		query.attributes["xmlns"] = "jabber:iq:search"
		forminstr = query.addElement("instructions")
		forminstr.addContent(lang.get("searchnodataform", ulang))
		x = query.addElement("x")
		x.attributes["xmlns"] = "jabber:x:data"
		x.attributes["type"] = "form"
		title = x.addElement("title")
		title.addContent(lang.get("searchtitle", ulang))
		instructions = x.addElement("instructions")
		instructions.addContent(lang.get("searchinstructions", ulang))
		x.addChild(utils.makeDataFormElement("hidden", "FORM_TYPE", value="jabber:iq:search"))
		x.addChild(utils.makeDataFormElement("text-single", "email", "E-Mail Address"))
		x.addChild(utils.makeDataFormElement("text-single", "first", "First Name"))
		x.addChild(utils.makeDataFormElement("text-single", "middle", "Middle Name"))
		x.addChild(utils.makeDataFormElement("text-single", "last", "Last Name"))
		x.addChild(utils.makeDataFormElement("text-single", "maiden", "Maiden Name"))
		x.addChild(utils.makeDataFormElement("text-single", "nick", "Nickname"))
		x.addChild(utils.makeDataFormElement("text-single", "address", "Street Address"))
		x.addChild(utils.makeDataFormElement("text-single", "city", "City"))
		x.addChild(utils.makeDataFormElement("text-single", "state", "State"))
		x.addChild(utils.makeDataFormElement("text-single", "zip", "Zip Code"))
		x.addChild(utils.makeDataFormElement("text-single", "country", "Country"))
		x.addChild(utils.makeDataFormElement("text-single", "interest", "Interest"))

		self.pytrans.send(iq)

	def processSearch(self, el):
		debug.log("SearchFactory: Processing search form")
		ulang = utils.getLang(el)
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		to = el.getAttribute("to")
		iq.attributes["from"] = to
		fro = el.getAttribute("from")
		iq.attributes["to"] = fro
		ID = el.getAttribute("id")
		if ID:
			iq.attributes["id"] = ID
		query = iq.addElement("query")
		query.attributes["xmlns"] = "jabber:iq:search"
		x = query.addElement("x")
		x.attributes["xmlns"] = "jabber:x:data"
		x.attributes["type"] = "result"
		x.addChild(utils.makeDataFormElement("hidden", "FORM_TYPE", value="jabber:iq:search"))
		reported = x.addElement("reported")
		reported.addChild(utils.makeDataFormElement(None, "jid", "Jabber ID"))
		reported.addChild(utils.makeDataFormElement(None, "first", "First Name"))
		reported.addChild(utils.makeDataFormElement(None, "middle", "Middle Name"))
		reported.addChild(utils.makeDataFormElement(None, "last", "Last Name"))
		reported.addChild(utils.makeDataFormElement(None, "maiden", "Maiden Name"))
		reported.addChild(utils.makeDataFormElement(None, "nick", "Nickname"))
		reported.addChild(utils.makeDataFormElement(None, "email", "E-Mail Address"))
		reported.addChild(utils.makeDataFormElement(None, "address", "Street Address"))
		reported.addChild(utils.makeDataFormElement(None, "city", "City"))
		reported.addChild(utils.makeDataFormElement(None, "state", "State"))
		reported.addChild(utils.makeDataFormElement(None, "country", "Country"))
		reported.addChild(utils.makeDataFormElement(None, "zip", "Zip Code"))
		reported.addChild(utils.makeDataFormElement(None, "region", "Region"))

		dataform = None
		for query in el.elements():
			if query.name == "query":
				for child in query.elements():
					if child.name == "x":
						dataform = child
						break
				break

		if not hasattr(self.pytrans, "legacycon"):
			self.pytrans.discovery.sendIqError(to=to, fro=config.jid, ID=ID, xmlns="jabber:iq:search", etype="cancel", condition="bad-request")

		if dataform:
			self.pytrans.legacycon.doSearch(dataform, iq).addCallback(self.gotSearchResponse)
		else:
			self.pytrans.discovery.sendIqError(to=to, fro=config.jid, ID=ID, xmlns="jabber:iq:search", etype="retry", condition="bad-request")

	def gotSearchResponse(self, iq):
		debug.log("SearchFactory: Sending search response %s" % iq.toXml())
		self.pytrans.send(iq)
