# -*- coding: UTF-8 -*-

import config

def get(lang=config.lang):
	if(not lang.__class__ in [str, unicode]):
		lang = config.lang
	try:
		lang = lang.replace("-", "_")
		return strings.__dict__[lang]
	except KeyError:
		try:
			return strings.__dict__[config.lang]
		except KeyError:
			return strings.__dict__['en']


# If you change or add any strings in this file please contact the translators listed below
# Everything must be in UTF-8
# Look for language codes here - http://www.w3.org/WAI/ER/IG/ert/iso639.htm

class strings:
	class en: # English - James Bunton <mailto:james@delx.cjb.net>/Daniel Henninger <mailto:jadestorm@nc.rr.com>
		# Text that may get sent to the user. Useful for translations. Keep any %s symbols you see or you will have troubles later
		registertext = u"Please type your ICQ user id number into the username field and your password."
		notloggedin = u"Error. You must log into the transport before sending messages."
		notregistered = u"Sorry. You do not appear to be registered with this transport. Please register and try again. If you are having trouble registering please contact your Jabber administrator."
		waitforlogin = u"Sorry, this message cannot be delivered yet. Please try again when the transport has finished logging in."
		gatewaytranslator = u"Enter the user's ICQ user id number."
		sessionnotactive = u"Your session with ICQ is not active at this time."
	en_US = en # en-US is the same as en, so are the others
	en_AU = en
	en_GB = en

	class de: # German - Windapple (Windapple@arcor.de)
		registertext = u"Bitte geben Sie Ihre ICQ Nummer in das Benutzernamen-Feld und Ihr Passwort ein."
		notloggedin = u"Fehler. Sie müssen sich erst beim Transport anmelden bevor Nachrichten versendet werden können."
		notregistered = u"Es tut mir leid, aber Sie scheinen nicht bei diesem Transport registriert zu sein. Registrieren Sie sich bitte und versuchen sie es später noch einmal. Sollten Sie Probleme mit der Registrierung haben, bitte Kontaktieren Sie ihren Jabber Administrator."
		waitforlogin = u"Es tut mir leid, aber diese Nachricht kann jetzt noch nicht versendet werden. Versuchen Sie es nochmals wenn die Anmeldung beim Transport zuende geführt wurde."
		gatewaytranslator = u"Geben Sie die ICQ Nummer des Benutzers an."

	class pl: # Polish - Tomasz Dominikowski (dominikowski@gmail.com)
		registertext = u"Proszę podaj swój numer ICQ w polu nazwa_użytkownika oraz swoje hasło. "
		notloggedin = u"Błąd. Musisz zalogować się do transportu zanim rozpoczniesz wysyłanie wiadomości."
		notregistered = u"Wybacz, ale wygląda na to, że nie jesteś zarejestrowany w tym transporcie. Proszę zarejestruj się i spróbuj ponownie. Jeśli masz z rejestracją problemy skontaktuj się ze swoim administratorem Jabbera."
		waitforlogin = u"Wybacz, ta wiadomość nie może zostać dostarczona. Proszę spróbuj ponownie po zalogowaniu do transportu."
		gatewaytranslator = u"Podaj numer ICQ (UIN) użytkownika."

	class cs: # Czech - Mešík (pihhan@cipis.net)
		registertext = u"Prosím zadej tvoje ICQ číslo do kolonky username a heslo do kolonky password."
		notloggedin = u"Chyba. Musíš se před odesíláním zpráv nejprve přihlásit."
		notregistered = u"Promiň. Zdá se že nejsi zaregistrován(a) na této službě. Prosím zaregistruj se a zkus znovu. Pokud máš problémy s registrací, kontaktuj prosím tvého správce Jabberu."
		waitforlogin = u"Promiň, tato zpráva nemůže být ještě doručena. Prosím zkus to znovu až služba dokončí přihlašování."
		gatewaytranslator = u"Zadej uživatelovo ICQ číslo."

	class nl: # Dutch - Matthias therry (matthias.therry@pi.be)
		registertext = u"Voer je ICQ-nummer en je wachtwoord in."
		notloggedin = u"Fout: Je moet eerst aanmelden op het transport alvorens berichten te versturen."
		notregistered = u"Sorry, je bent niet geregistreerd op dit transport. Registreer je eerst en probeer dan opnieuw. Contacteer de beheerder van je Jabberserver bij registratieproblemen."
		waitforlogin = u"Sorry, dit bericht kon nog niet worden afgeleverd. Probeer opnieuw wanneer het transport klaar is met aanmelden."
		gatewaytranslator = u"Voer het ICQ-nummer van de gebruiker in."
	nl_NL = nl
	dut = nl
	nla = nl

	class ru: # Russian - Sergey Kirienko (abonentu@pisem.net)
		registertext = u"Введите ваш номер ICQ и пароль."

		notloggedin = u"Ошибка. Вы должны зарегистрироваться в службе, перед тем как отправлять сообщения."
		notregistered = u"Извините. Вы не зарегистрированы в этой службе. Зарегистрирутесь и попробуйте снова. В крайнем случае обратитесь к администратору вашего сервера Jabber."
		waitforlogin = u"Сообщение пока не может быть доставлено. Подождите, пока служба выполнит регистрацию."
		gatewaytranslator = u"Введите номер ICQ пользователя."

	class sv: # Swedish - Erik Ivarsson (erik.i@telia.com)
		registertext = u"Ange ICQ-användarid (uin) i fältet användarnamn samt lösenord."
		notloggedin = u"Fel. Du måste logga in på transporten innan meddelanden kan skickas."
		notregistered = u"Tyvärr. Du är inte registrerad på denna transport. Registrera dig och försök igen. Om du har problem med registreringen, kontakta din jabber-administratör."
		waitforlogin = u"Tyvärr. Detta meddelande kan inte levereras än. Försök igen när transporten är klar med inloggningen."
		gatewaytranslator = u"Ange användarens ICQ-användarid (uin)."

	class es: # Spanish - alejandro david weil (tenuki@gmail.com)
		registertext = u"Por favor tipee su número de identificacion de ICQ en el campo de usuario y su clave."
		notloggedin = u"Error. Debe logearse en el transporte antes de enviar mensajes."
		notregistered = u"Lo siento. Usted no parece estar registrado con este transporte. Por favor, regístrese e inténtelo nuevamente. Si usted está teniendo problemas para registrarse, por favor, contacte su administrador Jabber."
		waitforlogin = u"Lo siento, este mensaje no puede ser enviado aún.  Por favor inténtelo nuevamente cuando el transporte haya terminado de conectarse."
		gatewaytranslator = u"Ingrese el número de ICQ del usuario."

	class fr: # French - KAeL (kael@crocobox.org)
		registertext = u"Veuillez entrer votre identifiant ICQ dans le champ nom et votre mot de passe"
		notloggedin = u"Erreur. Vous devez vous connecter au transport avant d\'envoyer des messages."
		notregistered = u"Désolé. Vous ne semblez pas être enregistré avec ce transport. Veuillez vous enregistrer et réessayer. Si vous avez des difficultés à vous enregistrer, veuillez contacter votre administrateur Jabber."
		waitforlogin = u"Désolé, ce message ne peut être délivré pour le moment. Veuillez réessayer plus tard quand le transport se sera identifié."
		gatewaytranslator = u"Entrez l\'identifiant ICQ."
