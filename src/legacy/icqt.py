# Copyright 2004 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.internet import protocol, reactor, defer
from tlib import oscar

import utils
if(utils.checkTwisted()):
	from twisted.xish.domish import Element
else:
	from tlib.domish import Element

from tlib import socks5, sockserror
from twisted.python import log
import config
import debug
import sys, warnings, pprint
import stats
import lang
import re


#############################################################################
# BOSConnection
#############################################################################
class B(oscar.BOSConnection):
	def __init__(self,username,cookie,icqcon):
		self.icqcon = icqcon
		self.authorizationRequests = [] # buddies that need authorization
		self.encoding = icqcon.encoding
		self.icqcon.bos = self
		self.session = icqcon.session  # convenience
		self.capabilities = [oscar.CAP_CHAT, oscar.CAP_UTF]
		self.statusindicators = oscar.STATUS_WEBAWARE
		if (config.crossChat):
			debug.log("B: __init__ adding cross chat")
			self.capabilities.append(oscar.CAP_CROSS_CHAT)
		if (config.socksProxyServer and config.socksProxyPort):
			self.socksProxyServer = config.socksProxyServer
			self.socksProxyPort = config.socksProxyPort
		oscar.BOSConnection.__init__(self,username,cookie)

	def initDone(self):
		self.requestSelfInfo().addCallback(self.gotSelfInfo)
		self.requestSSI().addCallback(self.gotBuddyList)
		debug.log("B: initDone %s for %s" % (self.username,self.session.jabberID))

	def gotUserInfo(self, id, type, userinfo):
		if userinfo:
			for i in range(len(userinfo)):
				userinfo[i] = userinfo[i].decode(self.encoding, "replace")
		if self.icqcon.userinfoCollection[id].gotUserInfo(id, type, userinfo):
			# True when all info packages has been received
			self.icqcon.gotvCard(self.icqcon.userinfoCollection[id])
			del self.icqcon.userinfoCollection[id]

	def buddyAdded(self, uin):
		from glue import icq2jid
		for g in self.ssigroups:
			for u in g.users:
				if u.name == uin:
					if u.authorized:
						self.session.sendPresence(to=self.session.jabberID, fro=icq2jid(uin), show=None, ptype="subscribed")
						return

	def gotAuthorizationRespons(self, uin, success):
		from glue import icq2jid
		debug.log("B: Authorization Respons: %s, %s"%(uin, success))
		if success:
			for g in self.ssigroups:
				for u in g.users:
					if u.name == uin:
						u.authorized = True
						u.authorizationRequestSent = False
						self.session.sendPresence(to=self.session.jabberID, fro=icq2jid(uin), show=None, ptype="subscribed")
						return
		else:
			for g in self.ssigroups:
				for u in g.users:
					if u.name == uin:
						u.authorizationRequestSent = False
			self.session.sendPresence(to=self.session.jabberID, fro=icq2jid(uin), show=None, status=None, ptype="unsubscribed")
 
	def gotAuthorizationRequest(self, uin):
		from glue import icq2jid
		debug.log("B: Authorization Request: %s"%uin)
		if not uin in self.authorizationRequests:
			self.authorizationRequests.append(uin)
			self.session.sendPresence(to=self.session.jabberID, fro=icq2jid(uin), ptype="subscribe")

	def youWereAdded(self, uin):
		from glue import icq2jid
		debug.log("B: %s added you to her/his contact list"%uin)
		self.session.sendPresence(to=self.session.jabberID, fro=icq2jid(uin), ptype="subscribe")

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
			self.icqcon.contacts.updateSSIContact(user.name, presence=ptype, show=show, status=status, ipaddr=user.icqIPaddy, lanipaddr=user.icqLANIPaddy, lanipport=user.icqLANIPport, icqprotocol=user.icqProtocolVersion)

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
		if user.name[0].isdigit():
			text = multiparts[0][0]
		else:
			text = oscar.dehtml(multiparts[0][0])
		if (len(multiparts[0]) > 1):
			if (multiparts[0][1] == 'unicode'):
				encoding = "utf-16be"
			else:
				encoding = self.encoding
		else:
			encoding = self.encoding
		debug.log("B: using encoding %s" % (encoding))
		text = text.decode(encoding, "replace")
		text = text.strip()
		self.session.sendMessage(to=self.session.jabberID, fro=sourcejid, body=text, mtype="chat")
		stats.incmessages += 1
		stats.sessionUpdate(self.session.jabberID, "incmessages", 1)

        def receiveTypingNotify(self, type, user):
		from glue import icq2jid

		debug.log("B: receiveTypingNotify %s from %s" % (type,hasattr(user,'name') and user.name or None))
		sourcejid = icq2jid(user.name)
		if (type == "begin"):
			self.session.sendTypingNotification(to=self.session.jabberID, fro=sourcejid, typing=True)
		elif (type == "idle"):
			self.session.sendTypingNotification(to=self.session.jabberID, fro=sourcejid, typing=False)
		elif (type == "finish"):
			self.session.sendTypingNotification(to=self.session.jabberID, fro=sourcejid, typing=False)

	def receiveSendFileRequest(self, user, file, description, cookie):
		debug.log("B: receiveSendFileRequest")


	# Callbacks
	def sendAwayPresence(self, msg, user):
		from glue import icq2jid

		buddyjid = icq2jid(user.name)
		ptype = None
		show = "away"
		status = msg[1]

		if status != None: 
			charset = "iso-8859-1"
			m = re.search('charset="(.+)"', msg[0])
			if m != None:
				charset = m.group(1)
				if charset == 'unicode-2-0':
					charset = 'utf-16be'
				elif charset == 'utf-8': pass
				elif charset == "us-ascii":
					charset = "iso-8859-1"
				else:
					debug.log( "unknown charset (%s) of buddy's away message" % msg[0] );
					charset = self.encoding
					status = msg[0] + ": " + status

			status = status.decode(charset, 'replace')
			debug.log( "dsh: away (%s, %s) message %s"
				% (charset, msg[0], status) )

		self.session.sendPresence(to=self.session.jabberID, fro=buddyjid, show=show, status=status, ptype=ptype)
		self.icqcon.contacts.updateSSIContact(user.name, presence=ptype, show=show, status=status, ipaddr=user.icqIPaddy, lanipaddr=user.icqLANIPaddy, lanipport=user.icqLANIPport, icqprotocol=user.icqProtocolVersion)

	def gotSelfInfo(self, user):
		debug.log("B: gotSelfInfo: %s" % (user.__dict__))
		self.name = user.name

	def gotBuddyList(self, l):
		debug.log("B: gotBuddyList: %s" % (str(l)))
		self.ssigroups = list()
		if (l is not None and l[0] is not None):
			for g in l[0]:
				debug.log("B: gotBuddyList found group %s" % (g.name))
				self.ssigroups.append(g)
				for u in g.users:
					debug.log("B: got user %s from group %s" % (u.name, g.name))
					self.icqcon.contacts.updateSSIContact(u.name, skipsave=True, nick=u.nick)
		self.icqcon.contacts.saveXDBBuddies()
		self.activateSSI()
		self.setProfile(None)
		self.setIdleTime(0)
		self.clientReady()
		self.session.ready = True
		tmpjid = config.jid
		if (self.session.registeredmunge):
			tmpjid = tmpjid + "/registered"
		self.session.sendPresence(to=self.session.jabberID, fro=tmpjid, show=self.icqcon.savedShow, status=self.icqcon.savedFriendly)
		if (self.icqcon.savedShow in ["online", "Online", None]):
			self.icqcon.setAway(None)
		else:
			self.icqcon.setAway(self.icqcon.savedFriendly)
		self.icqcon.setICQStatus(self.icqcon.savedShow)
		self.requestOffline()

	def connectionLost(self, reason):
		message = "ICQ connection lost! Reason: %s" % reason
		try:
			self.icqcon.alertUser(message)
		except:
			pass
		# Send error presence
		self.session.removeMe("wait", "remote-server-timeout", message)

		oscar.OscarConnection.connectionLost(self, reason)


