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



if(config.debugOn):
	if(len(config.debugLog) > 0):
		try:
			file = open(config.debugLog, 'a')
		except:
			print "Error opening debug log file. Exiting..."
			os.abort()
		def log(data, wtime=True):
			if(wtime):
				file.write(time.strftime("%D - %H:%M:%S - "))
			#file.write(utils.latin1(data) + "\n")
			file.write(data + "\n")
			file.flush()
	else:
		def log(data, wtime=True):
			if(wtime):
				print time.strftime("%D - %H:%M:%S - "),
			#print utils.latin1(data)
			print data
	log("Debug logging enabled.")
else:
	def log(data):
		pass


def write(data):
	# So that I can pass this module to twisted.python.failure.Failure.printDetailedTraceback() as a file
	data = data.rstrip()
	log(data)

