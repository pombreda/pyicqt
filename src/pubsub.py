# Copyright 2004-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from tlib.twistwrap import Element, jid
from twisted.internet import reactor, task
import config
import lang
from debug import LogEvent, INFO, WARN, ERROR
import globals
import os

SPOOL_UMASK = 0077

class PublishSubscribe:
	def __init__(self, pytrans):
		LogEvent(INFO)
		self.pytrans = pytrans
		self.storage = PubSubStorage()

		# Add disco entries without handlers.  We're going to set up
		# our own general handler, we'll do that in a moment.
		self.pytrans.disco.addFeature(globals.PUBSUB, None, config.jid)
		self.pytrans.disco.addFeature(globals.PUBSUBPEP, None, config.jid)

		# Set up the pubsub prefix handler.
		self.pytrans.iq.addHandler(globals.PUBSUB, self.incomingIq, prefix=1)

	def incomingIq(self, el):
		itype = el.getAttribute("type")
		fro = el.getAttribute("from")
		froj = jid.JID(fro)
		to = el.getAttribute("to")
		toj = jid.JID(to)
		ID = el.getAttribute("id")

	def localPublish(self, jid, node, itemid, el):
		self.storage.setItem(jid, node, itemid, el)



class PubSubStorage:
	""" Manages pubsub nodes on disk. Nodes are stored according to
	their jid and node.  The layout is config.spooldir / config.jid / pubsub / pubsub jid / node.
        That said, nodes can also have /'s in them, so we will utilize the
        file system to store these in a 'nice' layout. """


	def dir(self, jid, node):
		""" Returns the full path to the directory that a 
		particular key is in. Creates that directory if it doesn't already exist. """
		X = os.path.sep
		d = os.path.abspath(config.spooldir) + X + config.jid + X + "pubsub" + X + utils.mangle(jid) + X + self.nodeToPath(node) + X
		prev_umask = os.umask(SPOOL_UMASK)
		if not os.path.exists(d):
			os.makedirs(d)
		os.umask(prev_umask)
		return d

	def nodeToPath(self, node):
		X = os.path.sep
		path = node.replace('//', X+'_'+X).replace('/', X)
		return path

	def pathToNode(self, path):
		X = os.path.sep
		node = path.replace(X, '/').replace(X+'_'+X, '//')
		return node
	
	def setItem(self, jid, node, itemid, el):
		""" Writes an item to disk according to its jid, node, and
		itemid.  Returns nothing. """
		LogEvent(INFO)
		prev_umask = os.umask(SPOOL_UMASK)
		try:
			f = open(self.dir(jid, node) + itemid + ".xml", 'wb')
			f.write(el.toXml())
			f.close()
		except IOError, e:
			LogEvent(WARN, msg="IOError writing to node %r - %r" % (jid, node))
		os.umask(prev_umask)
	
	def getItem(self, jid, node, itemid):
		""" Loads the item from a node from disk and returns an element """
		try:
			filename = self.dir(jid, node) + itemid + ".xml"
			if os.path.isfile(filename):
				LogEvent(INFO, msg="Getting item %r - %r" % (node, itemid))
				document = utils.parseFile(filename)
				return document
			else:
				LogEvent(INFO, msg="Avatar not found %r" % (key))
		except IOError, e:
			LogEvent(INFO, msg="IOError reading item %r - %r" % (node, itemid))