#############################################################################
# Oscar Authenticator
#############################################################################
class OA(oscar.OscarAuthenticator):
	def __init__(self,username,password,icqcon,deferred=None,icq=1):
		self.icqcon = icqcon
		self.BOSClass = B
		oscar.OscarAuthenticator.__init__(self,username,password,deferred,icq)

	def connectToBOS(self, server, port):
		if config.socksProxyServer:
			c = socks5.ProxyClientCreator(reactor, self.BOSClass, self.username, self.cookie, self.icqcon)
			return c.connectSocks5Proxy(server, int(port), config.socksProxyServer, int(config.socksProxyPort), "OABOS")
		else:
			c = protocol.ClientCreator(reactor, self.BOSClass, self.username, self.cookie, self.icqcon)
			return c.connectTCP(server, int(port))



#############################################################################
# ICQConnection
#############################################################################
class ICQConnection:
	def __init__(self, username, password, encoding):
		self.username = username
		self.password = password
		self.encoding = encoding
		self.reactor = reactor
		self.contacts = ICQContacts(self.session, encoding)
		self.userinfoCollection = {}
		self.userinfoID = 0
		self.deferred = defer.Deferred()
		self.deferred.addErrback(self.errorCallback)
		hostport = (config.icqServer, int(config.icqPort))
		debug.log("ICQConnection: client creation for %s" % (self.session.jabberID))
		if config.socksProxyServer and config.socksProxyPort:
			self.oa = OA
			self.creator = socks5.ProxyClientCreator(self.reactor, self.oa, self.username, self.password, self, deferred=self.deferred, icq=1)
			debug.log("ICQConnection: connect via socks proxy")
			self.creator.connectSocks5Proxy(config.icqServer, int(config.icqPort), config.socksProxyServer, int(config.socksProxyPort), "ICQCONN")
		else:
			self.oa = OA
			self.creator = protocol.ClientCreator(self.reactor, self.oa, self.username, self.password, self, deferred=self.deferred, icq=1)
			debug.log("ICQConnection: connect direct tcp")
			self.creator.connectTCP(*hostport)

		debug.log("ICQConnection: \"%s\" created" % (self.username))
	
	def setAway(self, awayMessage=None):
		debug.log("ICQConnection: setAway %s" % (awayMessage))
		try:
			self.bos.setAway(awayMessage.encode(self.encoding, 'replace'))
		except AttributeError:
			#self.alertUser(lang.get(config.jid).sessionnotactive)
			pass

	def setICQStatus(self, status):
		debug.log("ICQConnection: setICQStatus %s" % (status))
		try:
			self.bos.setICQStatus(status)
		except AttributeError:
			#self.alertUser(lang.get(config.jid).sessionnotactive)
			pass

	def sendMessage(self, target, message):
		from glue import jid2icq
		try:
			stats.outmessages += 1
			stats.sessionUpdate(self.session.jabberID, "outmessages", 1)

			scrnname = jid2icq(target)
			debug.log("ICQConnection: sendMessage %s %s" % (scrnname, message))
			encoded = message.encode(self.encoding, "replace")
			debug.log("ICQConnection: sendMessage encoded %s" % (encoded))
			self.bos.sendMessage(scrnname, encoded, offline=1)
		except AttributeError:
			self.alertUser(lang.get(config.jid).sessionnotactive)

	def resendBuddies(self, resource):
		from glue import icq2jid
		debug.log("ICQConnection: resendBuddies %s" % (resource))
		try:
			for c in self.contacts.ssicontacts.keys( ):
				debug.log("ICQConnection: resending buddy of %s" % (c))
				jid = icq2jid(c)
				show = self.contacts.ssicontacts[c]['show']
				status = self.contacts.ssicontacts[c]['status']
				ptype = self.contacts.ssicontacts[c]['presence']
				self.session.sendPresence(to=self.session.jabberID, fro=jid, show=show, status=status, ptype=ptype)
		except AttributeError:
			return

        def sendTypingNotify(self, type, dest):
		from tlib.oscar import MTN_FINISH, MTN_IDLE, MTN_BEGIN
		from glue import jid2icq
		try:
			username = jid2icq(dest)
			debug.log("ICQConnection: sendTypingNotify %s to %s" % (type,username))
			if (type == "begin"):
				self.bos.sendTypingNotification(username, MTN_BEGIN)
			elif (type == "idle"):
				self.bos.sendTypingNotification(username, MTN_IDLE)
			elif (type == "finish"):
				self.bos.sendTypingNotification(username, MTN_FINISH)
		except AttributeError:
			self.alertUser(lang.get(config.jid).sessionnotactive)

	def getvCard(self, vcard, user):
		debug.log("ICQConnection: getvCard %s" % (user))
		if (not user.isdigit()):
			debug.log("ICQConnection: getvCard uin is not a number")
			return
		try:
			d = defer.Deferred()
			#self.bos.getMetaInfo(user).addCallback(self.gotvCard, user, vcard, d)
			self.userinfoID = (self.userinfoID+1)%256
			self.userinfoCollection[self.userinfoID] = UserInfoCollector(self.userinfoID, d, vcard, user)
			self.bos.getMetaInfo(user, self.userinfoID) #.addCallback(self.gotvCard, user, vcard, d)
			return d
		except AttributeError:
			self.alertUser(lang.get(config.jid).sessionnotactive)

	def gotvCard(self, usercol):
		debug.log("ICQConnection: gotvCard: %s" % (usercol.userinfo))
 
		if usercol != None and usercol.valid:
			vcard = usercol.vcard
			fn = vcard.addElement("FN")
			fn.addContent(usercol.first + " " + usercol.last)
			n = vcard.addElement("N")
			given = n.addElement("GIVEN")
			given.addContent(usercol.first)
			family = n.addElement("FAMILY")
			family.addContent(usercol.last)
			middle = n.addElement("MIDDLE")
			nickname = vcard.addElement("NICKNAME")
			nickname.addContent(usercol.nick)
			bday = vcard.addElement("BDAY")
			bday.addContent(usercol.birthday)
			desc = vcard.addElement("DESC")
			desc.addContent(usercol.about)
			try:
				c = self.contacts.ssicontacts[usercol.userinfo]
				desc.addContent("\n\n-----\n"+c['lanipaddr']+'/'+c['ipaddr']+':'+"%s"%(c['lanipport'])+' v.'+"%s"%(c['icqprotocol']))
			except:
				pass
			url = vcard.addElement("URL")
			url.addContent(usercol.homepage)

			# Home address
			adr = vcard.addElement("ADR")
			adr.addElement("HOME")
			street = adr.addElement("STREET")
			street.addContent(usercol.homeAddress)
			locality = adr.addElement("LOCALITY")
			locality.addContent(usercol.homeCity)
			region = adr.addElement("REGION")
			region.addContent(usercol.homeState)
			pcode = adr.addElement("PCODE")
			pcode.addContent(usercol.homeZIP)
			ctry = adr.addElement("CTRY")
			ctry.addContent(usercol.homeCountry)
			# home number
			tel = vcard.addElement("TEL")
			tel.addElement("VOICE")
			tel.addElement("HOME")
			telNumber = tel.addElement("NUMBER")
			telNumber.addContent(usercol.homePhone)
			tel = vcard.addElement("TEL")
			tel.addElement("FAX")
			tel.addElement("HOME")
			telNumber = tel.addElement("NUMBER")
			telNumber.addContent(usercol.homeFax)
			tel = vcard.addElement("TEL")
			tel.addElement("CELL")
			tel.addElement("HOME")
			number = tel.addElement("NUMBER")
			number.addContent(usercol.cellPhone)
			# email
			email = vcard.addElement("EMAIL")
			email.addElement("INTERNET")
			email.addElement("PREF")
			emailid = email.addElement("USERID")
			emailid.addContent(usercol.email)

			# work
			adr = vcard.addElement("ADR")
			adr.addElement("WORK")
			street = adr.addElement("STREET")
			street.addContent(usercol.workAddress)
			locality = adr.addElement("LOCALITY")
			locality.addContent(usercol.workCity)
			region = adr.addElement("REGION")

			region.addContent(usercol.workState)
			pcode = adr.addElement("PCODE")
			pcode.addContent(usercol.workZIP)
			ctry = adr.addElement("CTRY")
			ctry.addContent(usercol.workCountry)

			tel = vcard.addElement("TEL")
			tel.addElement("WORK")
			tel.addElement("VOICE")
			number = tel.addElement("NUMBER")
			number.addContent(usercol.workPhone)
			tel = vcard.addElement("TEL")
			tel.addElement("WORK")
			tel.addElement("FAX")
			number = tel.addElement("NUMBER")
			number.addContent(usercol.workFax)

			jabberid = vcard.addElement("JABBERID")
			jabberid.addContent(usercol.userinfo+"@"+config.jid)

			usercol.d.callback(vcard)
		elif usercol:
			usercol.d.callback(usercol.vcard)
		else:
			self.session.sendErrorMessage(self.session.jabberID, uin+"@"+config.jid, "cancel", "undefined-condition", "", "Unable to retrieve user information")
			# error of some kind

	def removeMe(self, etype=None, econdition=None, etext=None):
		from glue import icq2jid
		debug.log("ICQConnection: removeMe")
		try:
			self.bos.stopKeepAlive()
			self.bos.disconnect()
			for c in self.contacts.ssicontacts.keys( ):
				if (self.contacts.ssicontacts[c]['presence'] == "unavailable"):
					continue

				debug.log("ICQConnection: sending offline for %s" % (c))
				jid = icq2jid(c)
				show = None
				status = None
				ptype = "unavailable"
				if etype:
					ptype = "error"
				else:
					ptype = "unavailable"
				self.session.sendPresence(to=self.session.jabberID, fro=jid, show=show, status=status, ptype=ptype, etype=etype, econdition=econdition, etext=etext)
		except AttributeError:
			return

	def removeResource(self, resource):
		from glue import icq2jid
		debug.log("ICQConnection: removeResource %s" % (resource))
		try:
			for c in self.contacts.ssicontacts.keys( ):
				if (self.contacts.ssicontacts[c]['presence'] == "unavailable"):
					continue

				debug.log("ICQConnection: sending offline for %s" % (c))
				jid = icq2jid(c)
				show = None
				status = None
				ptype = "unavailable"
				self.session.sendPresence(to=self.session.jabberID+"/"+resource, fro=jid, show=show, status=status, ptype=ptype)
		except AttributeError:
			return

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

				try:
					for g in self.bos.ssigroups:
						for u in g.users:
							if u.name == userHandle:
								if (not u.authorizationRequestSent) and (not u.authorized):
									self.bos.sendAuthorizationRequest(userHandle, "Please authorize me!")
									u.authorizationRequestSent = True
									return
								else:
									cb()
									return

					savethisgroup = None
					groupName = "PyICQ-t Buddies"
					for g in self.bos.ssigroups:
						if (g.name == groupName):
							debug.log("Located group %s" % (g.name))
							savethisgroup = g

					if (savethisgroup is None):
						debug.log("Adding new group")
						newGroupID = self.generateGroupID()
						newGroup = oscar.SSIGroup(groupName, newGroupID, 0)
						self.bos.startModifySSI()
						self.bos.addItemSSI(newGroup)
						self.bos.endModifySSI()
						savethisgroup = newGroup
						self.bos.ssigroups.append(newGroup)

					group = self.findGroupByName(groupName)
					newUserID = self.generateBuddyID(group.groupID)
					newUser = oscar.SSIBuddy(userHandle, group.groupID, newUserID)
					savethisgroup.addUser(newUserID, newUser)


					debug.log("Adding item to SSI")
					self.bos.startModifySSI()
					self.bos.addItemSSI(newUser)
					self.bos.modifyItemSSI(savethisgroup)
					self.bos.endModifySSI()

					self.contacts.updateSSIContact(userHandle)
					updatePresence("subscribe")
				except AttributeError:
					self.alertUser(lang.get(config.jid).sessionnotactive)

			elif(subtype == "subscribed"):
				# The user has granted this contact subscription
				debug.log("ICQConnection: Subscribed request received.")
				try:
					if userHandle in self.bos.authorizationRequests:
						self.bos.sendAuthorizationRespons(userHandle, True, "OK")
						self.bos.authorizationRequests.remove(userHandle)
				except AttributeError:
					self.alertUser(lang.get(config.jid).sessionnotactive)

			elif(subtype == "unsubscribe" or subtype == "unsubscribed"):
				# User wants to unsubscribe to this contact's presence. (User is removing the contact from their list)
				debug.log("ICQConnection: Unsubscribe(d) request received.")

				def cb(arg=None):
					updatePresence("unsubscribed")

				try:

					if userHandle in self.bos.authorizationRequests:
						self.bos.sendAuthorizationRespons(userHandle, False, "")
						self.bos.authorizationRequests.remove(userHandle)

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
					debug.log("ICQConnection: Removing %s (u:%d g:%d) from group %s"%(savethisuser.name, savethisuser.buddyID, savethisuser.groupID, savethisuser.group.name))
					de = self.bos.delItemSSI(savethisuser)
					de.addCallback(self.SSIItemDeleted, savethisuser)
					de.addCallback(cb)
					self.bos.endModifySSI()
				except AttributeError:
					self.alertUser(lang.get(config.jid).sessionnotactive)

                else: # The user wants to change subscription to the transport
			try:
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
			except AttributeError:
				self.alertUser(lang.get(config.jid).sessionnotactive)

	def SSIItemDeleted(self, x, user):
		c = 0
		for g in self.bos.ssigroups:
			c += 1
			for u in g.users:
				if u.name == user.name:
					g.users.remove(u)
					del g.usersToID[u]

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
		self.alertUser(message)

		# Send error presence
		self.session.removeMe("auth", "not-authorized", message)

	def findGroupByID(self, groupID):
		for x in self.bos.ssigroups:
			if x.groupID == groupID:
				return x

	def findGroupByName(self, groupName):
		for x in self.bos.ssigroups:
			if x.name == groupName:
				return x

	def generateGroupID(self):
		pGroupID = len(self.bos.ssigroups)
		while True:
			pGroupID += 1
			found = False
			for x in self.bos.ssigroups:
				if pGroupID == x.groupID:
					found = True
					break
			if not found: break
		return pGroupID

	def generateBuddyID(self, groupID):
		group = self.findGroupByID(groupID)
		pBuddyID = len(group.users)
		while True: # If all integers are taken we got a bigger problems 
			pBuddyID += 1
			found = False
			for x in group.users:
				if pBuddyID == x.buddyID:
					found = True
					break
			if not found: break
		return pBuddyID

	def alertUser(self, message):
		tmpjid = config.jid
		if (self.session.registeredmunge):
			tmpjid = tmpjid + "/registered"
		self.session.sendMessage(to=self.session.jabberID, fro=tmpjid, body=message, mtype="error")


