# Copyright 2004-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.internet import protocol, reactor
from tlib import oscar
from tlib import socks5
import config
import utils
from debug import LogEvent, INFO, WARN, ERROR
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
		if config.enableWebPresence:
			self.statusindicators = oscar.STATUS_WEBAWARE
		self.unreadmessages = 0
		if config.crossChat:
			self.capabilities.append(oscar.CAP_CROSS_CHAT)
		oscar.BOSConnection.__init__(self,username,cookie)
		if config.socksProxyServer and config.socksProxyPort:
			self.socksProxyServer = config.socksProxyServer
			self.socksProxyPort = config.socksProxyPort
		if config.icqPort:
			self.connectPort = config.icqPort
		self.defaultEncoding = config.encoding

	def initDone(self):
		if not hasattr(self, "session") or not self.session:
			LogEvent(INFO, "", "No session!")
			return
		self.requestSelfInfo().addCallback(self.gotSelfInfo)
		#self.requestSelfInfo() # experimenting with no callback
		self.requestSSI().addCallback(self.gotBuddyList)
		LogEvent(INFO, self.session.jabberID)

	def connectionLost(self, reason):
		message = "ICQ connection lost! Reason: %s" % reason
		LogEvent(INFO, self.session.jabberID, message)
		try:
			self.icqcon.alertUser(message)
		except:
			pass

		oscar.BOSConnection.connectionLost(self, reason)

		try:
			self.session.removeMe()
		except:
			pass

	def gotUserInfo(self, id, type, userinfo):
		if userinfo:
			for i in range(len(userinfo)):
				userinfo[i] = userinfo[i].decode(config.encoding, "replace").encode("utf-8", "replace")
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
		LogEvent(INFO, self.session.jabberID)
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
		LogEvent(INFO, self.session.jabberID)
		if not uin in self.authorizationRequests:
			self.authorizationRequests.append(uin)
			self.session.sendPresence(to=self.session.jabberID, fro=icq2jid(uin), ptype="subscribe")

	def youWereAdded(self, uin):
		from glue import icq2jid
		LogEvent(INFO, self.session.jabberID)
		self.session.sendPresence(to=self.session.jabberID, fro=icq2jid(uin), ptype="subscribe")

	def updateBuddy(self, user):
		from glue import icq2jid
		LogEvent(INFO, self.session.jabberID)
		buddyjid = icq2jid(user.name)
                c = self.session.contactList.findContact(buddyjid)
                if not c: return

		ptype = None
		if user.icqStatus == 'dnd':
			show = 'dnd'
		elif user.icqStatus == 'xa':
			show = 'xa'
		elif user.icqStatus == 'busy':
			show = 'dnd'
		elif user.icqStatus == 'chat':
			show = 'chat'
		elif user.icqStatus == 'dnd':
			show = 'dnd'
		elif user.icqStatus == 'away':
			show = 'away'
		else:
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
				if not show: show = "xa"
			elif user.idleTime>60:
				idle_time = "Idle %d hours"%(user.idleTime/(60))
				if not show: show = "away"
			else:
				idle_time = "Idle %d minutes"%(user.idleTime)
			if status:
				status="%s - %s"%(idle_time,status)
			else:
				status=idle_time

		if user.iconmd5sum != None and not config.disableAvatars and not config.avatarsOnlyOnChat:
			if self.icqcon.legacyList.diffAvatar(user.name, md5Hash=binascii.hexlify(user.iconmd5sum)):
				LogEvent(INFO, self.session.jabberID, "Retrieving buddy icon for %s" % user.name)
				self.retrieveBuddyIconFromServer(user.name, user.iconmd5sum, user.icontype).addCallback(self.gotBuddyIconFromServer)
			else:
				LogEvent(INFO, self.session.jabberID, "Buddy icon is the same, using what we have for %s" % user.name)

		if user.caps:
			self.icqcon.legacyList.setCapabilities(user.name, user.caps)
		status = status.encode("utf-8", "replace")
		if user.flags.count("away"):
			self.getAway(user.name).addCallback(self.sendAwayPresence, user)
		else:
			c.updatePresence(show=show, status=status, ptype=ptype, url=url)
			self.icqcon.legacyList.updateSSIContact(user.name, presence=ptype, show=show, status=status, ipaddr=user.icqIPaddy, lanipaddr=user.icqLANIPaddy, lanipport=user.icqLANIPport, icqprotocol=user.icqProtocolVersion, url=url)

	def gotBuddyIconFromServer(self, (contact, icontype, iconhash, iconlen, icondata)):
		if config.disableAvatars: return
		LogEvent(INFO, self.session.jabberID, "%s: hash: %s, len: %d" % (contact, binascii.hexlify(iconhash), iconlen))
		if iconlen > 0 and iconlen != 90: # Some ICQ clients send crap
			self.icqcon.legacyList.updateAvatar(contact, icondata, md5Hash=iconhash)

	def offlineBuddy(self, user):
		from glue import icq2jid 
		LogEvent(INFO, self.session.jabberID, user.name)
		buddyjid = icq2jid(user.name)
                c = self.session.contactList.findContact(buddyjid)
                if not c: return
		show = None
		status = None
		ptype = "unavailable"
		c.updatePresence(show=show, status=status, ptype=ptype)

	def receiveMessage(self, user, multiparts, flags):
		from glue import icq2jid

		LogEvent(INFO, self.session.jabberID, "%s %s %s" % (user.name, multiparts, flags))
		sourcejid = icq2jid(user.name)
		text = multiparts[0][0]
		if len(multiparts[0]) > 1:
			if multiparts[0][1] == 'unicode':
				encoding = "utf-16be"
			else:
				encoding = config.encoding
		else:
			encoding = config.encoding
		LogEvent(INFO, self.session.jabberID, "Using encoding %s" % (encoding))
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
				#self.sendMessage(user.name, "Away message: "+self.awayMessage.encode("iso-8859-1", "replace"), autoResponse=1)
				self.sendMessage(user.name, "Away message: "+self.awayMessage, autoResponse=1)
				self.awayResponses[user.name] = time.time()

		if "icon" in flags and not config.disableAvatars:
			if self.icqcon.legacyList.diffAvatar(user.name, numHash=user.iconcksum):
				LogEvent(INFO, self.session.jabberID, "User %s has a buddy icon we want, will ask for it next message." % user.name)
				self.requesticon[user.name] = 1
			else:
				LogEvent(INFO, self.session.jabberID, "User %s has a icon that we already have." % user.name)

		if "iconrequest" in flags and hasattr(self.icqcon, "myavatar") and not config.disableAvatars:
			LogEvent(INFO, self.session.jabberID, "User %s wants our icon, so we're sending it." % user.name)
			icondata = self.icqcon.myavatar
			self.sendIconDirect(user.name, icondata, wantAck=1)

	def receiveWarning(self, newLevel, user):
		LogEvent(INFO, self.session.jabberID)
		#debug.log("B: receiveWarning [%s] from %s" % (newLevel,hasattr(user,'name') and user.name or None))

	def receiveTypingNotify(self, type, user):
		from glue import icq2jid
		LogEvent(INFO, self.session.jabberID)
		#debug.log("B: receiveTypingNotify %s from %s" % (type,hasattr(user,'name') and user.name or None))
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
		LogEvent(INFO, self.session.jabberID)

	def emailNotificationReceived(self, addr, url, unreadnum, hasunread):
		LogEvent(INFO, self.session.jabberID)
		#debug.log("B: emailNotificationReceived %s %s %d %d" % (addr, url, unreadnum, hasunread))
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
		if user.icqStatus == 'dnd':
			show = 'dnd'
		elif user.icqStatus == 'xa':
			show = 'xa'
		elif user.icqStatus == 'busy':
			show = 'dnd'
		elif user.icqStatus == 'chat':
			show = 'chat'
		elif user.icqStatus == 'dnd':
			show = 'dnd'
		elif user.icqStatus == 'away':
			show = 'away'
		else:
			show = 'away'

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
					LogEvent(INFO, self.session.jabberID, "Unknown charset (%s) of buddy's away message" % msg[0]);
					charset = config.encoding
					status = msg[0] + ": " + status

			status = status.decode(charset, 'replace')
			LogEvent(INFO, self.session.jabberID, "Away (%s, %s) message %s" % (charset, msg[0], status))

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
		LogEvent(INFO, self.session.jabberID)
		self.name = user.name

	def receivedSelfInfo(self, user):
		LogEvent(INFO, self.session.jabberID)
		self.name = user.name

	def receivedIconUploadRequest(self, iconhash):
		if config.disableAvatars: return
		LogEvent(INFO, self.session.jabberID, "%s" % binascii.hexlify(iconhash))
		if hasattr(self.icqcon, "myavatar"):
			LogEvent(INFO, self.session.jabberID, "I have an icon, sending it on, %d" % len(self.icqcon.myavatar))
			self.uploadBuddyIconToServer(self.icqcon.myavatar, len(self.icqcon.myavatar)).addCallback(self.uploadedBuddyIconToServer)
			#del self.icqcon.myavatar

	def receivedIconDirect(self, user, icondata):
		if config.disableAvatars: return
		LogEvent(INFO, self.session.jabberID, "%s [%d]" % (user.name, user.iconlen))
		if user.iconlen > 0 and user.iconlen != 90: # Some ICQ clients send crap
			self.icqcon.legacyList.updateAvatar(user.name, icondata, numHash=user.iconcksum)

	def uploadedBuddyIconToServer(self, iconchecksum):
		LogEvent(INFO, self.session.jabberID, "%s" % (iconchecksum))

	def readGroup(self, memberlist, parent=None):
		for member in memberlist:
			if isinstance(member, oscar.SSIGroup):
				LogEvent(INFO, self.session.jabberID, "Found group %s" % (member.name))
				self.ssigroups.append(member)
				self.readGroup(member.users, parent=member)
			elif isinstance(member, oscar.SSIBuddy):
				if member.nick:
					unick,uenc = oscar.guess_encoding(member.nick, config.encoding)
				else:
					unick = None
				if parent:
					LogEvent(INFO, self.session.jabberID, "Found user %r (%r) from group %r" % (member.name, unick, parent.name))
				else:
					LogEvent(INFO, self.session.jabberID, "Found user %r (%r) from master group" % (member.name, unick))
				self.icqcon.legacyList.updateSSIContact(member.name, nick=unick)
				if member.name[0].isdigit() and (not member.nick or member.name == member.nick):
					# Hrm, lets get that nick
					self.getnicknames.append(member.name)
			else:
				LogEvent(INFO, self.session.jabberID, "Found unknown SSI entity: %r" % member)
			
	def gotBuddyList(self, l):
		LogEvent(INFO, self.session.jabberID, "%s" % (str(l)))
		self.getnicknames = list()
		if l is not None and l[0] is not None:
			self.readGroup(l[0])
		if l is not None and l[5] is not None:
			for i in l[5]:
				LogEvent(INFO, self.session.jabberID, "Found icon %s" % (str(i)))
				self.ssiiconsum.append(i)
		self.activateSSI()
		self.setProfile(self.session.description)
		self.setIdleTime(0)
		self.clientReady()
		if not config.disableMailNotifications:
			self.activateEmailNotification()
		self.session.ready = True
		tmpjid=config.jid
		if self.session.registeredmunge:
			tmpjid=config.jid+"/registered"
		if self.session.pytrans:
			self.session.sendPresence(to=self.session.jabberID, fro=tmpjid, show=self.icqcon.savedShow, status=self.icqcon.savedFriendly, url=self.icqcon.savedURL)
		if not self.icqcon.savedShow or self.icqcon.savedShow == "online":
			self.icqcon.setBack(self.icqcon.savedFriendly)
		else:
			self.icqcon.setAway(self.icqcon.savedFriendly)
		if hasattr(self.icqcon, "myavatar") and not config.disableAvatars:
			self.icqcon.changeAvatar(self.icqcon.myavatar)
		self.icqcon.setICQStatus(self.icqcon.savedShow)
		self.requestOffline()
		# Ok, lets get those nicknames.
		for n in self.getnicknames:
			self.getShortInfo(n).addCallback(self.gotNickname, n)

	def gotNickname(self, (nick, first, last, email), uin):
		LogEvent(INFO, self.session.jabberID)
		if nick:
			unick,uenc = oscar.guess_encoding(nick, config.encoding)
			LogEvent(INFO, self.session.jabberID, "Found a nickname, lets update.")
			self.icqcon.legacyList.updateNickname(uin, unick)

	def warnedUser(self, oldLevel, newLevel, username):
		LogEvent(INFO, self.session.jabberID)



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
			return c.connectSocks5Proxy(server, port, config.socksProxyServer, config.socksProxyPort, "OABOS")
		else:
			c = protocol.ClientCreator(reactor, self.BOSClass, self.username, self.cookie, self.icqcon)
			return c.connectTCP(server, port)

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
