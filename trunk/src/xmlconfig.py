# Copyright 2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
if utils.checkTwisted():
	from twisted.xish.domish import Element
else:
	from tlib.domish import Element

import debug
import config
import sys
if type(True) != bool: from bool import bool

def invalidError(text):
	print text
	print "Exiting..."
	sys.exit(1)

def importFile(conffile):
	if conffile[0] != "/":
		conffile = "../"+conffile

	try:
		document = utils.parseFile(conffile)
	except Exception, e:
		invalidError("Error parsing configuration file: " + str(e))

	for child in document.elements():
		tag = child.name
		cdata = child.__str__()
		children = [x for x in child.elements()]
		if type(getattr(config, tag)) == dict:
			# For options like <settings><username>blar</username><password>foo</password></settings>
			try:
				if not cdata.isspace():
					invalidError("Tag %s in your configuration file should be a dictionary (ie, must have subtags)." % (tag))
				myDict = getattr(config, tag)
				for child in children:
					n = child.name
					s = child.__str__()
					myDict[n] = s
					debug.log("Adding %s=%s to config dictionary %s" % (n, s, tag))
			except AttributeError:
				debug.log("Ignoring configuration option %s" % (tag))
		elif type(getattr(config, tag)) == list:
			# For options like <admins><jid>user1@host.com</jid><jid>user2@host.com</jid></admins>
			try:
				if not cdata.isspace():
					invalidError("Tag %s in your configuration file should be a list (ie, must have subtags)." % (tag))
				myList = getattr(config, tag)
				for child in children:
					s = child.__str__()
					debug.log("Adding %s to config list %s" % (s, tag))
					myList.append(s)
			except AttributeError:
				debug.log("Ignoring configuration option %s" % (tag))
		elif type(getattr(config, tag)) == str:
			# For config options like <ip>127.0.0.1</ip>
			try:
				if not cdata:
					invalidError("Tag %s in your configuration file should be a string (ie, must have cdata)." % (tag))
				debug.log("Setting config option %s = %s" % (tag, cdata))
				setattr(config, tag, cdata)
			except AttributeError:
				debug.log("Ignoring configuration option %s" % (tag))
		elif type(getattr(config, tag)) == bool:
			# For config options like <crossChat/>
			try:
				if cdata:
					invalidError("Tag %s in your configuration file should be a boolean (ie, no cdata)." % (tag))
				debug.log("Enabling config option %s" % (tag))
				setattr(config, tag, True)
			except AttributeError:
				debug.log("Ignoring configuration option %s" % (tag))
		else:
			debug.log("Ignoring unrecognized configuration option %s" % (tag))

def importOptions(options):
	for o in options:
		debug.log("Setting config option %s = %s" % (o, options[o]))
		setattr(config, o, options[o])

def Import(file = None, options = None):
	debug.log("Config: Created configuration entity")
	if file != None:
		importFile(file)
	if options != None:
		importOptions(options)