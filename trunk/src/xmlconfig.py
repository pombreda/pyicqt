# Copyright 2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

from tlib.domish import parseText, Element
import debug
import config

def importFile(conffile):
	if (conffile[0] != "/"):
		conffile = "../"+conffile
	f = open(conffile)
	lines = f.readlines()
	f.close()
	file = ""
	for line in lines:
		file += line

	document = parseText(file)
	for child in document.elements():
		debug.log("Reading config option %s = %s" % (child.name, child.__str__()))
		setattr(config, child.name, child.__str__())

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
