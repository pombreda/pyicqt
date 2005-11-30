# Copyright 2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
if utils.checkTwisted():
	from twisted.xish.domish import Element
	from twisted.words.protocols.jabber import jid
else:
	from tlib.domish import Element
	from tlib.jabber import jid
import debug
import config
import disco
import lang
import re
import globals
from tlib import oscar



def sendCancellation(pytrans, node, el, sessionid=None):
	to = el.getAttribute("from")
	ID = el.getAttribute("id")
	ulang = utils.getLang(el)

	iq = Element((None, "iq"))
	iq.attributes["to"] = to
	iq.attributes["from"] = config.jid
	if ID:
		iq.attributes["id"] = ID
	iq.attributes["type"] = "result"

	command = iq.addElement("command")
	if sessionid:
		command.attributes["sessionid"] = sessionid
	else:
		command.attributes["sessionid"] = pytrans.makeMessageID()
	command.attributes["node"] = node
	command.attributes["xmlns"] = globals.COMMANDS
	command.attributes["status"] = "canceled"

	pytrans.send(iq)



def sendError(pytrans, node, el, errormsg, sessionid=None):
	to = el.getAttribute("from")
	ID = el.getAttribute("id")
	ulang = utils.getLang(el)

	iq = Element((None, "iq"))
	iq.attributes["to"] = to
	iq.attributes["from"] = config.jid
	if ID:
		iq.attributes["id"] = ID
	iq.attributes["type"] = "result"

	command = iq.addElement("command")
	if sessionid:
		command.attributes["sessionid"] = sessionid
	else:
		command.attributes["sessionid"] = pytrans.makeMessageID()
	command.attributes["node"] = node
	command.attributes["xmlns"] = globals.COMMANDS
	command.attributes["status"] = "completed"

	note = command.addElement("note")
	note.attributes["type"] = "error"
	note.addContent(errormsg)

	pytrans.send(iq)
