# -*- coding: UTF-8 -*-

import config

def get(lang=config.lang):
	if(not lang.__class__ in [str, unicode]):
		lang = config.lang
	try:
		lang = lang.replace("-", "_")
		return strings.__dict__[lang]
	except KeyError:
		return strings.__dict__[config.lang]


# If you change or add any strings in this file please contact the translators listed below
# Everything must be in UTF-8
# Look for language codes here - http://www.w3.org/WAI/ER/IG/ert/iso639.htm

class strings:
	class en: # English - James Bunton <mailto:james@delx.cjb.net>/Daniel Henninger <mailto:jadestorm@nc.rr.com>
		# Text that may get sent to the user. Useful for translations. Keep any %s symbols you see or you will have troubles later
		sessionGreeting = "This is an experimental gateway, PyICQ-t. If you experience problems please contact Daniel Henninger <jadestorm@nc.rr.com>"
		registerText = "Please type your ICQ user id number into the username field and your password."
		notLoggedIn = "Error. You must log into the transport before sending messages."
		notRegistered = "Sorry. You do not appear to be registered with this transport. Please register and try again. If you are having trouble registering please contact your Jabber administrator."
		waitForLogin = "Sorry, this message cannot be delivered yet. Please try again when the transport has finished logging in."
		groupchatInvite = "You have been invited into a groupchat on the legacy service. You must join this room to switch into groupchat mode %s.\nIf you do not join this room you will not be able to participate in the groupchat, but you will still appear to have joined it to contacts on the ICQ service."
		groupchatFailJoin1 = "You did not join the groupchat room %s.\nThe following users were in the groupchat:"
		groupchatFailJoin2 = "You have been removed from this room on the legacy service. The following was said before you were disconnected, while you appeared to be in the groupchat to the contacts on the legacy service."
		groupchatPrivateError = "Sorry. You cannot send private messages to users in this groupchat. Please instead add the user to your contact list and message them that way."
		gatewayTranslator = "Enter the user's ICQ user id number."
	en_US = en # en-US is the same as en, so are the others
	en_AU = en
	en_GB = en
