# Copyright 2004 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.web.microdom import Element
from twisted.internet import protocol, reactor, defer
#from twisted.protocols import oscar
from tlib import oscar
from twisted.python import log
import config
import utils
import debug
import sys, warnings, pprint



#############################################################################
# BOSConnection
#############################################################################
class B(oscar.BOSConnection):
	def __init__(self,username,cookie,icqcon):
		self.icqcon = icqcon
		self.icqcon.bos = self
		self.session = icqcon.session  # convenience
		self.capabilities = [oscar.CAP_CHAT]
		oscar.BOSConnection.__init__(self,username,cookie)

	def initDone(self):
		self.requestSelfInfo().addCallback(self.gotSelfInfo)
		self.requestSSI().addCallback(self.gotBuddyList)
		debug.log("B: initDone %s for %s" % (self.username,self.session.jabberID))

	def updateBuddy(self, user):
		from glue import icq2jid

		debug.log("B: updateBuddy %s" % (user))
		buddyjid = icq2jid(user.name)
		ptype = None
		show = None
		status = None
		if (user.flags.count("away")):
			self.getAway(user.name).addCallback(self.sendAwayPresence, user)
		else:
			self.session.sendPresence(to=self.session.jabberID, fro=buddyjid, show=show, status=status, ptype=ptype)
			self.icqcon.contacts.updateSSIContact(user.name, presence=ptype, show=show, status=status)

	def offlineBuddy(self, user):
		from glue import icq2jid

		debug.log("B: offlineBuddy %s" % (user.name))
		buddyjid = icq2jid(user.name)
		show = None
		status = None
		ptype = "unavailable"
		self.session.sendPresence(to=self.session.jabberID, fro=buddyjid, show=show, status=status, ptype=ptype)

	def receiveMessage(self, user, multiparts, flags):
		from glue import icq2jid

		debug.log("B: receiveMessage %s %s %s %s %s" % (self.session.jabberID, self.name, user.name, multiparts, flags))
		sourcejid = icq2jid(user.name)
		text = multiparts[0][0]
		text = text.decode("utf-8", "replace")
		text = text.strip()
		self.session.sendMessage(to=self.session.jabberID, fro=sourcejid, body=text, mtype="chat")

	def receiveSendFileRequest(self, user, file, description, cookie):
		debug.log("B: receiveSendFileRequest")


	# Callbacks
	def sendAwayPresence(self, msg, user):
		from glue import icq2jid

		buddyjid = icq2jid(user.name)
		ptype = None
		show = "away"
		status = msg
		self.session.sendPresence(to=self.session.jabberID, fro=buddyjid, show=show, status=status, ptype=ptype)
		self.icqcon.contacts.updateSSIContact(user.name, presence=ptype, show=show, status=status)

	def gotSelfInfo(self, user):
		debug.log("B: gotSelfInfo: %s" % (user.__dict__))
		self.name = user.name

	def gotBuddyList(self, l):
		debug.log("B: gotBuddyList: %s" % (str(l)))
		self.ssigroups = list()
		if (l is not None):
			for g in l[0]:
				debug.log("B: gotBuddyList found group %s" % (g.name))
				self.ssigroups.append(g)
				for u in g.users:
					debug.log("B: got user %s from group %s" % (u.name, g.name))
					self.icqcon.contacts.updateSSIContact(u.name, skipsave=True)
		self.icqcon.contacts.saveXDBBuddies()
		self.activateSSI()
		self.setIdleTime(0)
		self.clientReady()
		self.session.ready = True
		self.session.sendPresence(to=self.session.jabberID, fro=config.jid, show=self.icqcon.savedShow, status=self.icqcon.savedFriendly)
		if (self.icqcon.savedShow in ["online", None]):
			self.icqcon.setAway(None)
		else:
			self.icqcon.setAway(self.icqcon.savedFriendly)


#############################################################################
# Oscar Authenticator
#############################################################################
class OA(oscar.OscarAuthenticator):
	def __init__(self,username,password,icqcon,deferred=None,icq=1):
		self.icqcon = icqcon
		self.BOSClass = B
		oscar.OscarAuthenticator.__init__(self,username,password,deferred,icq)

	def connectToBOS(self, server, port):
		c = protocol.ClientCreator(reactor, self.BOSClass, self.username, self.cookie, self.icqcon)
		return c.connectTCP(server, int(port))