#############################################################################
# ICQContacts
#############################################################################
class ICQContacts:
	def __init__(self, session, encoding):
		self.encoding = encoding
		self.session = session
		self.ssicontacts = { }
		self.xdbcontacts = self.getXDBBuddies()
		self.xdbchanged = False

	def updateSSIContact(self, contact, presence="unavailable", show=None, status=None, skipsave=False, nick=None, ipaddr=None, lanipaddr=None, lanipport=None, icqprotocol=None):
		debug.log("ICQContacts: updating contact %s" % (contact.lower()))
		self.ssicontacts[contact.lower()] = {
			'presence': presence,
			'show': show,
			'status': status,
			'ipaddr' : ipaddr,
			'lanipaddr' : lanipaddr,
			'lanipport' : lanipport,
			'icqprotocol' : icqprotocol
		}

		if (not self.xdbcontacts.count(contact.lower())):
			from glue import icq2jid
			if nick:
				self.session.sendRosterImport(icq2jid(contact), "subscribe", "both", nick.decode(self.encoding, 'replace'))
			else:
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

		for child in result.elements():
			try:
				if(child.name == "item"):
					bl.append(child.getAttribute("jid"))
			except AttributeError:
				continue
		return bl

	def saveXDBBuddies(self):
		debug.log("ICQContacts: setXDBBuddies %s %s" % (config.jid, self.session.jabberID))
		if (not self.xdbchanged):
			debug.log("ICQContacts: nothing has changed, no need to save")
			return

		newXDB = Element((None, "query"))
		newXDB.attributes["xmlns"] = "jabber:iq:roster"

		for c in self.xdbcontacts:
			try:
				item = Element((None, "item"))
				item.attributes["jid"] = c
				newXDB.addChild(item)

			except:
				pass

		self.session.pytrans.xdb.set(self.session.jabberID, "jabber:iq:roster", newXDB)
		self.xdbchanged = False
		debug.log("ICQContacts: contacts saved")

