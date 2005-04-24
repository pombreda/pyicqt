# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

import debug
import re
import string

def fudgestr(text, num):
	if(not (text.__class__ in [str, unicode])): return ""
	newtext = ""
	for c in text:
		i = ord(c)
		if(i >= num):
			i = ord(' ')
		newtext += chr(i)
	return newtext

def egdufstr(text, num):
    if(not (text.__class__ in [str, unicode])): return ""
    newtext = ""
    for c in text:
        i = ord(c)
        if(i <= num):
            i = ord(' ')
        newtext += chr(i)
    return newtext

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
		if ((ord(c) >= from_char) and (ord(c) <= to_char)):
			return True
	return False

_excluded = range(0,9)+range(11,13)+range(14,32)+range(0xD800,0xE000)+range(0xFFFE,0x10000)

excluded = {}
for c in _excluded: excluded[c] = None

def xmlify(s):
	debug.log("xmlify: class is %s: %s" % (s.__class__, s))
	if (s.__class__ == str):
		us = unicode(s)
		return us.translate(excluded)
	elif (s.__class__ == unicode):
		return s.translate(excluded)
	else:
		return ""

# 
# def utf8(text):
# 	return text
#	return fudgestr(text, 128)
# 	return fudgestr(text, 256)
# 
#def latin1(text):
#	return fudgestr(text, 128)
def latin1(text):
	return text

def utf8encode(text):
	encodedstring = ""
	for c in text.encode('utf-8', 'replace'):
		if is_in(set_char, c) and not _controlCharPat.search(c): 
			encodedstring = encodedstring + c
	#encodedstring.replace('\x00','')
	return encodedstring

def copyDict(dic):
	""" Does a deep copy of a dictionary """
	out = {}
	for key in dic.keys():
		out[key] = dic[key]
	return out

def copyList(lst):
	""" Does a deep copy of a list """
	out = []
	for i in lst:
		out.append(i)
	return out

def mutilateMe(me):
	""" Mutilates a class :) """
#	for key in dir(me):
#		exec "me." + key + " = None"

def getLang(el):
	return el.getAttribute((u'http://www.w3.org/XML/1998/namespace', u'lang'))

def doPath(path):
	if(path and path[0] == "/"):
		return path
	else:
		return "../" + path

def parseText(text):
	t = TextParser()
	t.parseString(text)
	return t.root

def parseFile(filename):
	t = TextParser()
	t.parseFile(filename)
	return t.root

class TextParser:
	""" Taken from http://xoomer.virgilio.it/dialtone/rsschannel.py """

	def __init__(self):
		self.root = None

	def parseFile(self, filename):
		return self.parseString(file(filename).read())

	def parseString(self, data):
		if(checkTwisted()):
			from twisted.xish.domish import SuxElementStream
		else:
			from tlib.domish import SuxElementStream
		es = SuxElementStream()
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

checkTwistedCached = None
def checkTwisted():
	""" Returns False if we're using an old version that needs tlib, otherwise returns True """
	global checkTwistedCached
	if(checkTwistedCached == None):
		import twisted.copyright
		checkTwistedCached = (VersionNumber(twisted.copyright.version) >= VersionNumber("2.0.0"))
	return checkTwistedCached

class VersionNumber:
	def __init__(self, vstring):
		self.varray = [0]
		index = 0 
		flag = True
		for c in vstring:
			if(c == '.'):
				self.varray.append(0)
				index += 1
				flag = True
			elif(c.isdigit() and flag):
				self.varray[index] *= 10
				self.varray[index] += int(c)
			else:
				flag = False
        
	def __cmp__(self, other):
		i = 0
		while(True):
			if(i == len(other.varray)):
				if(i < len(self.varray)):
					return 1
				else:
					return 0
			if(i == len(self.varray)):
				if(i < len(other.varray)):
					return -1
				else:
					return 0
			if(self.varray[i] > other.varray[i]):
				return 1
			elif(self.varray[i] < other.varray[i]):
				return -1
			i += 1

class RollingStock:
	def __init__(self, size):
		self.lst = []
		self.size = size

	def push(self, data):
		self.lst.append(str(data))
		if(len(self.lst) > self.size):
			self.lst.remove(self.lst[0])

	def grabAll(self):
		return "".join(self.lst)

	def flush(self):
		self.lst = []
