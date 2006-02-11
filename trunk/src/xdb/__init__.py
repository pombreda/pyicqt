# Copyright 2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import os
import debug
from config import xdbDriver

try:
	exec("from %s import XDB, housekeep" % xdbDriver)
	debug.log("Using XDB driver %s" % xdbDriver)
except:
	print("No valid XDB driver specified, exiting...")
	raise
	os._exit(-1)
