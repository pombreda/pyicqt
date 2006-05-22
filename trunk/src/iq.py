# Copyright 2004-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from tlib.twistwrap import Element, jid
from twisted.internet.defer import Deferred
from twisted.internet import reactor
from debug import LogEvent, INFO, WARN, ERROR
import lang

class IqHandler:
	"""
	Handles everything IQ related. You can send IQ stanzas and receive
	a Deferred to notify you when a response comes, or if there's a timeout.
	"""

	def __init__ (self, pytrans):
		LogEvent(INFO)
		self.pytrans = pytrans
		self.prefixhandlers = {} # A dict indexed by namespace prefix of handlers to fire given a starts-with match
		self.handlers = {} # A dict indexed by namespace of handlers to fire given a particular namespace
		self.deferredIqs = {} # A dict indexed by (jid, id) of deferreds to fire

	def sendIq(self, el, timeout=15):
		"""
		Used for sending IQ packets.  The id attribute for the IQ will
		be autogenerated if it is not there yet.  Returns a deferred
		which will fire with the matching IQ response as it's sole
		argument.
		"""

		def checkDeferred():
			if not d.called:
				d.errback(Exception("Timeout"))
				del self.deferredIqs[(jid, ID)]

		jid = el.getAttribute("to")
		ID = el.getAttribute("id")
		if not ID:
			ID = self.pytrans.makeMessageID()
			el.attributes["id"] = ID
		self.pytrans.send(el)
		d = Deferred()
		self.deferredIqs[(jid, ID)] = d
		reactor.callLater(timeout, checkDeferred)
		return d

	def onIq(self, el):
		""" Decides what to do with an IQ """
		fro = el.getAttribute("from")
		to = el.getAttribute("to")
		ID = el.getAttribute("id")
		iqType = el.getAttribute("type")
		ulang = utils.getLang(el)
		try: # StringPrep
			froj = jid.JID(fro)
			to = jid.JID(to).full()
		except Exception, e:
			LogEvent(INFO, msg="Dropping IQ because of stringprep error")

		# Check if it's a response to a sent IQ
		if self.deferredIqs.has_key((fro, ID)) and (iqType == "error" or iqType == "result"):
			LogEvent(INFO, msg="Doing callback")
			self.deferredIqs[(fro, ID)].callback(el)
			del self.deferredIqs[(fro, ID)]
			return

		if not (iqType == "get" or iqType == "set"): return # Not interested

		LogEvent(INFO, msg="Looking for handler")
		for query in el.elements():
			xmlns = query.uri
			node = query.getAttribute("node")

			if self.handlers.has_key(xmlns):
				LogEvent(INFO, msg="Namespace handler found")
				handler = self.handlers[xmlns]
				if handler:
					handler(el)
					return

			for prefix in self.prefixhandlers.keys():
				if xmlns.startswith(prefix):
					LogEvent(INFO, msg="Namespace prefix handler found")
					handler = self.prefixhandlers[prefix]
					if handler:
						handler(el)
						return

			# Still hasn't been handled
			LogEvent(WARN, msg="Unknown Iq Request")
			self.sendIqError(to=fro, fro=to, ID=ID, xmlns=xmlns, etype="cancel", condition="feature-not-implemented")

	def sendIqError(self, to, fro, ID, xmlns, etype, condition):
		""" Sends an IQ error response. See the XMPP RFC for details on the fields. """
		#debug.log("Sending IQ Error: %r %r %r %r %r" % (to,fro,xmlns,etype,condition))
		LogEvent(INFO)
		el = Element((None, "iq"))
		el.attributes["to"] = to
		el.attributes["from"] = fro
		if ID:
			el.attributes["id"] = ID
		el.attributes["type"] = "error"
		error = el.addElement("error")
		error.attributes["type"] = etype
		error.attributes["code"] = str(utils.errorCodeMap[condition])
		cond = error.addElement(condition)
		self.pytrans.send(el)

	def addHandler(self, ns, handler, prefix=0):
		"""
		Adds a namespace handler to the handler pool.
		If prefix is true, match at beginning of namespace.
		"""
		LogEvent(INFO)
		if prefix:
			self.prefixhandlers[ns] = handler
		else:
			self.handlers[ns] = handler
