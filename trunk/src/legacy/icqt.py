# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.internet import protocol, reactor
from tlib import oscar
from tlib import socks5
import config
import utils
import debug
import lang
import re
import time
import binascii
import md5



#############################################################################
# BOSConnection
#############################################################################
class B(oscar.BOSConnection):
	def __init__(self,username,cookie,icqcon):
		self.chats = list()
		self.ssigroups = list()
		self.ssiiconsum = list()
		self.requesticon = {}
		self.awayResponses = {}
		self.icqcon = icqcon
		self.authorizationRequests = [] # buddies that need authorization
		self.icqcon.bos = self
		self.session = icqcon.session  # convenience
		self.capabilities = [oscar.CAP_ICON, oscar.CAP_UTF]
		self.statusindicators = oscar.STATUS_WEBAWARE
		self.unreadmessages = 0
		if config.crossChat:
			self.capabilities.append(oscar.CAP_CROSS_CHAT)
		if config.socksProxyServer and config.socksProxyPort:
			self.socksProxyServer = config.socksProxyServer
			self.socksProxyPort = config.socksProxyPort
		oscar.BOSConnection.__init__(self,username,cookie)

	def initDone(self):
		if not hasattr(self, "session") or not self.session:
			debug.log("B: initDone, no session!")
			return
		self.requestSelfInfo().addCallback(self.gotSelfInfo)
		#self.requestSelfInfo() # experimenting with no callback
		self.requestSSI().addCallback(self.gotBuddyList)
		debug.log("B: initDone %s for %s" % (self.username,self.session.jabberID))

	def connectionLost(self, reason):
		message = "ICQ connection lost! Reason: %s" % reason
		debug.log("B: connectionLost: %s" % message)
		try:
			self.icqcon.alertUser(message)
		except:
			pass

		oscar.BOSConnection.connectionLost(self, reason)
		if hasattr(self, "session") and self.session:
			self.session.removeMe()

	def gotUserInfo(self, id, type, userinfo):
		if userinfo:
			for i in range(len(userinfo)):
				userinfo[i] = userinfo[i].decode(config.encoding, "replace")
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

	def gotAuthorizationResponse(self, uin, success):
		from glue import icq2jid
		debug.log("B: Authorization Response: %s, %s"%(uin, success))
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
                c = self.session.contactList.findContact(buddyjid)
                if not c: return

		ptype = None
		show = None
		status = user.status
		encoding = user.statusencoding
		url = user.url
		#status = re.sub("<[^>]*>","",status) # Removes any HTML tags
		status = oscar.dehtml(status) # Removes any HTML tags
		if encoding:
			if encoding == "unicode":
				status = status.decode("utf-16be", "replace")
			elif encoding == "iso-8859-1":
				status = status.decode("iso-8859-1", "replace")
		if status == "Away" or status=="I am currently away from the computer." or status=="I am away from my computer right now.":
			status = ""
		if user.idleTime:
			if user.idleTime>60*24:
				idle_time = "Idle %d days"%(user.idleTime/(60*24))
			elif user.idleTime>60:
				idle_time = "Idle %d hours"%(user.idleTime/(60))
			else:
				idle_time = "Idle %d minutes"%(user.idleTime)
			if status:
				status="%s - %s"%(idle_time,status)
			else:
				status=idle_time

		if user.iconmd5sum != None:
			if self.icqcon.legacyList.diffAvatar(user.name, binascii.hexlify(user.iconmd5sum)):
				debug.log("Retrieving buddy icon for %s" % user.name)
				self.retrieveBuddyIconFromServer(user.name, user.iconmd5sum, user.icontype).addCallback(self.gotBuddyIconFromServer)
			else:
				debug.log("Buddy icon is the same, using what we have for %s" % user.name)

		if user.caps:
			self.icqcon.legacyList.setCapabilities(user.name, user.caps)
		status = status.encode("utf-8", "replace")
		if user.flags.count("away"):
			self.getAway(user.name).addCallback(self.sendAwayPresence, user)
		else:
			c.updatePresence(show=show, status=status, ptype=ptype, url=url)
			self.icqcon.legacyList.updateSSIContact(user.name, presence=ptype, show=show, status=status, ipaddr=user.icqIPaddy, lanipaddr=user.icqLANIPaddy, lanipport=user.icqLANIPport, icqprotocol=user.icqProtocolVersion, url=url)

	def gotBuddyIconFromServer(self, iconinfo):
		contact = iconinfo[0]
		icontype = iconinfo[1]
		iconhash = iconinfo[2]
		iconlen = iconinfo[3]
		icondata = iconinfo[4]
		debug.log("B: gotBuddyIconFromServer for %s: hash: %s, len: %d" % (contact, binascii.hexlify(iconhash), iconlen))
		if iconlen > 0 and iconlen != 90: # Some ICQ clients send crap
			self.icqcon.legacyList.updateAvatar(contact, icondata, iconhash)

	def offlineBuddy(self, user):
		from glue import icq2jid 
		debug.log("B: offlineBuddy %s" % (user.name))
		buddyjid = icq2jid(user.name)
                c = self.session.contactList.findContact(buddyjid)
                if not c: return
		show = None
		status = None
		ptype = "unavailable"
		c.updatePresence(show=show, status=status, ptype=ptype)

	def receiveMessage(self, user, multiparts, flags):
		from glue import icq2jid

		debug.log("B: receiveMessage %s %s %s %s %s" % (self.session.jabberID, self.name, user.name, multiparts, flags))
		sourcejid = icq2jid(user.name)
		text = multiparts[0][0]
		if len(multiparts[0]) > 1:
			if multiparts[0][1] == 'unicode':
				encoding = "utf-16be"
			else:
				encoding = config.encoding
		else:
			encoding = config.encoding
		debug.log("B: using encoding %s" % (encoding))
		text = text.decode(encoding, "replace")
		xhtml = utils.prepxhtml(text)
		if not user.name[0].isdigit():
			text = oscar.dehtml(text)
		text = text.strip()
		mtype = "chat"
		if "auto" in flags:
			mtype = "headline"

		self.session.sendMessage(to=self.session.jabberID, fro=sourcejid, body=text, mtype=mtype, xhtml=xhtml)
		self.session.pytrans.statistics.stats['IncomingMessages'] += 1
		self.session.pytrans.statistics.sessionUpdate(self.session.jabberID, 'IncomingMessages', 1)
		if self.awayMessage and not "auto" in flags:
			if not self.awayResponses.has_key(user.name) or self.awayResponses[user.name] < (time.time() - 900):
				self.sendMessage(user.name, "Away message: "+self.awayMessage.encode("iso-8859-1", "replace"), autoResponse=1)
				self.awayResponses[user.name] = time.time()

		if user.iconcksum != None:
			if self.icqcon.legacyList.diffAvatar(user.name, binascii.hexlify(user.iconcksum)):
				debug.log("User %s has a buddy icon we want, will ask for it next message." % user.name)
				self.requesticon[user.name] = 1
			else:
				debug.log("User %s has a icon that we already have." % user.name)

		if "iconrequest" in flags and hasattr(self.icqcon, "myavatar"):
			debug.log("User %s wants our icon, so we're sending it." % user.name)
			icondata = self.icqcon.myavatar
			self.sendIconDirect(user.name, icondata, wantAck=1)

	def receiveWarning(self, newLevel, user):
		debug.log("B: receiveWarning [%s] from %s" % (newLevel,hasattr(user,'name') and user.name or None))

	def receiveTypingNotify(self, type, user):
		from glue import icq2jid
		debug.log("B: receiveTypingNotify %s from %s" % (type,hasattr(user,'name') and user.name or None))
		sourcejid = icq2jid(user.name)
		if type == "begin":
			self.session.sendTypingNotification(to=self.session.jabberID, fro=sourcejid, typing=True)
			self.session.sendChatStateNotification(to=self.session.jabberID, fro=sourcejid, state="composing")
		elif type == "idle":
			self.session.sendTypingNotification(to=self.session.jabberID, fro=sourcejid, typing=False)
			self.session.sendChatStateNotification(to=self.session.jabberID, fro=sourcejid, state="paused")
		elif type == "finish":
			self.session.sendTypingNotification(to=self.session.jabberID, fro=sourcejid, typing=False)
			self.session.sendChatStateNotification(to=self.session.jabberID, fro=sourcejid, state="active")

	def errorMessage(self, message):
		tmpjid = config.jid
		if self.session.registeredmunge:
			tmpjid = tmpjid + "/registered"
		self.session.sendErrorMessage(to=self.session.jabberID, fro=tmpjid, etype="cancel", condition="recipient-unavailable",explanation=message)

	def receiveSendFileRequest(self, user, file, description, cookie):
		debug.log("B: receiveSendFileRequest")

	def emailNotificationReceived(self, addr, url, unreadnum, hasunread):
		debug.log("B: emailNotificationReceived %s %s %d %d" % (addr, url, unreadnum, hasunread))
		if unreadnum > self.unreadmessages:
			diff = unreadnum - self.unreadmessages
			self.session.sendMessage(to=self.session.jabberID, fro=config.jid, body=lang.get("icqemailnotification", config.jid) % (diff, addr, url), mtype="headline")
		self.unreadmessages = unreadnum


	# Callbacks
	def sendAwayPresence(self, msg, user):
		from glue import icq2jid
		buddyjid = icq2jid(user.name)

		c = self.session.contactList.findContact(buddyjid)
		if not c: return

		ptype = None
		show = "away"
		status = oscar.dehtml(msg[1]) # Removes any HTML tags
		url = user.url

		if status != None:
			charset = "iso-8859-1"
			m = None
			if msg[0]:
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
					charset = config.encoding
					status = msg[0] + ": " + status

			status = status.decode(charset, 'replace')
			debug.log( "dsh: away (%s, %s) message %s" % (charset, msg[0], status) )

		if status == "Away" or status=="I am currently away from the computer." or status=="I am away from my computer right now.":
			status = ""
		if user.idleTime:
			if user.idleTime>60*24:
				idle_time = "Idle %d days"%(user.idleTime/(60*24))
			elif user.idleTime>60:
				idle_time = "Idle %d hours"%(user.idleTime/(60))
			else:
				idle_time = "Idle %d minutes"%(user.idleTime)
			if status:
				status="%s - %s"%(idle_time,status)
			else:
				status=idle_time

		c.updatePresence(show=show, status=status, ptype=ptype)
		self.icqcon.legacyList.updateSSIContact(user.name, presence=ptype, show=show, status=status, ipaddr=user.icqIPaddy, lanipaddr=user.icqLANIPaddy, lanipport=user.icqLANIPport, icqprotocol=user.icqProtocolVersion, url=url)

	def gotSelfInfo(self, user):
		debug.log("B: gotSelfInfo: %s" % (user.__dict__))
		self.name = user.name

	def receivedSelfInfo(self, user):
		debug.log("B: receivedSelfInfo: %s" % (user.__dict__))
		self.name = user.name

	def receivedIconUploadRequest(self, iconhash):
		debug.log("B: receivedIconUploadRequest: %s" % binascii.hexlify(iconhash))
		if hasattr(self.icqcon, "myavatar"):
			debug.log("B: I have an icon, sending it on, %d" % len(self.icqcon.myavatar))
			self.uploadBuddyIconToServer(self.icqcon.myavatar, len(self.icqcon.myavatar)).addCallback(self.uploadedBuddyIconToServer)
			#del self.icqcon.myavatar

	def receivedIconDirect(self, user, icondata):
		debug.log("B: receivedIconDirectRequest for %s [%d]" % (user.name, user.iconlen))
		if user.iconlen > 0 and user.iconlen != 90: # Some ICQ clients send crap
			self.icqcon.legacyList.updateAvatar(user.name, icondata, user.iconhash)

	def uploadedBuddyIconToServer(self, iconchecksum):
		debug.log("B: uploadedBuddyIconToServer: %s" % (iconchecksum))

	def gotBuddyList(self, l):
		debug.log("B: gotBuddyList: %s" % (str(l)))
		if l is not None and l[0] is not None:
			for g in l[0]:
				debug.log("B: gotBuddyList found group %s" % (g.name))
				self.ssigroups.append(g)
				for u in g.users:
					debug.log("B: got user %s (%s) from group %s" % (u.name, u.nick, g.name))
					self.icqcon.legacyList.updateSSIContact(u.name, nick=u.nick)
		if l is not None and l[5] is not None:
			for i in l[5]:
				debug.log("B: gotBuddyList found icon %s" % (str(i)))
				self.ssiiconsum.append(i)
		self.activateSSI()
		self.setProfile(self.session.description)
		self.setIdleTime(0)
		self.clientReady()
		self.activateEmailNotification()
		self.session.ready = True
		tmpjid=config.jid
		if self.session.registeredmunge:
			tmpjid=config.jid+"/registered"
		if self.session.pytrans:
			self.session.sendPresence(to=self.session.jabberID, fro=tmpjid, show=self.icqcon.savedShow, status=self.icqcon.savedFriendly, url=self.icqcon.savedURL)
		if not self.icqcon.savedShow or self.icqcon.savedShow == "online":
			self.icqcon.setAway(None)
		else:
			self.icqcon.setAway(self.icqcon.savedFriendly)
		if hasattr(self.icqcon, "myavatar"):
			self.icqcon.changeAvatar(self.icqcon.myavatar)
		self.icqcon.setICQStatus(self.icqcon.savedShow)
		self.requestOffline()

	def warnedUser(self, oldLevel, newLevel, username):
		debug.log("B: warnedUser");



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

#	def connectionLost(self, reason):
#		message = "ICQ connection lost! Reason: %s" % reason
#		debug.log("OA: connectionLost: %s" % message)
#		try:
#			self.icqcon.alertUser(message)
#		except:
#			pass
#
#		oscar.OscarConnection.connectionLost(self, reason)
#		if hasattr(self.icqcon, "session") and self.icqcon.session:
#			self.icqcon.session.removeMe()
