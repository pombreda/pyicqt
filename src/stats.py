# Copyright 2005 Daniel Henninger <jadestorm@nc.rr.com>.
# Licensed for distribution under the GPL version 2, check COPYING for details

incmessages = 0
outmessages = 0
totalsess = 0
maxsess = 0
sessionstats = { }

def sessionSetup(jid):
	sessionstats[jid] = { }
	sessionstats[jid]['incmessages'] = 0
	sessionstats[jid]['outmessages'] = 0
	sessionstats[jid]['connections'] = 0

def sessionUpdate(jid, setting, value):
	if (not sessionstats.has_key(jid)):
		sessionSetup(jid)
	sessionstats[jid][setting] += value
