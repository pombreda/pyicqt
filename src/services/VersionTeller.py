# Copyright 2004-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from tlib.twistwrap import Element, jid
from twisted.internet import reactor, task
import jabw
import legacy
import disco
import config
import lang
from debug import LogEvent, INFO, WARN, ERROR
import base64
import sys
import avatar
import globals

class VersionTeller:
	def __init__(self, pytrans):
		self.pytrans = pytrans
		self.pytrans.disco.addFeature(globals.IQVERSION, self.incomingIq, config.jid)
		self.pytrans.disco.addFeature(globals.IQVERSION, self.incomingIq, "USER")

	def incomingIq(self, el):
		eltype = el.getAttribute("type")
		if eltype != "get": return # Only answer "get" stanzas

		self.sendVersion(el)

	def sendVersion(self, el):
		LogEvent(INFO)
		iq = Element((None, "iq"))
		iq.attributes["type"] = "result"
		iq.attributes["from"] = el.getAttribute("to")
		iq.attributes["to"] = el.getAttribute("from")
		if el.getAttribute("id"):
			iq.attributes["id"] = el.getAttribute("id")
		query = iq.addElement("query")
		query.attributes["xmlns"] = globals.IQVERSION
		name = query.addElement("name")
		name.addContent(legacy.name)
		version = query.addElement("version")
		version.addContent(legacy.version)
		os = query.addElement("os")
		os.addContent("Python" + sys.version)

		self.pytrans.send(iq)
