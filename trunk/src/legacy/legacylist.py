# Copyright 2005-2006 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import imgmanip
from tlib.twistwrap import Element
from tlib import oscar
from legacy import glue
import config
import avatar
from debug import LogEvent, INFO, WARN, ERROR
import os
import os.path
import binascii
import os.path
import md5

X = os.path.sep

class LegacyList:
	def __init__(self, session):
		self.session = session
		self.ssicontacts = { }
		self.usercaps = { }
		self.xdbcontacts = self.getLegacyList()
		for c in self.xdbcontacts:
			from glue import icq2jid
			jabContact = self.session.contactList.createContact(icq2jid(c), "both")
			if not config.disableAvatars:
				if self.xdbcontacts[c].has_key("ssihash") and self.xdbcontacts[c].has_key("localhash"):
					LogEvent(INFO, self.session.jabberID, "Setting custom avatar for %s" %(c))
					avatarData = avatar.AvatarCache().getAvatar(self.xdbcontacts[c]["localhash"])
					jabContact.updateAvatar(avatarData, push=False)
				else:
					if not config.disableDefaultAvatar:
						LogEvent(INFO, self.session.jabberID, "Setting default avatar for %s" %(c))
						if c[0].isdigit():
							jabContact.updateAvatar(glue.defaultICQAvatar, push=False)
						else:
							jabContact.updateAvatar(glue.defaultAIMAvatar, push=False)

	def removeMe(self):
		self.session = None
		self.ssicontacts = None
		self.usercaps = None
		self.xdbcontacts = None

	def addContact(self, jid):
		LogEvent(INFO, self.session.jabberID)
		userHandle = glue.jid2icq(jid)
		self.session.legacycon.addContact(userHandle)
		self.session.contactList.getContact(jid).contactGrantsAuth()
	
	def removeContact(self, jid):
		LogEvent(INFO, self.session.jabberID)
		userHandle = glue.jid2icq(jid)
		self.session.legacycon.removeContact(userHandle)
	
	def authContact(self, jid):
		LogEvent(INFO, self.session.jabberID)
		userHandle = glue.jid2icq(jid)
		self.session.legacycon.authContact(userHandle)
	
	def deauthContact(self, jid):
		LogEvent(INFO, self.session.jabberID)
		userHandle = glue.jid2icq(jid)
		self.session.legacycon.deauthContact(userHandle)

	def setCapabilities(self, contact, caplist):
		LogEvent(INFO, self.session.jabberID)
		self.usercaps[contact.lower()] = [ ]
		for c in caplist:
			self.usercaps[contact.lower()].append(c)

	def hasCapability(self, contact, capability):
		LogEvent(INFO, self.session.jabberID)
		if self.usercaps.has_key(contact.lower()):
			if capability in self.usercaps[contact.lower()]:
				return True
		return False

	def diffAvatar(self, contact, md5Hash=None, numHash=None):
		if self.xdbcontacts.has_key(contact.lower()):
			if self.xdbcontacts[contact.lower()].has_key("md5hash"):
				if md5Hash and self.xdbcontacts[contact.lower()]["md5hash"] == md5Hash:
					return False
				if numHash and self.xdbcontacts[contact.lower()]["numhash"] == numHash:
					return False
		return True

	def updateIconHashes(self, contact, shaHash, md5Hash, numHash):
		if config.disableAvatars: return
		LogEvent(INFO, self.session.jabberID)
		#debug.log("updateIconHashes: %s %s %s %d" % (contact.lower(), binascii.hexlify(shaHash), md5Hash, numHash))
		if self.xdbcontacts[contact.lower()].has_key('ssihash'):
			del self.xdbcontacts[contact.lower()]['ssihash']
		if self.xdbcontacts[contact.lower()].has_key('localhash'):
			del self.xdbcontacts[contact.lower()]['localhash']
		self.xdbcontacts[contact.lower()]['md5hash'] = md5Hash
		self.xdbcontacts[contact.lower()]['numhash'] = str(numHash)
		self.xdbcontacts[contact.lower()]['shahash'] = shaHash
		self.session.pytrans.xdb.setListEntry("roster", self.session.jabberID, contact.lower(), payload=self.xdbcontacts[contact.lower()])

	def updateAvatar(self, contact, iconData=None, md5Hash=None, numHash=None):
		if config.disableAvatars: return
		from glue import icq2jid

		if md5Hash:
			LogEvent(INFO, self.session.jabberID, "%s [M]%s" % (contact.lower(), binascii.hexlify(md5Hash)))
		elif numHash:
			LogEvent(INFO, self.session.jabberID, "%s [N]%d" % (contact.lower(), numHash))

		c = self.session.contactList.findContact(icq2jid(contact))
		if not c:
			#debug.log("Update setting default avatar for %s" %(contact))
			jabContact = self.session.contactList.createContact(icq2jid(contact), "both")
			c = jabContact

		if iconData and (md5Hash or numHash):
			LogEvent(INFO, self.session.jabberID, "Update setting custom avatar for %s" %(contact))
			try:
				# Debugging, keeps original icon pre-convert
				try:
					f = open(os.path.abspath(config.spooldir)+X+config.jid+X+"avatarsdebug"+X+contact+".icondata", 'w')
					f.write(iconData)
					f.close()
				except:
					# This isn't important
					pass
				avatarData = avatar.AvatarCache().setAvatar(imgmanip.convertToPNG(iconData))
				c.updateAvatar(avatarData, push=True)
				if not md5Hash:
					m = md5.new()
					m.update(iconData)
					md5Hash = m.digest()
				if not numHash:
					numHash = oscar.getIconSum(iconData)
				self.updateIconHashes(contact.lower(), binascii.hexlify(md5Hash), avatarData.getImageHash(), numHash)
			except:
				LogEvent(INFO, self.session.jabberID, "Whoa there, this image doesn't want to work.  Lets leave it where it was...")
		else:
			if not c.avatar:
				LogEvent(INFO, self.session.jabberID, "Update setting default avatar for %s" %(contact))
				if config.disableDefaultAvatar:
					c.updateAvatar(None, push=True)
				else:
					if contact[0].isdigit():
						c.updateAvatar(glue.defaultICQAvatar, push=True)
					else:
						c.updateAvatar(glue.defaultAIMAvatar, push=True)

	def updateSSIContact(self, contact, presence="unavailable", show=None, status=None, nick=None, ipaddr=None, lanipaddr=None, lanipport=None, icqprotocol=None, url=None):
		from glue import icq2jid

		LogEvent(INFO, self.session.jabberID)
		self.ssicontacts[contact.lower()] = {
			'presence': presence,
			'show': show,
			'status': status,
			'url': url,
                        'ipaddr' : ipaddr,
                        'lanipaddr' : lanipaddr,
                        'lanipport' : lanipport,
                        'icqprotocol' : icqprotocol
		}

		c = self.session.contactList.findContact(icq2jid(contact))
		if not c:
			LogEvent(INFO, self.session.jabberID, "Update setting default avatar for %s" %(contact))
			c = self.session.contactList.createContact(icq2jid(contact), "both")
			if not config.disableAvatars:
				if contact[0].isdigit():
					c.updateAvatar(glue.defaultICQAvatar, push=False)
				else:
					c.updateAvatar(glue.defaultAIMAvatar, push=False)

		if not self.xdbcontacts.has_key(contact.lower()):
			if nick:
				c.updateNickname(nick.decode(config.encoding, 'replace'), push=True)
				self.session.sendRosterImport(icq2jid(contact), "subscribe", "both", nick.decode(config.encoding, 'replace'))
			else:
				self.session.sendRosterImport(icq2jid(contact), "subscribe", "both", contact)
			self.xdbcontacts[contact.lower()] = {}
			self.session.pytrans.xdb.setListEntry("roster", self.session.jabberID, contact.lower(), payload=self.xdbcontacts[contact.lower()])

	def getLegacyList(self):
		LogEvent(INFO, self.session.jabberID)
		bl = dict()
		entities = self.session.pytrans.xdb.getList("roster", self.session.jabberID)
		if entities == None:
			LogEvent(INFO, self.session.jabberID, "Unable to get list, or empty")
			return bl

		for e in entities:
			name = e[0]
			attrs = e[1]
			bl[name] = attrs
		return bl