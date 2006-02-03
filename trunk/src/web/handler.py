# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

from nevow import rend, loaders, inevow, static
from nevow import tags as T
from twisted.protocols import http
from twisted.web import microdom
from twisted.internet import reactor
from twisted.cred import portal, credentials
import debug
import config
import legacy
import sys, os
import lang
from xmppcred import XMPPRealm, XMPPChecker, IXMPPAvatar

# Template Node
class WebInterface_template(rend.Page):
	addSlash = True
	docFactory = loaders.xmlfile('data/www/template.html')

	def __init__(self, pytrans):
		self.pytrans = pytrans

	def renderHTTP(self, ctx):
		request = inevow.IRequest(ctx)
		username = request.getUser()
		password = request.getPassword()
		p = portal.Portal(XMPPRealm())
		p.registerChecker(XMPPChecker(config.mainServer, 5222))
		creds = credentials.UsernamePassword(username, password)
		return p.login(creds, None, IXMPPAvatar).addCallback(
			self._loginSucceeded, ctx).addErrback(
			self._loginFailed, ctx)

	def _loginSucceeded(self, avatarInfo, ctx):
		return rend.Page.renderHTTP(self, ctx)

	def _loginFailed(self, result, ctx):
		request = inevow.IRequest(ctx)
		request.setHeader('WWW-Authenticate', 'Basic realm="PyICQ-t Web Interface"')
		request.setResponseCode(http.UNAUTHORIZED)
		return "Authorization required."

	def render_version(self, context, data):
		return [legacy.version]

	def render_title(self, context, data):
		return [legacy.name]

	def render_menu(self, context, data):
		request = inevow.IRequest(context)
		username = request.getUser()

		ret = T.table(border=0,cellspacing=3,cellpadding=3)
		row = T.tr(valign="middle")
		row[T.td(_class="menuentry",width="150",align="center",onclick="self.location='/account/'",onmouseover="this.className='menuentrypressed';",onmouseout="this.className='menuentry';")[T.a(_class="menuentry",href="/account/")["Account"]]]

		if config.admins.count(username) > 0:
			row[T.td(_class="menuentry",width="150",align="center",onclick="self.location='/status/'",onmouseover="this.className='menuentrypressed';",onmouseout="this.className='menuentry';")[T.a(_class="menuentry",href="/status/")["Status"]]]
			row[T.td(_class="menuentry",width="150",align="center",onclick="self.location='/config/'",onmouseover="this.className='menuentrypressed';",onmouseout="this.className='menuentry';")[T.a(_class="menuentry",href="/config/")["Configuration"]]]
			row[T.td(_class="menuentry",width="150",align="center",onclick="self.location='/controls/'",onmouseover="this.className='menuentrypressed';",onmouseout="this.className='menuentry';")[T.a(_class="menuentry",href="/controls/")["Controls"]]]

		ret[row]

		return ret

	child_images = static.File('data/www/images/')
	child_css = static.File('data/www/css/')


# Root Node
class WebInterface(WebInterface_template):
	def childFactory(self, ctx, name):
		debug.log("WebInterface: childFactory %s %s" % (ctx, name))
		if name == "account":
			return WebInterface_account(pytrans=self.pytrans)
		if name == "status":
			return WebInterface_status(pytrans=self.pytrans)
		if name == "config":
			return WebInterface_config(pytrans=self.pytrans)
		if name == "controls":
			return WebInterface_controls(pytrans=self.pytrans)
		else:
			pass

	def render_content(self, ctx):
		return loaders.htmlstr("""
<P CLASS="intro">Welcome to the PyICQ-t web interface.  At
present, these interfaces are very limited, mostly providing miscellaneous
information about the transport.  Eventually, this interface will do more,
but for now, enjoy the statistics and such!</P>
""")


