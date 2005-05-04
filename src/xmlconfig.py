# Copyright 2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
if(utils.checkTwisted()):
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
	if (conffile[0] != "/"):
		conffile = "../"+conffile
	document = utils.parseFile(conffile)
	for child in document.elements():
		tag = child.name
		cdata = child.__str__()
		debug.log("Reading config option %s = %s" % (tag, cdata))
		if (cdata):
			# For config options like <ip>127.0.0.1</ip>
			try:
				if(type(getattr(config, tag)) != str):
					invalidError("Tag %s in your configuration file should be a boolean (ie, no cdata)." % (tag))
				setattr(config, tag, cdata)
			except AttributeError:
				debug.log("Ignoring configuration option %s" % (tag))
		else:
			# For config options like <crossChat/>
			try:
				if(type(getattr(config, tag)) != bool):
					invalidError("Tag %s in your configuration file should be a string (ie, must have cdata)." % (tag))
				setattr(config, tag, True)
			except AttributeError:
				debug.log("Ignoring configuration option %s" % (tag))

def importOptions(options):
	for o in options:
		debug.log("Setting config option %s = %s" % (o, options[o]))
		setattr(config, o, options[o])

def Import(file = None, options = None):
	debug.log("Config: Created configuration entity")
	if (file != None):
		importFile(file)
	if (options != None):
		importOptions(options)
