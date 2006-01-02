# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import debug
import re
import string
import config
import os
import os.path
import sys
from twisted.web import microdom

class VersionNumber:
	def __init__(self, vstring):
		self.varray = [0]
		index = 0 
		flag = True
		for c in vstring:
			if c == '.':
				self.varray.append(0)
				index += 1
				flag = True
			elif c.isdigit() and flag:
				self.varray[index] *= 10
				self.varray[index] += int(c)
			else:
				flag = False
        
	def __cmp__(self, other):
		i = 0
		while True:
			if i == len(other.varray):
				if i < len(self.varray):
					return 1
				else:
					return 0
			if i == len(self.varray):
				if i < len(other.varray):
					return -1
				else:
					return 0
			if self.varray[i] > other.varray[i]:
				return 1
			elif self.varray[i] < other.varray[i]:
				return -1
			i += 1

checkTwistedCached = None
def checkTwisted():
	""" Returns False if we're using an old version that needs tlib, otherwise returns True """
	global checkTwistedCached
	if checkTwistedCached == None:
		import twisted.copyright
		checkTwistedCached = (VersionNumber(twisted.copyright.version) >= VersionNumber("2.0.0"))
	return checkTwistedCached

if checkTwisted():
	from twisted.xish.domish import Element
else:
	from tlib.domish import Element

_controlCharPat = re.compile(
	r"[\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f"
	r"\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f]")

set_char = [
	(0x000001, 0x00D7FF),
	(0x00E000, 0x00FFFD),
	(0x010000, 0x10FFFF)
]

set_restrictedchar = [
	(0x01, 0x08),
	(0x0B, 0x0C),
	(0x0E, 0x1F),
	(0x7F, 0x84),
	(0x86, 0x9F)
]

def is_in(set_list, c):
	for i in set_list:
		from_char, to_char = i
		if ord(c) >= from_char and ord(c) <= to_char:
			return True
	return False

_excluded = range(0,9)+range(11,13)+range(14,32)+range(0xD800,0xE000)+range(0xFFFE,0x10000)

excluded = {}
for c in _excluded: excluded[c] = None

def xmlify(s):
	debug.log("xmlify: class is %s: %s" % (s.__class__, s))
	if s.__class__ == str:
		try:
			us = unicode(s)
		except UnicodeDecodeError:
			us = unicode(s, 'iso-8859-1')
		return us.translate(excluded)
	elif s.__class__ == unicode:
		return s.translate(excluded)
	else:
		return ""

def prepxhtml(s):
	try:
		debug.log("prepxhtml: Got %s" % s)
		s = re.sub('<html.*>','<html>',s) # Don't ask...
		ms = microdom.parseString(s, beExtremelyLenient=True)
		ret = ms.toxml()
		#ms = parseText(s, beExtremelyLenient=True)
		#ret = ms.toXml()
		ret = re.sub('<\?xml.*\?>', '', ret)
		ret = re.sub('<html>','<html xmlns="http://jabber.org/protocol/xhtml-im">',ret)
		debug.log("prepxhtml: Made %s" % ret)
		return ret
	except:
		debug.log("prepxhtml: Failed")
		return None
	
def utf8encode(text):
	if text == None: return text
	encodedstring = ""
	for c in text.encode('utf-8', 'replace'):
		if is_in(set_char, c) and not _controlCharPat.search(c): 
			encodedstring = encodedstring + c
	#encodedstring.replace('\x00','')
	return encodedstring

def copyList(lst):
	""" Does a deep copy of a list """
	out = []
	out.extend(lst)
	return out

def mutilateMe(me):
	""" Mutilates a class :) """
#	for key in dir(me):
#		exec "me." + key + " = None"

def getLang(el):
	return el.getAttribute((u'http://www.w3.org/XML/1998/namespace', u'lang'))

import random
def random_guid():
	format = "{%4X%4X-%4X-%4X-%4X-%4X%4X%4X}"
	data = []
	for x in xrange(8):
		data.append(random.random() * 0xAAFF + 0x1111)
	data = tuple(data)

	return format % data


import base64
def b64enc(s):
	return base64.encodestring(s).replace('\n', '')

def b64dec(s):
	return base64.decodestring(s)

try:
	import Image
	import StringIO

	def convertToPNG(imageData):
		inbuff = StringIO.StringIO(imageData)
		outbuff = StringIO.StringIO()
		Image.open(inbuff).save(outbuff, "PNG")
		outbuff.seek(0)
		imageData = outbuff.read()
		return imageData

	def convertToJPG(imageData):
		inbuff = StringIO.StringIO(imageData)
		outbuff = StringIO.StringIO()
		img = Image.open(inbuff)
		if img.size[0] > 64 or img.size[1] > 64:
			img.thumbnail((64,64))
		elif img.size[0] < 15 or img.size[1] < 15:
			img.thumbnail((15,15))
		img.convert().save(outbuff, "JPEG")
		outbuff.seek(0)
		imageData = outbuff.read()
		return imageData
