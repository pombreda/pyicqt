# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import os
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
if(config.tracebackDebug):
	rollingStock = utils.RollingStock(100)

def reopenFile(first=False):
	global debugFile
	if(debugFile or first):
		if(debugFile): debugFile.close()

		try:
			debugFile = open(utils.doPath(config.debugLog), 'a')
		except:
			print "Error opening debug log debugFile. Exiting..."
			os.abort()


def flushDebugSmart():
	global rollingStack
	if(config.debugSmart):
		debugFile.write(rollingStack.grabAll())
		rollingStack.flush()
		debugFile.flush()


if(config.debugOn):
	if(len(config.debugLog) > 0):
		reopenFile(True)
		def log(data, wtime=True):
			text = ""
			if(wtime):
				text += time.strftime("[%Y-%m-%d %H:%M:%S] ")
			text += data + "\n"
			if(config.tracebackDebug):
				rollingStock.push(text)
			else:
				debugFile.write(text)
				debugFile.flush()
	else:
		def log(data, wtime=True):
			text = ""
			if(wtime):
				text += time.strftime("[%Y-%m-%d %H:%M:%S] ")
			text += data
			if(config.tracebackDebug):
				rollingStock.push(text)
			else:
				print text
	log("Debug logging enabled.")
else:
	def log(data):
		pass


def write(data):
	# So that I can pass this module to twisted.python.failure.Failure.printDetailedTraceback() as a file
	data = data.rstrip()
	log(data)