# Account Node
class WebInterface_account(WebInterface_template):
	def render_content(self, context, data):
		return loaders.htmlstr("""
<B>Your Account</B>
<HR />
<SPAN nevow:render="info" />
<BR /><BR />
<B>Roster</B>
<HR />
<SPAN nevow:render="roster" />
""")

	def render_info(self, context, data):
		request = inevow.IRequest(context)
		username = request.getUser()
		print "username = %s" % (username)
		reg = self.pytrans.xdb.getRegistration(username)
		if not reg:
			return "You are not currently registered with the transport."

		return reg[0]

	def render_roster(self, context, data):
		request = inevow.IRequest(context)
		username = request.getUser()
		print "username = %s" % (username)

		ret = T.table(border = 0,width = "100%",cellspacing=5,cellpadding=2)
		roster = self.pytrans.xdb.getList("roster", username)
		if not roster:
			return ret
		for item in roster:
			row = T.tr[T.td[item[0]]]
			ret[row]
		return ret


# Status Node
class WebInterface_status(WebInterface_template):
	def render_content(self, context, data):
		return loaders.htmlstr("""
<B>Transport Statistics</B>
<HR />
<SPAN nevow:render="statistics" />
<BR /><BR />
<B>Sessions</B>
<HR />
<SPAN nevow:render="sessions" />
""")

	def render_statistics(self, context, data):
		ret = T.table(border = 0,width = "100%",cellspacing=5,cellpadding=2)
		for key in self.pytrans.statistics.stats:
			label = lang.get("statistics_%s" % key, config.lang)
			description = lang.get("statistics_%s_Desc" % key, config.lang)

			row = T.tr[
				T.th(align = "right")[label+":"],
				T.td[self.pytrans.statistics.stats[key]],
				T.td[description]
			]
			ret[row]
		return ret

	def render_sessions(self, context, data):
		if len(self.pytrans.sessions) <= 0:
			return "No active sessions."

		ret = T.table(border = 0,width = "100%",cellspacing=5,cellpadding=2)
		row = T.tr[
			T.th["User"],
			T.th["Incoming Messages"],
			T.th["Outgoing Messages"],
			T.th["Connections"]
		]
		ret[row]
		for key in self.pytrans.sessions:
			jid = self.pytrans.sessions[key].jabberID
			row = T.tr[
				T.td[jid],
				T.td(align = "center")[self.pytrans.statistics.sessionstats[jid]['IncomingMessages']],
				T.td(align = "center")[self.pytrans.statistics.sessionstats[jid]['OutgoingMessages']],
				T.td(align = "center")[self.pytrans.statistics.sessionstats[jid]['Connections']]
			]
			ret[row]
		return ret


# Configuration Node
class WebInterface_config(WebInterface_template):
	def render_content(self, context, data):
		return loaders.htmlstr("""
<B>Configuration</B>
<HR />
<SPAN nevow:render="config" />
""")

	def render_config(self, context, data):
		table = T.table(border=0)
		for key in config.__dict__.keys():
			if key[0] == "_":
				continue
			if key.find("secret") >= 0:
				setting = "**hidden**"
			else:
				setting = config.__dict__[key]
			row = T.tr[T.td[key], T.td["="], T.td[setting]]
			table[row]
		return table


# Controls Node
class WebInterface_controls(WebInterface_template):
	#def renderHTTP(self, ctx):
	#	request = inevow.IRequest(ctx)
	#	if request.args.get('shutdown'):
	#		debug.log("WebInterface: Received shutdown")
	#		reactor.stop()
	#	return WebInterface_template.renderHTTP(self, ctx)

	def render_content(self, context, data):
		return loaders.htmlstr("""
<B>Controls</B>
<HR />
<SPAN nevow:render="message" />
<SPAN nevow:render="controls" />
""")

	def render_message(self, context, data):
		request = inevow.IRequest(context)
		if request.args.get('shutdown'):
			return T.b["Server is now shut down.  Attempts to reload this page will fail."]
		return ""

	def render_controls(self, context, data):
		request = inevow.IRequest(context)
		if request.args.get('shutdown'):
			return ""
		return T.form(method="POST")[
			T.input(type="submit", name="shutdown", value="Shut Down")
		]
