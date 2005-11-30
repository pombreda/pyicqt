# Copyright 2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import utils
if utils.checkTwisted():
	from twisted.xish.domish import Element
else:
	from tlib.domish import Element
from tlib import oscar
from legacy import glue
import config
import avatar
import debug
import binascii

f = open("legacy/defaultAvatar.png")
defaultAvatarData = f.read()
f.close()
defaultAvatar = avatar.AvatarCache().setAvatar(defaultAvatarData)

class LegacyList:
	def __init__(self, session):
		self.session = session
		self.ssicontacts = { }
		self.xdbcontacts = self.getLegacyList()
		for c in self.xdbcontacts:
			from glue import icq2jid
			jabContact = self.session.contactList.createContact(icq2jid(c), "both")
			if self.xdbcontacts[c].has_key("ssihash") and self.xdbcontacts[c].has_key("localhash"):
				debug.log("Setting custom avatar for %s" %(c))
				avatarData = avatar.AvatarCache().getAvatar(self.xdbcontacts[c]["localhash"])
				jabContact.updateAvatar(avatarData, push=False)
			else:
				global defaultAvatar
				debug.log("Setting default avatar for %s" %(c))
				jabContact.updateAvatar(defaultAvatar, push=False)

	def removeMe(self):
		self.session = None
		self.ssicontacts = None
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
		#self.ssicontacts[contact.lower()]['caps'] = caplist
		pass

	def hasCapability(self, contact, capability):
		if self.ssicontacts.has_key(contact.lower()):
			if self.ssicontacts[contact.lower()].has_key("caps"):
				c = self.ssicontacts[contact.lower()]['caps']
				if c and c.has_key(capability):
					return True
		return False

	def diffAvatar(self, contact, iconHash):
		if self.xdbcontacts.has_key(contact.lower()):
			if self.xdbcontacts[contact.lower()].has_key("ssihash"):
				if self.xdbcontacts[contact.lower()]["ssihash"] == iconHash:
					return False
		return True

	def updateIconHashes(self, contact, ssiHash, localHash):
		debug.log("updateIconHashes: %s %s %s" % (contact.lower(), binascii.hexlify(ssiHash), localHash))
		self.xdbcontacts[contact.lower()]['ssihash'] = ssiHash
		self.xdbcontacts[contact.lower()]['localhash'] = localHash
		self.session.pytrans.xdb.setListEntry("roster", self.session.jabberID, contact.lower(), payload=self.xdbcontacts[contact.lower()])

	def updateAvatar(self, contact, iconData=None, iconHash=None):
		global defaultAvatar
		from glue import icq2jid

		debug.log("updateAvatar: %s %s" % (contact.lower(), binascii.hexlify(iconHash)))

		c = self.session.contactList.findContact(icq2jid(contact))
		if not c:
			#debug.log("Update setting default avatar for %s" %(contact))
			jabContact = self.session.contactList.createContact(icq2jid(contact), "both")
			c = jabContact

		if iconData and iconHash:
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
				self.updateIconHashes(contact.lower(), binascii.hexlify(iconHash), avatarData.getImageHash())
			except:
				debug.log("Whoa there, this image doesn't want to work.  Lets leave it where it was...")
		else:
			if not c.avatar:
				debug.log("Update setting default avatar for %s" %(contact))
				c.updateAvatar(defaultAvatar, push=True)

	def updateSSIContact(self, contact, presence="unavailable", show=None, status=None):
		global defaultAvatar
		from glue import icq2jid

		debug.log("LegacyList: updating contact %s" % (contact.lower()))
		self.ssicontacts[contact.lower()] = {
			'presence': presence,
			'show': show,
			'status': status
		}

		c = self.session.contactList.findContact(icq2jid(contact))
		if not c:
			debug.log("Update setting default avatar for %s" %(contact))
			jabContact = self.session.contactList.createContact(icq2jid(contact), "both")
			jabContact.updateAvatar(defaultAvatar, push=False)

		if not self.xdbcontacts.has_key(contact.lower()):
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
