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
