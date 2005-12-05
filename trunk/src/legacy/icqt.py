# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

from twisted.internet import protocol, reactor, defer
from tlib import oscar
from tlib.domish import Element
from tlib import socks5, sockserror
from twisted.python import log
import config
import utils
import debug
import sys, warnings, pprint
import lang
import re
import time
import binascii



#############################################################################
# BOSConnection
#############################################################################
class B(oscar.BOSConnection):
	def __init__(self,username,cookie,icqcon):
		self.chats = list()
		self.ssigroups = list()
		self.ssiiconsum = list()
		self.awayResponses = {}
		self.icqcon = icqcon
		self.authorizationRequests = [] # buddies that need authorization
		self.icqcon.bos = self
		self.session = icqcon.session  # convenience
		self.capabilities = [oscar.CAP_CHAT, oscar.CAP_ICON, oscar.CAP_UTF]
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
		#status = re.sub("<[^>]*>","",status) # Removes any HTML tags
		status = oscar.dehtml(status) # Removes any HTML tags
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

		if user.iconhash != None:
			if self.icqcon.legacyList.diffAvatar(user.name, binascii.hexlify(user.iconhash)):
				debug.log("Retrieving buddy icon for %s" % user.name)
				self.retrieveBuddyIcon(user.name, user.iconhash, user.icontype).addCallback(self.gotBuddyIcon)
			else:
				debug.log("Buddy icon is the same, using what we have for %s" % user.name)

		self.icqcon.legacyList.setCapabilities(user.name, user.caps)
		if user.flags.count("away"):
			self.getAway(user.name).addCallback(self.sendAwayPresence, user)
		else:
			c.updatePresence(show=show, status=status, ptype=ptype)
			self.icqcon.legacyList.updateSSIContact(user.name, presence=ptype, show=show, status=status, ipaddr=user.icqIPaddy, lanipaddr=user.icqLANIPaddy, lanipport=user.icqLANIPport, icqprotocol=user.icqProtocolVersion)

	def gotBuddyIcon(self, iconinfo):
		contact = iconinfo[0]
		icontype = iconinfo[1]
		iconhash = iconinfo[2]
		iconlen = iconinfo[3]
		icondata = iconinfo[4]
		debug.log("B: gotBuddyIcon for %s: hash: %s, len: %d" % (contact, binascii.hexlify(iconhash), iconlen))
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
		if not user.name[0].isdigit():
			text = oscar.dehtml(text)
		text = text.strip()
		self.session.sendMessage(to=self.session.jabberID, fro=sourcejid, body=text, mtype="chat", xhtml=utils.prepxhtml(multiparts[0][0]))
		self.session.pytrans.statistics.stats['IncomingMessages'] += 1
		self.session.pytrans.statistics.sessionUpdate(self.session.jabberID, 'IncomingMessages', 1)
		if self.awayMessage:
			if not self.awayResponses.has_key(user.name) or self.awayResponses[user.name] < (time.time() - 900):
				self.sendMessage(user.name, "Away message: "+self.awayMessage.encode("iso-8859-1", "replace"), autoResponse=1)
				self.awayResponses[user.name] = time.time

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

	def receiveChatInvite(self, user, message, exchange, fullName, instance, shortName, inviteTime):
		from glue import icq2jid, LegacyGroupchat
		debug.log("B: receiveChatInvite from %s for room %s with message: %s" % (user.name,shortName,message))
		groupchat = LegacyGroupchat(session=self.session, resource=self.session.highestResource(), ID=shortName.replace(' ','_')+"%"+str(exchange), existing=True)
		groupchat.sendUserInvite(icq2jid(user.name))

	def chatReceiveMessage(self, chat, user, message):
		from glue import icq2jidGroup
		debug.log("B: chatReceiveMessage to %s:%d from %s:%s" % (chat.name,chat.exchange,user.name,message))

		if user.name.lower() == self.username.lower():
			return

		fro = icq2jidGroup(chat.name, user.name, None)
		if not self.session.findGroupchat(fro):
			fro = icq2jidGroup(chat.name, user.name, chat.exchange)
		text = oscar.dehtml(message)
		text = text.decode("utf-8", "replace")
		text = text.strip()
		self.session.sendMessage(to=self.session.jabberID, fro=fro, body=text, mtype="groupchat")
		self.session.pytrans.statistics.stats['IncomingMessages'] += 1
		self.session.pytrans.statistics.sessionUpdate(self.session.jabberID, 'IncomingMessages', 1)

	def chatMemberJoined(self, chat, member):
		from glue import icq2jidGroup
		debug.log("B: chatMemberJoined %s joined %s" % (member.name,chat.name))
		fro = icq2jidGroup(chat.name, member.name, chat.exchange)
		ptype = None
		show = None
		status = None
		self.session.sendPresence(to=self.session.jabberID, fro=fro, show=show, status=status, ptype=ptype)

	def chatMemberLeft(self, chat, member):
		from glue import icq2jidGroup
		debug.log("B: chatMemberLeft %s left %s (members: %s)" % (member.name,chat.name,map(lambda x:x.name,chat.members)))
		fro = icq2jidGroup(chat.name, member.name, chat.exchange)
		ptype = "unavailable"
		show = None
		status = None
		self.session.sendPresence(to=self.session.jabberID, fro=fro, show=show, status=status, ptype=ptype)

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
		self.icqcon.legacyList.updateSSIContact(user.name, presence=ptype, show=show, status=status, ipaddr=user.icqIPaddy, lanipaddr=user.icqLANIPaddy, lanipport=user.icqLANIPport, icqprotocol=user.icqProtocolVersion)

	def gotSelfInfo(self, user):
		debug.log("B: gotSelfInfo: %s" % (user.__dict__))
		self.name = user.name

	def receivedSelfInfo(self, user):
		debug.log("B: receivedSelfInfo: %s" % (user.__dict__))
		self.name = user.name

	def requestBuddyIcon(self, iconhash):
		debug.log("B: requestBuddyIcon: %s" % binascii.hexlify(iconhash))
		if hasattr(self.icqcon, "myavatar"):
			debug.log("B: I have an icon, sending it on, %d" % len(self.icqcon.myavatar))
			self.sendBuddyIcon(self.icqcon.myavatar, len(self.icqcon.myavatar)).addCallback(self.sentBuddyIcon)
			del self.icqcon.myavatar

	def sentBuddyIcon(self, iconchecksum):
		debug.log("B: sentBuddyIcon: %s" % (iconchecksum))

	def gotBuddyList(self, l):
		debug.log("B: gotBuddyList: %s" % (str(l)))
		if l is not None and l[0] is not None:
			for g in l[0]:
				debug.log("B: gotBuddyList found group %s" % (g.name))
				self.ssigroups.append(g)
				for u in g.users:
					debug.log("B: got user %s from group %s" % (u.name, g.name))
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
			self.session.sendPresence(to=self.session.jabberID, fro=tmpjid, show=self.icqcon.savedShow, status=self.icqcon.savedFriendly)
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

	def createdRoom(self, (exchange, fullName, instance)):
		debug.log("B: createdRoom: %s, %s, %s" % (exchange, fullName, instance))
		self.joinChat(exchange, fullName, instance).addCallback(self.chatJoined)

	def chatJoined(self, chat):
		from glue import icq2jidGroup
		debug.log("B: chatJoined room %s (members: %s)" % (chat.name,map(lambda x:x.name,chat.members)))
		if chat.members is not None:
			for m in chat.members:
				fro = icq2jidGroup(chat.name, m.name, chat.exchange)
				ptype = None
				show = None
				status = None
				self.session.sendPresence(to=self.session.jabberID, fro=fro, show=show, status=status, ptype=ptype)
		self.chats.append(chat)



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



