import time
import traceback
import debug
import sys

class ExceptionHook:
	def __init__(self):
		debug.log("Init ExceptionHook")

	def __call__(self, etype, evalue, etraceback):
		debug.log("[=============================== BEGIN EXCEPTION ==============================]", wtime=False)
		debug.log("Exception Time: %s" % (time.strftime("%Y-%m-%d %H:%M:%S")), wtime=False)
		debug.log("Exception Type: %s" % (etype), wtime=False)
		debug.log("Exception Summary: %s" % (evalue), wtime=False)
		debug.log("Exceptions can be handy in debugging.  Please report this to the developers.", wtime=False)
		tba = traceback.format_exception(etype,evalue,etraceback)
		debug.log("[================================== STACKTRACE ================================]", wtime=False)
		for i in tba:
			debug.log("%s" % (i), wtime=False)
		debug.log("[================================ END EXCEPTION ===============================]", wtime=False)

sys.excepthook = ExceptionHook()
