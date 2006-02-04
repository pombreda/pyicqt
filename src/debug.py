# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import os
import sys
import config
import utils
import time

""" A simple logging module. Use as follows.

> import debug
> debug.log("text string")

If debugging is enabled then the data will be dumped to a file
or the screen (whichever the user chose)
"""

debugFile = None
rollingStock = None
if config.tracebackDebug:
	rollingStock = utils.RollingStack(100)

def reopenFile(first=False):
	global debugFile
	if debugFile or first:
		if debugFile: debugFile.close()

		try:
			debugFile = open(utils.doPath(config.debugLog), 'a')
		except:
			print "Error opening debug log debugFile. Exiting..."
			os.abort()


def flushDebugSmart():
	global rollingStack
	if config.tracebackDebug:
		debugFile.write(rollingStack.grabAll())
		rollingStack.flush()
		debugFile.flush()


if config.debugOn:
	if len(config.debugLog) > 0:
		reopenFile(True)
		def log(data, wtime=True):
			try:
				text = ""
				if wtime:
					text += time.strftime("[%Y-%m-%d %H:%M:%S] ")
				text += data + "\n"
				if config.tracebackDebug:
					rollingStock.push(text)
				else:
					debugFile.write(text)
					debugFile.flush()
			except:
				debugFile.write("There was an error writing a log entry.  Entry skipped.")
				debugFile.flush()
	else:
		def log(data, wtime=True):
			try:
				text = ""
				if wtime:
					text += time.strftime("[%Y-%m-%d %H:%M:%S] ")
				text += data
				if config.tracebackDebug:
					rollingStock.push(text)
				else:
					print text
					sys.stdout.flush()
			except:
				print "There was an error writing a log entry.  Entry skipped."
				sys.stdout.flush()
	log("Debug logging enabled.")
else:
	def log(data):
		pass


def write(data):
	# So that I can pass this module to twisted.python.failure.Failure.printDetailedTraceback() as a file
	data = data.rstrip()
	log(data)

def warn(data):
	log("WARNING! " + data)
