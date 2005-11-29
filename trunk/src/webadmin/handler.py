# Copyright 2004-2005 Daniel Henninger <jadestorm@nc.rr.com>
# Licensed for distribution under the GPL version 2, check COPYING for details

#from twisted.web.woven import page
from nevow import rend, loaders, inevow
from nevow import tags as T
from twisted.protocols import http
from twisted.web import microdom
from twisted.internet import reactor
import debug
import config
import legacy
import sys, os
import lang

admintmplhead = """
<HTML>

<HEAD>
<TITLE>PyICQ-t Web Administration</TITLE>
<STYLE>
BODY {
	background-color: #ddffdd;
	font-family: Arial, Helvetica, sans-serif;
	margin-top: 0.0px;
	margin-bottom: 0.0px;
	margin-left: 0.0px;
	margin-right: 0.0px;
}

P.intro {
	margin-top: 10.0px;
	margin-left: 10.0px;
	margin-right: 10.0px;
	margin-bottom: 10.0px;
}

SPAN.title {
	font-family: Arial, Helvetica, sans-serif;
	font-size: 200%;
	font-weight: bolder;
	border-left: 2.0px solid #000000;
	border-top: 2.0px solid #000000;
	border-right: 2.0px solid #77ee77;
	border-bottom: 2.0px solid #77ee77;
	padding-top: 2.0px;
	padding-bottom: 2.0px;
	padding-left: 50.0px;
	padding-right: 50.0px;
}

SPAN.name {
	font-family: Arial, Helvetica, sans-serif;
	font-size: 100%;
	font-weight: bold;
}

SPAN.version {
	font-family: Arial, Helvetica, sans-serif;
	font-size: 100%;
	font-weight: bold;
}

TR.title {
	background-color: #5cbb57;
}

TD.menu {
	background-color: #aaffaa;
}

TD.menuentrypressed {
	background-color: #77ee77;
	border-left: 2.0px solid #000000;
	border-top: 2.0px solid #000000;
	border-right: 2.0px solid #77ee77;
	border-bottom: 2.0px solid #77ee77;
}

TD.menuentry {
	background-color: #77ee77;
	border-right: 2.0px solid #000000;
	border-bottom: 2.0px solid #000000;
	border-left: 2.0px solid #77ee77;
	border-top: 2.0px solid #77ee77;
}

A, A:visited {
	color: #000000;
}

A:hover {
	color: #777777;
}

A.menuentry, A:visited.menuentry {
	text-decoration: none;
}

A:hover.menuentry {
	text-decoration: none;
	color: #000000;
}

A.control {
	color: #000000;
	text-decoration: none;
	background-color: #77ee77;
	border-right: 2.0px solid #000000;
	border-bottom: 2.0px solid #000000;
	border-left: 2.0px solid #77ee77;
	border-top: 2.0px solid #77ee77;
}

A:hover.control {
	color: #000000;
	text-decoration: none;
	background-color: #77ee77;
	border-left: 2.0px solid #000000;
	border-top: 2.0px solid #000000;
	border-right: 2.0px solid #77ee77;
	border-bottom: 2.0px solid #77ee77;
}
</STYLE>
</HEAD>

<BODY>
<TABLE BORDER="0" WIDTH="100%" CELLSPACING="0" CELLPADDING="3">
<TR CLASS="title" VALIGN="middle" HEIGHT="50">
<TH><TABLE BORDER="0" WIDTH="100%" CELLSPACING="0" CELLPADDING="3">
<TR VALIGN="middle">
<TD ALIGN="center" WIDTH="100"><SPAN CLASS="name">PyICQ-t</SPAN></TD>
<TD ALIGN="center"><SPAN CLASS="title"><SPAN nevow:render="title" /></SPAN></TD>
<TD ALIGN="center" WIDTH="100"><SPAN CLASS="version"><SPAN nevow:render="version" /></SPAN></TD>
</TR>
</TABLE></TH>
</TR>
<TR VALIGN="top">
<TD CLASS="menu" ALIGN="left"><TABLE BORDER="0" CELLSPACING="3" CELLPADDING="3">
<TR VALIGN="middle">
<TD CLASS="menuentry" WIDTH="150" ALIGN="center" onClick="self.location='/status/'" onMouseOver="this.className='menuentrypressed';" onMouseOut="this.className='menuentry';"><A CLASS="menuentry" HREF="/status/">Status</A></TD>
<TD CLASS="menuentry" WIDTH="150" ALIGN="center" onClick="self.location='/config/'" onMouseOver="this.className='menuentrypressed';" onMouseOut="this.className='menuentry';"><A CLASS="menuentry" HREF="/config/">Configuration</A></TD>
<TD CLASS="menuentry" WIDTH="150" ALIGN="center" onClick="self.location='/controls/'" onMouseOver="this.className='menuentrypressed';" onMouseOut="this.className='menuentry';"><A CLASS="menuentry" HREF="/controls/">Controls</A></TD>
</TR>
</TABLE></TD>
</TR>
<TR VALIGN="top">
<TD ALIGN="left">
"""