class UserInfoCollector:
	def __init__(self, id, d, vcard, userinfo):
		self.packetCounter = 0
		self.vcard = vcard
		self.d = d
		self.id = id
		self.userinfo = userinfo
		self.nick = None
		self.first = None
		self.last = None
		self.email = None
		self.homeCity = None
		self.homeState = None
		self.homePhone = None
		self.homeFax = None
		self.homeAddress = None
		self.cellPhone = None
		self.homeZIP = None
		self.homeCountry = None
		self.workCity = None
		self.workState = None
		self.workPhone = None
		self.workFax = None
		self.workAddress = None
		self.workZIP = None
		self.workCountry = None
		self.workCompany = None
		self.workDepartment = None
		self.workPosition = None
		self.workRole = None
		self.homepage = None
		self.about = None
		self.birthday = None
		self.valid = True

	def gotUserInfo(self, id, type, userinfo):
		self.packetCounter += 1
		if type == 0xffff:
			self.valid = False
			self.packetCounter = 8 # we'll get no more packages
		if type == 0xc8:
			# basic user info
			self.nick = userinfo[0]
			self.first = userinfo[1]
			self.last = userinfo[2]
			self.email = userinfo[3]
			self.homeCity = userinfo[4]
			self.homeState = userinfo[5]
			self.homePhone = userinfo[6]
			self.homeFax = userinfo[7]
			self.homeAddress = userinfo[8]
			self.cellPhone = userinfo[9]
			self.homeZIP = userinfo[10]
			self.homeCountry = userinfo[11]
		elif type == 0xdc:
			self.homepage = userinfo[0]
			self.birthday = userinfo[1]
		elif type == 0xd2:
			self.workCity = userinfo[0]
			self.workState = userinfo[1]
			self.workPhone = userinfo[2]
			self.workFax = userinfo[3]
			self.workAddress = userinfo[4]
			self.workZIP = userinfo[5]
			self.workCountry = userinfo[6]
			self.workCompany = userinfo[7]
			self.workDepartment = userinfo[8]
			self.workPosition = userinfo[9]
		elif type == 0xe6:
			self.about = userinfo[0]

		if self.packetCounter >= 8:
			return True
		else:
			return False
