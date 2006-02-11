# -*- coding: UTF-8 -*-
# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

import config
import os
import langs

def get(stringid, lang=config.lang):
	if not (lang.__class__ == str or lang.__class__ == unicode):
		lang = config.lang
	try:
		lang = lang.replace("-", "_")
		return langs.__dict__[lang].__dict__[stringid]
	except KeyError:
		try:
			return langs.__dict__[config.lang].__dict__[stringid]
		except KeyError:
			return langs.__dict__['en'].__dict__[stringid]


# If you change or add any strings in this file please contact the translators listed below
# Everything must be in UTF-8
# Look for language codes here - http://www.w3.org/WAI/ER/IG/ert/iso639.htm

#files=os.listdir("langs");
#for i in range(len(files)):
#	if files[i] == "__init__.py": continue
#	if files[i].endswith(".py"):
#		files[i] = files[i].replace(".py","")
#		exec("import langs.%s" % files[i])
