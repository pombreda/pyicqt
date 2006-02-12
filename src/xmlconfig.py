# Copyright 2005-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from tlib.twistwrap import Element
from debug import LogEvent, INFO, WARN, ERROR
import config
import sys
if type(True) != bool: from bool import bool

def invalidError(text):
	print text
	print "Exiting..."
	sys.exit(1)

def importFile(conffile):
	#if conffile[0] != "/":
	#	conffile = "../"+conffile

	try:
		document = utils.parseFile(conffile)
	except Exception, e:
		invalidError("Error parsing configuration file: " + str(e))

	for child in document.elements():
		tag = child.name
		cdata = child.__str__()
		children = [x for x in child.elements()]
		if not hasattr(config, tag):
			LogEvent(WARN, "", "Ignoring unrecognized configuration option %r" % tag)
		elif type(getattr(config, tag)) == dict:
			# For options like <settings><username>blar</username><password>foo</password></settings>
			try:
				if not cdata.isspace():
					invalidError("Tag %r in your configuration file should be a dictionary (ie, must have subtags)." % (tag))
				myDict = getattr(config, tag)
				for child in children:
					n = child.name
					s = child.__str__()
					myDict[n] = s
					LogEvent(INFO, "", "Adding %r=%r to config dictionary %r" % (n, s, tag))
			except AttributeError:
				LogEvent(WARN, "", "Ignoring configuration option %r" % (tag))
		elif type(getattr(config, tag)) == list:
			# For options like <admins><jid>user1@host.com</jid><jid>user2@host.com</jid></admins>
			try:
				if not cdata.isspace():
					invalidError("Tag %r in your configuration file should be a list (ie, must have subtags)." % (tag))
				myList = getattr(config, tag)
				for child in children:
					s = child.__str__()
					LogEvent(INFO, "", "Adding %r to config list %r" % (s, tag))
					myList.append(s)
			except AttributeError:
				LogEvent(WARN, "", "Ignoring configuration option %r" % (tag))
		elif type(getattr(config, tag)) == str:
			# For config options like <ip>127.0.0.1</ip>
			try:
				if not cdata:
					invalidError("Tag %r in your configuration file should be a string (ie, must have cdata)." % (tag))
				LogEvent(INFO, "", "Setting config option %r = %r" % (tag, cdata))
				setattr(config, tag, cdata)
			except AttributeError:
				LogEvent(WARN, "", "Ignoring configuration option %r" % (tag))
		elif type(getattr(config, tag)) == bool:
			# For config options like <crossChat/>
			try:
				if cdata:
					invalidError("Tag %r in your configuration file should be a boolean (ie, no cdata)." % (tag))
				LogEvent(INFO, "", "Enabling config option %r" % (tag))
				setattr(config, tag, True)
			except AttributeError:
				LogEvent(WARN, "", "Ignoring configuration option %r" % (tag))
		else:
			LogEvent(WARN, "", "Ignoring unrecognized configuration option %r" % (tag))

def importOptions(options):
	for o in options:
		LogEvent(INFO, "", "Setting config option %r = %r" % (o, options[o]))
		setattr(config, o, options[o])

def Import(file = None, options = None):
	LogEvent(INFO, "", "Created configuration entity")
	if file != None:
		importFile(file)
	if options != None:
		importOptions(options)