admintmplfoot = """
</TD>
</TR>
</TABLE>
</BODY>

</HTML>
"""

# Root Node
class WebAdmin(rend.Page):
	addSlash = True
	docFactory = loaders.htmlstr(admintmplhead + """
<P CLASS="intro">Welcome to the PyICQ-t administration interface.  At
present, these interfaces are very limited, mostly providing miscellaneous
information about the transport.  Eventually, this interface will do more,
but for now, enjoy the statistics and such!</P>
""" + admintmplfoot)

	def __init__(self, pytrans):
		self.pytrans = pytrans

	def renderHTTP(self, ctx):
		request = inevow.IRequest(ctx)
		password = request.getPassword()
		if password != config.websecret:
			request.setHeader('WWW-Authenticate', 'Basic realm="PyICQ-t"')
			request.setResponseCode(http.UNAUTHORIZED)
			return "Authorization required."
		return rend.Page.renderHTTP(self, ctx)

	def childFactory(self, ctx, name):
		debug.log("WebAdmin: getDynamicChild %s %s" % (ctx, name))
		if name == "status":
			return WebAdmin_status(pytrans=self.pytrans)
		if name == "config":
			return WebAdmin_config(pytrans=self.pytrans)
		if name == "controls":
			return WebAdmin_controls(pytrans=self.pytrans)
		else:
			pass

	def render_version(self, context, data):
		return [legacy.version]

	def render_title(self, context, data):
		return [legacy.name]

# Status Node
class WebAdmin_status(WebAdmin):
	docFactory = loaders.htmlstr(admintmplhead + """
<B>Transport Statistics</B>
<HR />
<SPAN nevow:render="statistics" />
<BR /><BR />
<B>Sessions</B>
<HR />
<SPAN nevow:render="sessions" />
""" + admintmplfoot)

	def __init__(self, pytrans):
		self.pytrans = pytrans

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
class WebAdmin_config(WebAdmin):
	docFactory = loaders.htmlstr(admintmplhead + """
<B>Configuration</B>
<HR />
<SPAN nevow:render="config" />
""" + admintmplfoot)

	def __init__(self, pytrans):
		self.pytrans = pytrans

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
class WebAdmin_controls(WebAdmin):
	docFactory = loaders.htmlstr(admintmplhead + """
<B>Controls</B>
<HR />
<SPAN nevow:render="message" />
<SPAN nevow:render="controls" />
""" + admintmplfoot)

	def __init__(self, pytrans):
		self.pytrans = pytrans

	def renderHTTP(self, ctx):
		request = inevow.IRequest(ctx)
		password = request.getPassword()
		if password != config.websecret:
			request.setHeader('WWW-Authenticate', 'Basic realm="PyICQ-t"')                  
			request.setResponseCode(http.UNAUTHORIZED)
			return "Authorization required."
		if request.args.get('shutdown'):
			debug.log("WebAdmin: Received shutdown")
			reactor.stop()
		return rend.Page.renderHTTP(self, ctx)

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
