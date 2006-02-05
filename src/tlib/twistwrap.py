# Copyright 2006 Daniel Henninger <jadestorm@nc.rr.com>.
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.python import log

checkTwistedCached = None
def checkTwisted():
	""" Returns False if we're using an old version that needs tlib, otherwise returns True """
	global checkTwistedCached
	if checkTwistedCached == None:
		import twisted.copyright
		checkTwistedCached = (VersionNumber(twisted.copyright.version) >= VersionNumber("2.0.0"))
	return checkTwistedCached

class VersionNumber:
	def __init__(self, vstring):
		self.varray = [0]
		index = 0 
		flag = True
		for c in vstring:
			if c == '.':
				self.varray.append(0)
				index += 1
				flag = True
			elif c.isdigit() and flag:
				self.varray[index] *= 10
				self.varray[index] += int(c)
			else:
				flag = False
	
	def __cmp__(self, other):
		i = 0
		while(True):
			if i == len(other.varray):
				if i < len(self.varray):
					return 1
				else:
					return 0
			if i == len(self.varray):
				if i < len(other.varray):
					return -1
				else:
					return 0

			if self.varray[i] > other.varray[i]:
				return 1
			elif self.varray[i] < other.varray[i]:
				return -1

			i += 1



# Suppress the annoying warning we get with Twisted 1.3
import warnings, re
warnings.filters.append(("ignore", None, UserWarning, re.compile("twisted.words.__init__"), 21))

try:
	log.msg("Trying to import XML DOM")
	from twisted.words.xish.domish import SuxElementStream, Element, unescapeFromXml, elementStream
	from twisted.words.jabber import xmlstream
	from twisted.words.protocols.jabber import jid, component, client, jstrports
	jid.intern = jid.internJID # This got renamed for some reason
	log.msg("Using Twisted >= 2.0, Words >= 0.3, Words DOM")
except ImportError:
	try:
		log.msg("Checking Twisted version...")
		if checkTwisted():
			from twisted.xish.domish import SuxElementStream, Element, unescapeFromXml, elementStream
			from twisted.xish import xmlstream
			from twisted.words.protocols.jabber import jid, component, client, jstrports
			jid.intern = jid.internJID # This got renamed for some reason
			log.msg("Using Twisted >= 2.0, Words < 0.3, Twisted DOM")
		else:
			from tlib.domish import SuxElementStream, Element, unescapeFromXml, elementStream
			from tlib import xmlstream
			from tlib.jabber import jid, component, client, jstrports
			log.msg("Using Twisted < 2.0, Internal patched DOM")
	except ImportError:
		print "Could not find the XML DOM. If you're using Twisted 2.x make sure you have twisted.words installed."
		raise
