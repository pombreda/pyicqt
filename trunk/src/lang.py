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
		sessionGreeting = u"This is an experimental gateway, PyICQ-t. If you experience problems please contact Daniel Henninger <jadestorm@nc.rr.com>"
		registerText = u"Please type your ICQ user id number into the username field and your password."
		notLoggedIn = u"Error. You must log into the transport before sending messages."
		notRegistered = u"Sorry. You do not appear to be registered with this transport. Please register and try again. If you are having trouble registering please contact your Jabber administrator."
		waitForLogin = u"Sorry, this message cannot be delivered yet. Please try again when the transport has finished logging in."
		groupchatInvite = u"You have been invited into a groupchat on the legacy service. You must join this room to switch into groupchat mode %s.\nIf you do not join this room you will not be able to participate in the groupchat, but you will still appear to have joined it to contacts on the ICQ service."
		groupchatFailJoin1 = u"You did not join the groupchat room %s.\nThe following users were in the groupchat:"
		groupchatFailJoin2 = u"You have been removed from this room on the legacy service. The following was said before you were disconnected, while you appeared to be in the groupchat to the contacts on the legacy service."
		groupchatPrivateError = u"Sorry. You cannot send private messages to users in this groupchat. Please instead add the user to your contact list and message them that way."
		gatewayTranslator = u"Enter the user's ICQ user id number."
	en_US = en # en-US is the same as en, so are the others
	en_AU = en
	en_GB = en

	class de: # German - Windapple (Windapple@arcor.de)
		sessiongreeting = u"Dies ist ein experimentelles Gateway, PyICQ-t. Sollten Sie Probleme haben, bitte kontaktieren Sie Daniel Henninger <jadestorm@nc.rr.com>"
		registertext = u"Bitte geben Sie Ihre ICQ Nummer in das Benutzernamen-Feld und Ihr Passwort ein."
		notloggedin = u"Fehler. Sie müssen sich erst beim Transport anmelden bevor Nachrichten versendet werden können."
		notregistered = u"Es tut mir leid, aber Sie scheinen nicht bei diesem Transport registriert zu sein. Registrieren Sie sich bitte und versuchen sie es später noch einmal. Sollten Sie Probleme mit der Registrierung haben, bitte Kontaktieren Sie ihren Jabber Administrator."
		waitforlogin = u"Es tut mir leid, aber diese Nachricht kann jetzt noch nicht versendet werden. Versuchen Sie es nochmals wenn die Anmeldung beim Transport zuende geführt wurde."
		groupchatinvite = u"Sie wurden in einen Gruppenchat auf dem Legacy Service eingeladen. Sie müssen diesem Raum beitreten um in den Gruppenchat-Modus %s zu wechseln.\\nFalls Sie nicht diesem Raum beitreten werden Sie nicht am Gruppenchat teilnehmen können, aber den Kontakten auf dem ICQ Service wird suggeriert, Sie wären beigetreten. "
		groupchatfailjoin2 = u"Sie sind dem Gruppenchat-Raum %s nicht beigetreten.\\nDie folgenden Benutzer waren im Gruppenchat:"
		groupchatfailjoin2 = u"Sie wurden von diesem Raum auf dem Legacy Service entfernt. Das folgende wurde kurz vor dem Trennen gesagt, während Sie den Kontakten am Legace Service noch als im Gruppenchat Anwesend angezeigt wurden."
		groupchatprivateerror = u"Es tut mir leid, aber Sie können den Nutzern in diesem Gruppenchat keine Privaten Nachrichten senden. Bitte fügen Sie sie stattdessen Ihrer Kontakliste hinzu und senden Sie die Nachrichten auf diesem Wege."
		gatewaytranslator = u"Geben Sie die ICQ Nummer des Benutzers an."

	class po: # Polish - Tomasz Dominikowski (dominikowski@gmail.com)
		sessiongreeting = u"To jest eksperymentalny transport, PyICQ-t. Jeśli występują problemy proszę skontaktować się z Danielem Henningerem <jadestorm@nc.rr.com>"
		registertext = u"Proszę podaj swój numer ICQ w polu nazwa_użytkownika oraz swoje hasło. "
		notloggedin = u"Błąd. Musisz zalogować się do transportu zanim rozpoczniesz wysyłanie wiadomości."
		notregistered = u"Wybacz, ale wygląda na to, że nie jesteś zarejestrowany w tym transporcie. Proszę zarejestruj się i spróbuj ponownie. Jeśli masz z rejestracją problemy skontaktuj się ze swoim administratorem Jabbera."
		waitforlogin = u"Wybacz, ta wiadomość nie może zostać dostarczona. Proszę spróbuj ponownie po zalogowaniu do transportu."
		groupchatinvite = u"Zostałeś zaproszony do grupowej rozmowy na zewnętrznej usłudze. Musisz dołączyć do pokoju aby wejść w tryb grupowej rozmowy %s.\\nJeśli nie dołączysz do pokoju nie będziesz mógł uczestniczyć w rozmowie grupowej, ale nadal będzie wyglądało, że dołączyłeś ten pokój do kontaktów w usłudze ICQ."
		groupchatfailjoin1 = u"Nie dołączyłeś do pokoju rozmowy grupowej %s.\\nW pokoju znajdowali się następujący użytkownicy:"
		groupchatfailjoin2 = u"Zostałeś usunięty z tego pokoju na zewnętrznej usłudze. Następująca treść została przekazana zanim zostałeś rozłączony, ale nadal widoczny w rozmowie grupowej na zewnętrznej usłudze."
		groupchatprivateerror = u"Wybacz, nie możesz wysłać prywatnej wiadomości do użytkowników rozmowy grupowej. Zamiast tego dodaj użytkownika do listy kontaktów i wyślij wiadomość w zwyczajny sposób."
		gatewaytranslator = u"Podaj numer ICQ (UIN) użytkownika."