except ImportError:
	print "ERROR! PyICQ-t requires the Python Imaging Library to function with avatars.  Either install the Python Imaging Library, or disable avatars using the <disableAvatars/> option in your config file. (this is not implemented just yet btw)"
	sys.exit(-1)


errorCodeMap = {
	"bad-request"			:	400,
	"conflict"			:	409,
	"feature-not-implemented"	:	501,
	"forbidden"			:	403,
	"gone"				:	302,
	"internal-server-error"		:	500,
	"item-not-found"		:	404,
	"jid-malformed"			:	400,
	"not-acceptable"		:	406,
	"not-allowed"			:	405,
	"not-authorized"		:	401,
	"payment-required"		:	402,
	"recipient-unavailable"		:	404,
	"redirect"			:	302,
	"registration-required"		:	407,
	"remote-server-not-found"	:	404,
	"remote-server-timeout"		:	504,
	"resource-constraint"		:	500,
	"service-unavailable"		:	503,
	"subscription-required"		:	407,
	"undefined-condition"		:	500,
	"unexpected-request"		:	400
}

def doPath(path):
	if path and path[0] == "/":
		return path
	else:
		return "../" + path

def parseText(text, beExtremelyLenient=False):
	t = TextParser(beExtremelyLenient)
	t.parseString(text)
	return t.root

def parseFile(filename, beExtremelyLenient=False):
	t = TextParser(beExtremelyLenient)
	t.parseFile(filename)
	return t.root

class TextParser:
	""" Taken from http://xoomer.virgilio.it/dialtone/rsschannel.py """

	def __init__(self, beExtremelyLenient=False):
		self.root = None
		self.beExtremelyLenient = beExtremelyLenient

	def parseFile(self, filename):
		return self.parseString(file(filename).read())

	def parseString(self, data):
		if checkTwisted():
			from twisted.xish.domish import SuxElementStream
		else:
			from tlib.domish import SuxElementStream
		es = SuxElementStream()
		es.beExtremelyLenient = self.beExtremelyLenient
		es.DocumentStartEvent = self.docStart
		es.DocumentEndEvent = self.docEnd
		es.ElementEvent = self.element
		es.parse(data)
		return self.root

	def docStart(self, e):
		self.root = e

	def docEnd(self):
		pass

	def element(self, e):
		self.root.addChild(e)

class RollingStack:
	def __init__(self, size):
		self.lst = []
		self.size = size

	def push(self, data):
		self.lst.append(str(data))
		if len(self.lst) > self.size:
			self.lst.remove(self.lst[0])

	def grabAll(self):
		return "".join(self.lst)

	def flush(self):
		self.lst = []


def makeDataFormElement(type, var, label=None, value=None, options=None):
	field = Element((None, "field"))
	if type:
		field.attributes["type"] = type
	if var:
		field.attributes["var"] = var
	if label:
		field.attributes["label"] = label
	if value:
		val = field.addElement("value")
		val.addContent(value)
	if options:
		# Take care of options at some point
		pass

	return field

def getDataFormValue(form, var):
	value = None
	for field in form.elements():
		if field.name == "field" and field.getAttribute("var") == var:
			for child in field.elements():
				if child.name == "value":
					if child.__str__():
						value = child.__str__();
					break
	return value

class NotesToMyself:
	def __init__(self, noteList):
		pre = doPath(config.spooldir) + "/" + config.jid + "/"
		self.filename = pre + "/notes_to_myself"
		self.notes = []
                
		if os.path.exists(self.filename):
			f = open(self.filename, "r")
			self.notes = [x.strip() for x in f.readlines()]
			f.close()
		elif not os.path.exists(pre):
			self.notes = noteList
			os.makedirs(pre)

	def check(self, note):
		return self.notes.count(note) == 0

	def append(self, note):
		if self.check(note):
			self.notes.append(note)

	def save(self):
		f = open(self.filename, "w")
		for note in self.notes:
			f.write(note + "\n")
		f.close()

def unmangle(jid):
	chunks = jid.split("%")
	end = chunks.pop()
	jid = "%s@%s" % ("%".join(chunks), end)
	return jid
         
def mangle(jid):
	return jid.replace("@", "%")

# Helper functions to encrypt and decrypt passwords
def encryptPassword(password):
	return base64.encodestring(password)

def decryptPassword(password):
	return base64.decodestring(password)