#############################################################################
# ICQConnection
#############################################################################
class ICQConnection:
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.reactor = reactor
		self.contacts = ICQContacts(self.session)
		self.deferred = defer.Deferred()
		self.deferred.addErrback(self.errorCallback)
		#hostport = ("login.icq.com", 5238)
		hostport = ("login.icq.com", 5190)
		debug.log("ICQConnection: client creation for %s" % (self.session.jabberID))
		self.oa = OA
		self.creator = protocol.ClientCreator(self.reactor, self.oa, self.username, self.password, self, deferred=self.deferred, icq=1)
		debug.log("ICQConnection: connect tcp")
		self.creator.connectTCP(*hostport)

		debug.log("ICQConnection: \"%s\" created" % (self.username))
	
	def setAway(self, awayMessage=None):
		debug.log("ICQConnection: setAway %s" % (awayMessage))
		if (not self.session.ready or not hasattr(self, "bos")):
			return

		self.bos.setAway(awayMessage)

	def sendMessage(self, target, message):
		from glue import jid2icq

		scrnname = jid2icq(target)
		debug.log("ICQConnection: sendMessage %s %s" % (scrnname, message))
		encoded = message.encode("iso-8859-1", "replace")
		if (self.session.ready and hasattr(self, "bos")):
			self.bos.sendMessage(scrnname, encoded)
		else:
			debug.log("ICQConnection: not logged in yet")
			if (hasattr(self.session, "jabberID")):
				self.session.sendMessage(to=self.session.jabberID, fro=config.jid, body="You are not currently logged into this transport.  Please log in again.", mtype="chat")
			return

	def resendBuddies(self, resource):
		from glue import icq2jid
		debug.log("ICQConnection: resendBuddies %s" % (resource))
		if (not hasattr(self, "contacts")):
			return

		for c in self.contacts.ssicontacts.keys( ):
			debug.log("ICQConnection: resending buddy of %s" % (c))
			jid = icq2jid(c)
			show = self.contacts.ssicontacts[c]['show']
			status = self.contacts.ssicontacts[c]['status']
			ptype = self.contacts.ssicontacts[c]['presence']
			self.session.sendPresence(to=self.session.jabberID, fro=jid, show=show, status=status, ptype=ptype)

	def getvCard(self, vcard, user):
		debug.log("ICQConnection: getvCard %s" % (user))
		d = defer.Deferred()
		self.bos.getMetaInfo(user).addCallback(self.gotvCard, user, vcard, d)
		return d

	def gotvCard(self, userinfo, uin, vcard, d):
		debug.log("ICQConnection: gotvCard: %s" % (userinfo))

		fn = vcard.addElement("FN")
		fn.addContent(userinfo[1]+" "+userinfo[2])
		n = vcard.addElement("N")
		given = n.addElement("GIVEN")
		given.addContent(userinfo[1])
		family = n.addElement("FAMILY")
		family.addContent(userinfo[2])
		middle = n.addElement("MIDDLE")
		nickname = vcard.addElement("NICKNAME")
		nickname.addContent(userinfo[0])
		email = vcard.addElement("EMAIL")
		email.addElement("INTERNET")
		email.addElement("PREF")
		emailid = email.addElement("USERID")
		emailid.addContent(userinfo[3])
		jabberid = vcard.addElement("JABBERID")
		jabberid.addContent(uin+"@"+config.jid)

		d.callback(vcard)

	def removeMe(self):
		from glue import icq2jid
		debug.log("ICQConnection: removeMe")
		if (not hasattr(self, "bos")):
			return

		self.bos.stopKeepAlive()
		self.bos.disconnect()

		if (not hasattr(self, "contacts")):
			return

		for c in self.contacts.ssicontacts.keys( ):
			if (self.contacts.ssicontacts[c]['presence'] == "unavailable"):
				continue

			debug.log("ICQConnection: sending offline for %s" % (c))
			jid = icq2jid(c)
			show = None
			status = None
			ptype = "unavailable"
			self.session.sendPresence(to=self.session.jabberID, fro=jid, show=show, status=status, ptype=ptype)

	def jabberSubscriptionReceived(self, to, subtype):
		debug.log("ICQConnection: Session \"%s\" - jabberSubscriptionReceived(\"%s\", \"%s\")" % (self.session.jabberID, to, subtype))

		def updatePresence(ptype): # Convenience
			self.session.sendPresence(to=self.session.jabberID, fro=to, ptype=ptype)

		if(to.find('@') > 0): # For contacts
			from glue import jid2icq

			userHandle = jid2icq(to)

			if(subtype == "subscribe"):
				# User wants to subscribe to contact's presence
				debug.log("ICQConnection: Subscribe request received.")
				def cb(arg=None):
					updatePresence("subscribed")

				if (not hasattr(self, "bos")):
					debug.log("Not properly logged in yet")
					if (hasattr(self.session, "jabberID")):
						self.session.sendMessage(to=self.session.jabberID, fro=config.jid, body="You are not currently logged into this transport.  Please log in again.", mtype="chat")
					return

				savethisgroup = None
				for g in self.bos.ssigroups:
					if (g.name == "General"):
						debug.log("Located group %s" % (g.name))
						savethisgroup = g

				if (savethisgroup is None):
					debug.log("Need to add a new group")
					return

				newUser = oscar.SSIBuddy(userHandle)
				newUserID = len(savethisgroup.users)+1
				savethisgroup.addUser(newUserID, newUser)

				debug.log("Adding item to SSI")
				self.bos.startModifySSI()
				self.bos.addItemSSI(newUser).addCallback(cb)
				self.bos.modifyItemSSI(savethisgroup)
				self.bos.endModifySSI()

				self.contacts.updateSSIContact(userHandle)

			elif(subtype == "subscribed"):
				# The user has granted this contact subscription
				debug.log("ICQConnection: Subscribed request received.")
				pass

			elif(subtype == "unsubscribe"):
				# User wants to unsubscribe to this contact's presence. (User is removing the contact from their list)
				debug.log("ICQConnection: Unsubscribe request received.")
				def cb(arg=None):
					updatePresence("unsubscribed")

				savethisuser = None
				for g in self.bos.ssigroups:
					for u in g.users:
						debug.log("Comparing %s and %s" % (u.name.lower(), userHandle))
						if (u.name.lower() == userHandle):
							debug.log("Located user %s" % (u.name))
							savethisuser = u

				if (savethisuser is None):
					debug.log("Did not find user")
					return

				self.bos.startModifySSI()
				self.bos.delItemSSI(savethisuser).addCallback(cb)
				self.bos.endModifySSI()

                        elif(subtype == "unsubscribed"):
                                # The user wants to remove this contact's authorisation. Contact will no longer be able to see user
				debug.log("ICQConnection: Unsubscribed request received.")
				pass

                else: # The user wants to change subscription to the transport
                        if(subtype == "subscribe"):
                                updatePresence("subscribed")

                        elif(subtype == "subscribed"):
                                return # Nothing to do

                        elif(subtype == "unsubscribe" or subtype == "unsubscribed"):
                                # They want to unregister. Ok, we can do that
                                jid = self.session.jabberID
				debug.log("Subscriptions: Session \"%s\" is about to be unregistered" % (jid))
				self.session.pytrans.registermanager.removeRegInfo(jid)
				debug.log("Subscriptions: Session \"%s\" has been unregistered" % (jid))


	# Callbacks
	def errorCallback(self, result):
		debug.log("ICQConnection: errorCallback %s" % (result.getErrorMessage()))
		errmsg = result.getErrorMessage()
		errmsgs = errmsg.split("'")
		message = "Authentication Error!"
		if (errmsgs[1]):
			message = message+"\n"+errmsgs[1]
		if (errmsgs[3]):
			message = message+"\n"+errmsgs[3]
		self.session.sendMessage(to=self.session.jabberID, fro=config.jid, body=message, mtype="chat")

		self.session.removeMe()



