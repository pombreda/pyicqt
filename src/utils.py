# Copyright 2004 James Bunton <james@delx.cjb.net>
# Licensed for distribution under the GPL version 2, check COPYING for details

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
		if is_in(set_char, c): 
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
