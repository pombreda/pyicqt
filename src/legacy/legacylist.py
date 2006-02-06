# Copyright 2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
from tlib.twistwrap import Element
from tlib import oscar
from legacy import glue
import config
import avatar
import debug
import binascii
import os.path
import md5

class LegacyList:
	def __init__(self, session):
		self.session = session
		self.ssicontacts = { }
		self.usercaps = { }
		self.xdbcontacts = self.getLegacyList()
		for c in self.xdbcontacts:
			from glue import icq2jid
			jabContact = self.session.contactList.createContact(icq2jid(c), "both")
			if self.xdbcontacts[c].has_key("ssihash") and self.xdbcontacts[c].has_key("localhash"):
				debug.log("Setting custom avatar for %s" %(c))
				avatarData = avatar.AvatarCache().getAvatar(self.xdbcontacts[c]["localhash"])
				jabContact.updateAvatar(avatarData, push=False)
			else:
				if not config.disableDefaultAvatar:
					debug.log("Setting default avatar for %s" %(c))
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
		debug.log("LegacyList: Session \"%s\" addContact(\"%s\")" % (self.session.jabberID, jid))
		userHandle = glue.jid2icq(jid)
		self.session.legacycon.addContact(userHandle)
		self.session.contactList.getContact(jid).contactGrantsAuth()
	
	def removeContact(self, jid):
		debug.log("LegacyList: Session \"%s\" removeContact(\"%s\")" % (self.session.jabberID, jid))
		userHandle = glue.jid2icq(jid)
		self.session.legacycon.removeContact(userHandle)
	
	def authContact(self, jid):
		debug.log("LegacyList: Session \"%s\" authContact(\"%s\")" % (self.session.jabberID, jid))
		userHandle = glue.jid2icq(jid)
		self.session.legacycon.authContact(userHandle)
	
	def deauthContact(self, jid):
		debug.log("LegacyList: Session \"%s\" deauthContact(\"%s\")" % (self.session.jabberID, jid))
		userHandle = glue.jid2icq(jid)
		self.session.legacycon.deauthContact(userHandle)

	def setCapabilities(self, contact, caplist):
		debug.log("LegacyList: Session \"%s\" setCapabilities(\"%s\"): %s" % (self.session.jabberID, contact.lower(), caplist))
		self.usercaps[contact.lower()] = [ ]
		for c in caplist:
			self.usercaps[contact.lower()].append(c)

	def hasCapability(self, contact, capability):
		debug.log("LegacyList: Session \"%s\" hasCapability(\"%s\"): %s" % (self.session.jabberID, contact.lower(), capability))
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
		debug.log("updateIconHashes: %s %s %s %d" % (contact.lower(), binascii.hexlify(shaHash), md5Hash, numHash))
		if self.xdbcontacts[contact.lower()].has_key('ssihash'):
			del self.xdbcontacts[contact.lower()]['ssihash']
		if self.xdbcontacts[contact.lower()].has_key('localhash'):
			del self.xdbcontacts[contact.lower()]['localhash']
		self.xdbcontacts[contact.lower()]['md5hash'] = md5Hash
		self.xdbcontacts[contact.lower()]['numhash'] = str(numHash)
		self.xdbcontacts[contact.lower()]['shahash'] = shaHash
		self.session.pytrans.xdb.setListEntry("roster", self.session.jabberID, contact.lower(), payload=self.xdbcontacts[contact.lower()])

	def updateAvatar(self, contact, iconData=None, md5Hash=None, numHash=None):
		from glue import icq2jid

		if md5Hash:
			debug.log("updateAvatar: %s %s" % (contact.lower(), binascii.hexlify(md5Hash)))
		elif numHash:
			debug.log("updateAvatar: %s (binary hash)" % (contact.lower()))

		c = self.session.contactList.findContact(icq2jid(contact))
		if not c:
			#debug.log("Update setting default avatar for %s" %(contact))
			jabContact = self.session.contactList.createContact(icq2jid(contact), "both")
			c = jabContact

		if iconData and (md5Hash or numHash):
			debug.log("Update setting custom avatar for %s" %(contact))
			try:
				# Debugging, keeps original icon pre-convert
				try:
					f = open(utils.doPath(config.spooldir)+"/"+config.jid+"/avatarsdebug/"+contact+".icondata", 'w')
					f.write(iconData)
					f.close()
				except:
					# This isn't important
					pass
				avatarData = avatar.AvatarCache().setAvatar(utils.convertToPNG(iconData))
				c.updateAvatar(avatarData, push=True)
				if not md5Hash:
					m = md5.new()
					m.update(iconData)
					md5Hash = m.digest()
				if not numHash:
					numHash = oscar.getIconSum(iconData)
				self.updateIconHashes(contact.lower(), binascii.hexlify(md5Hash), avatarData.getImageHash(), numHash)
			except:
				debug.log("Whoa there, this image doesn't want to work.  Lets leave it where it was...")
		else:
			if not c.avatar:
				debug.log("Update setting default avatar for %s" %(contact))
				if config.disableDefaultAvatar:
					c.updateAvatar(None, push=True)
				else:
					if contact[0].isdigit():
						c.updateAvatar(glue.defaultICQAvatar, push=True)
					else:
						c.updateAvatar(glue.defaultAIMAvatar, push=True)

	def updateSSIContact(self, contact, presence="unavailable", show=None, status=None, nick=None, ipaddr=None, lanipaddr=None, lanipport=None, icqprotocol=None, url=None):
		from glue import icq2jid

		debug.log("LegacyList: updating contact %s" % (contact.lower()))
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
			debug.log("Update setting default avatar for %s" %(contact))
			c = self.session.contactList.createContact(icq2jid(contact), "both")
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
		debug.log("LegacyList: getLegacyList %s %s" % (config.jid, self.session.jabberID))
		bl = dict()
		entities = self.session.pytrans.xdb.getList("roster", self.session.jabberID)
		if entities == None:
			debug.log("LegacyList: getLegacyList unable to get list, or empty")
			return bl

		for e in entities:
			name = e[0]
			attrs = e[1]
			bl[name] = attrs
		return bl