#############################################################################
# ICQContacts
#############################################################################
class ICQContacts:
	def __init__(self, session):
		self.session = session
		self.ssicontacts = { }
		self.xdbcontacts = self.getXDBBuddies()
		self.xdbchanged = False

	def updateSSIContact(self, contact, presence="unavailable", show=None, status=None, skipsave=False):
		debug.log("ICQContacts: updating contact %s" % (contact.lower()))
		self.ssicontacts[contact.lower()] = {
			'presence': presence,
			'show': show,
			'status': status
		}

		if (not self.xdbcontacts.count(contact.lower())):
			from glue import icq2jid
			self.session.sendRosterImport(icq2jid(contact), "subscribe", "both", contact)
			self.xdbcontacts.append(contact.lower())
			self.xdbchanged = True
			if (not skipsave):
				self.saveXDBBuddies()

	def getXDBBuddies(self):
		debug.log("ICQContacts: getXDBBuddies %s %s" % (config.jid, self.session.jabberID))
		bl = list()
		result = self.session.pytrans.xdb.request(self.session.jabberID, "jabber:iq:roster")
		if (result == None):
			debug.log("ICQContacts: getXDBBuddies unable to get list, or empty")
			return bl

		for child in result.childNodes:
			try:
				if(child.tagName == "item"):
					bl.append(child.attributes["jid"])
			except AttributeError:
				continue
		return bl

	def saveXDBBuddies(self):
		debug.log("ICQContacts: setXDBBuddies %s %s" % (config.jid, self.session.jabberID))
		if (not self.xdbchanged):
			debug.log("ICQContacts: nothing has changed, no need to save")
			return

		newXDB = Element("query")
		newXDB.namespace = "jabber:iq:roster"

		for c in self.xdbcontacts:
			try:
				item = Element("item")
				item.setAttribute("jid", c)
				newXDB.appendChild(item)

			except:
				pass

		self.session.pytrans.xdb.set(self.session.jabberID, "aimtrans:roster", newXDB)
		self.xdbchanged = False
		debug.log("ICQContacts: contacts saved")