#############################################################################
# ICQConnection
#############################################################################
class ICQConnection:
	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.reactor = reactor
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
			self.bos.awayResponses = {}
			self.bos.setAway(utils.xmlify(awayMessage))
		except AttributeError:
			#self.alertUser(lang.get("sessionnotactive", config.jid))
			pass

	def setBack(self, backMessage=None):
		debug.log("ICQConnection: setBack %s" % (backMessage))
		try:
			self.bos.awayResponses = {}
			self.bos.setBack(utils.utf8encode(backMessage))
		except AttributeError:
			#self.alertUser(lang.get("sessionnotactive", config.jid))
			pass

	def setProfile(self, profileMessage=None):
		debug.log("ICQConnection: setProfile %s" % (profileMessage))
		try:
			self.bos.setProfile(profileMessage)
		except AttributeError:
			#self.alertUser(lang.get("sessionnotactive", config.jid))
			pass

	def setICQStatus(self, status):
		debug.log("ICQConnection: setICQStatus %s" % (status))
		try:
			self.bos.setICQStatus(status)
		except AttributeError:
			#self.alertUser(lang.get(config.jid).sessionnotactive)
			pass

	def sendMessage(self, target, message, xhtml):
		from glue import jid2icq
		try:
			self.session.pytrans.statistics.stats['OutgoingMessages'] += 1
			self.session.pytrans.statistics.sessionUpdate(self.session.jabberID, 'OutgoingMessages', 1)        
			uin = jid2icq(target)
			debug.log("ICQConnection: sendMessage %s %s" % (uin, message))
			if uin[0].isdigit():
				encoding = "iso-8859-1"
				if self.legacyList.hasCapability(uin, "unicode"):
					encoding = "utf-8"
				debug.log("ICQConnection: sendMessage encoding %s" % encoding)
				self.bos.sendMessage(uin, message.encode(encoding, "replace"), offline=1)
			else:
				if xhtml:
					self.bos.sendMessage(uin, xhtml, offline=1)
				else:
					htmlized = oscar.html(message)
					self.bos.sendMessage(uin, htmlized, offline=1)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def resendBuddies(self, resource):
		from glue import icq2jid
		debug.log("ICQConnection: resendBuddies %s" % (resource))
		try:
			for c in self.legacyList.ssicontacts.keys( ):
				debug.log("ICQConnection: resending buddy of %s" % (c))
				jid = icq2jid(c)
				show = self.legacyList.ssicontacts[c]['show']
				status = self.legacyList.ssicontacts[c]['status']
				ptype = self.legacyList.ssicontacts[c]['presence']
				#FIXME, needs to be contact based updatePresence
				self.session.sendPresence(to=self.session.jabberID, fro=jid, show=show, status=status, ptype=ptype)
		except AttributeError:
			return

	def sendTypingNotify(self, type, dest):
		from tlib.oscar import MTN_FINISH, MTN_IDLE, MTN_BEGIN
		from glue import jid2icq
		try:
			username = jid2icq(dest)
			debug.log("ICQConnection: sendTypingNotify %s to %s" % (type,username))
			if type == "begin":
				self.bos.sendTypingNotification(username, MTN_BEGIN)
			elif type == "idle":
				self.bos.sendTypingNotification(username, MTN_IDLE)
			elif type == "finish":
				self.bos.sendTypingNotification(username, MTN_FINISH)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def createChat(self, chatroom, exchange):
		debug.log("ICQConnection: createChat %s %d" % (chatroom, exchange))
		try:
			self.bos.createChat(chatroom, exchange).addCallback(self.bos.createdRoom)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def leaveChat(self, chatroom):
		debug.log("ICQConnection: leaveChat %s" % (chatroom))
		try:
			for c in self.bos.chats:
				if c.name == chatroom:
					c.leaveChat()
					self.bos.chats.remove(c)
					break
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def sendChat(self, chatroom, message):
		debug.log("ICQConnection: sendChat %s %s" % (chatroom, message))
		try:
			for c in self.bos.chats:
				debug.log("Checking chat %s" % (c.name))
				if c.name.lower() == chatroom.lower():
					c.sendMessage(message)
					debug.log("Found chat and sent message.")
					break
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def sendInvite(self, chatroom, contact):
		debug.log("ICQConnection: sendInvite %s %s" % (chatroom, contact))
		try:
			for c in self.bos.chats:
				if c.name.lower() == chatroom.lower():
					self.bos.sendInvite(contact, c)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

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
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def gotvCard(self, usercol):
		from glue import icq2jid

		#debug.log("ICQConnection: gotvCard: %s" % (profile))
		debug.log("ICQConnection: gotvCard")

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

	def gotnovCard(self, profile, user, vcard, d):
		from glue import icq2jid
		debug.log("ICQConnection: novCard: %s" % (profile))

		nickname = vcard.addElement("NICKNAME")
		nickname.addContent(user)
		jabberid = vcard.addElement("JABBERID")
		jabberid.addContent(icq2jid(user))
		desc = vcard.addElement("DESC")
		desc.addContent("User is not online.")

		d.callback(vcard)

	def removeMe(self):
		from glue import icq2jid
		debug.log("ICQConnection: removeMe")
		try:
			self.bos.stopKeepAlive()
			self.bos.disconnect()
		except AttributeError:
			return

	def resourceOffline(self, resource):
		from glue import icq2jid
		debug.log("ICQConnection: resourceOffline %s" % (resource))
		try:
			show = None
			status = None
			ptype = "unavailable"
			for c in self.legacyList.ssicontacts.keys( ):
				debug.log("ICQConnection: sending offline for %s" % (c))
				jid = icq2jid(c)

				self.session.sendPresence(to=self.session.jabberID+"/"+resource, fro=jid, ptype=ptype, show=show, status=status)
			self.session.sendPresence(to=self.session.jabberID+"/"+resource, fro=config.jid, ptype=ptype, show=show, status=status)
		except AttributeError:
			return

	def icq2uhandle(self, icqid):
		retstr = icqid.replace(' ','')
		return retstr.lower()

	def updatePresence(self, userHandle, ptype): # Convenience
		from glue import icq2jid
		to = icq2jid(userHandle)
		self.session.sendPresence(to=self.session.jabberID, fro=to, ptype=ptype)

	def addContact(self, userHandle):
		debug.log("ICQConnection: Session \"%s\" - addContact(\"%s\")" % (self.session.jabberID, userHandle))
		def cb(arg=None):
			self.updatePresence(userHandle, "subscribed")

		try:
			for g in self.bos.ssigroups:
				for u in g.users:
					icqHandle = self.icq2uhandle(u.name)
					if icqHandle == userHandle:
						if not u.authorizationRequestSent and not u.authorized:
							self.bos.sendAuthorizationRequest(userHandle, "Please authorize me!")
							u.authorizationRequestSent = True
							return
						else:
							cb()
							return

			savethisgroup = None
			groupName = "PyICQ-t Buddies"
			for g in self.bos.ssigroups:
				if g.name == groupName:
					debug.log("Located group %s" % (g.name))
					savethisgroup = g

			if savethisgroup is None:
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

			self.legacyList.updateSSIContact(userHandle)
			self.updatePresence(userHandle, "subscribe")
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def removeContact(self, userHandle):
		debug.log("ICQConnection: Session \"%s\" - removeContact(\"%s\")" % (self.session.jabberID, userHandle))
		if userHandle in self.bos.authorizationRequests:
			self.bos.sendAuthorizationResponse(userHandle, False, "")
			self.bos.authorizationRequests.remove(userHandle)

		def cb(arg=None):
			self.updatePresence(userHandle, "unsubscribed")

		try:
			savetheseusers = []
			for g in self.bos.ssigroups:
				for u in g.users:
					icqHandle = self.icq2uhandle(u.name)
					debug.log("Comparing %s and %s" % (icqHandle, userHandle))
					if icqHandle == userHandle:
						debug.log("Located user %s" % (u.name))
						savetheseusers.append(u)

			if len(savetheseusers) == 0:
				debug.log("Did not find user")
				return

			self.bos.startModifySSI()
			for u in savetheseusers:
				debug.log("ICQConnection: Removing %s (u:%d g:%d) from group %s"%(u.name, u.buddyID, u.groupID, u.group.name))
				de = self.bos.delItemSSI(u)
				de.addCallback(self.SSIItemDeleted, u)
			de.addCallback(cb)
			self.bos.endModifySSI()
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def authContact(self, userHandle):
		debug.log("ICQConnection: Session \"%s\" - authContact(\"%s\")" % (self.session.jabberID, userHandle))
		try:
			if userHandle in self.bos.authorizationRequests:
				self.bos.sendAuthorizationResponse(userHandle, True, "OK")
				self.bos.authorizationRequests.remove(userHandle)
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def deauthContact(self, userHandle):
		debug.log("ICQConnection: Session \"%s\" - deauthContact(\"%s\")" % (self.session.jabberID, userHandle))
		# I don't recall why these are the same
		self.authContact(userHandle)

	def SSIItemDeleted(self, x, user):
		c = 0
		for g in self.bos.ssigroups:
			c += 1
			for u in g.users:
				if u.buddyID == user.buddyID and u.groupID == user.groupID:
					g.users.remove(u)
					del g.usersToID[u]

	def errorCallback(self, result):
		debug.log("ICQConnection: errorCallback %s" % (result.getErrorMessage()))
		errmsg = result.getErrorMessage()
		errmsgs = errmsg.split("'")
		message = "Authentication Error!" 
		if errmsgs[1]:
			message = message+"\n"+errmsgs[1]
		if errmsgs[3]:
			message = message+"\n"+errmsgs[3]
		self.alertUser(message)

		self.session.removeMe()

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
		if self.session.registeredmunge:
			tmpjid = tmpjid + "/registered"
		self.session.sendMessage(to=self.session.jabberID, fro=tmpjid, body=message, mtype="error")

	def changeAvatar(self, imageData):
		try:
			self.myavatar = utils.convertToJPG(imageData)
		except:
			debug.log("ICQConnection: changeAvatar, unable to convert avatar to JPEG, punting.")
			return
		if hasattr(self, "bos"):
			if len(self.bos.ssiiconsum) > 0 and self.bos.ssiiconsum[0]:
				debug.log("ICQConnection: changeAvatar, replacing existing icon")
				self.bos.ssiiconsum[0].updateIcon(imageData)
				self.bos.startModifySSI()
				self.bos.modifyItemSSI(self.bos.ssiiconsum[0])
				self.bos.endModifySSI()
			else:
				debug.log("ICQConnection: changeAvatar, adding new icon")
				newBuddySum = oscar.SSIIconSum()
				newBuddySum.updateIcon(imageData)
				self.bos.startModifySSI()
				self.bos.addItemSSI(newBuddySum)
				self.bos.endModifySSI()
			#if hasattr(self, "myavatar"):
			#	del self.myavatar

	def doSearch(self, form, iq):
		#TEST self.bos.sendInterestsRequest()
		email = utils.getDataFormValue(form, "email")
		first = utils.getDataFormValue(form, "first")
		middle = utils.getDataFormValue(form, "middle")
		last = utils.getDataFormValue(form, "last")
		maiden = utils.getDataFormValue(form, "maiden")
		nick = utils.getDataFormValue(form, "nick")
		address = utils.getDataFormValue(form, "address")
		city = utils.getDataFormValue(form, "city")
		state = utils.getDataFormValue(form, "state")
		zip = utils.getDataFormValue(form, "zip")
		country = utils.getDataFormValue(form, "country")
		interest = utils.getDataFormValue(form, "interest")
                debug.log("ICQConnection: doSearch %s" % (form.toXml()))
		try:
			d = defer.Deferred()
			self.bos.sendDirectorySearch(email=email, first=first, middle=middle, last=last, maiden=maiden, nickname=nick, address=address, city=city, state=state, zip=zip, country=country, interest=interest).addCallback(self.gotSearchResults, iq, d).addErrback(self.gotSearchError, d)
			return d
		except AttributeError:
			self.alertUser(lang.get("sessionnotactive", config.jid))

	def gotSearchResults(self, results, iq, d):
		debug.log("ICQConnection: gotSearchResults %s %s" % (results, iq.toXml()))
		from glue import icq2jid

		x = None
		for query in iq.elements():
			if query.name == "query":
				for child in query.elements():
					if child.name == "x":
						x = child
						break
				break

		if x:
			for r in results:
				if r.has_key("screenname"):
					r["jid"] = icq2jid(r["screenname"])
				else:
					r["jid"] = "Unknown"
				item = x.addElement("item")
				for k in ["jid","first","middle","last","maiden","nick","email","address","city","state","country","zip","region"]:
					item.addChild(utils.makeDataFormElement(None, k, value=r.get(k,None)))
		d.callback(iq)

	def gotSearchError(self, error, d):
		debug.log("ICQConnection: gotSearchError %s" % (error))
		#d.callback(vcard)



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
